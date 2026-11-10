"""미국판 음성 구조를 읽고 새 조사 JSON만 만든다. 디코더/패처가 아니다."""
from collections import Counter
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import struct
import subprocess
import sys
import wave

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.discover_inputs import DiscReader, file_info, psx_arc, sha256

ROOT = Path(__file__).resolve().parents[1]
SUPPORTED_SOURCE = "3ceab06ac99add4035f912188bcbf5b16c02056f46a33d38ff0c8dbce6cb613b"


def reference_info(path):
    info = file_info(path)
    raw = path.read_bytes()
    if raw[:4] != b"RIFF" or raw[8:12] != b"WAVE":
        raise ValueError("Expected RIFF WAVE")
    if struct.unpack_from("<I", raw, 4)[0] + 8 != len(raw):
        raise ValueError("RIFF length mismatch")
    pos, chunks = 12, []
    while pos + 8 <= len(raw):
        name, size = struct.unpack_from("<4sI", raw, pos)
        if pos + 8 + size > len(raw):
            raise ValueError("Truncated WAVE chunk")
        item = {"id": name.decode("ascii"), "offset": pos + 8, "size": size}
        if name == b"LIST" and raw[pos + 8:pos + 12] == b"INFO":
            sub, tags = pos + 12, {}
            while sub + 8 <= pos + 8 + size:
                key, length = struct.unpack_from("<4sI", raw, sub)
                if sub + 8 + length > pos + 8 + size:
                    raise ValueError("Truncated INFO tag")
                tags[key.decode("ascii")] = raw[sub + 8:sub + 8 + length].rstrip(b"\0").decode("utf-8", errors="replace")
                sub += 8 + length + (length & 1)
            item["tags"] = tags
        chunks.append(item)
        pos += 8 + size + (size & 1)
    with wave.open(str(path), "rb") as wav:
        channels, width, rate, frames, compression, _ = wav.getparams()
        if width != 2 or compression != "NONE":
            raise ValueError("Signal statistics support PCM16 only")
        samples = np.frombuffer(wav.readframes(frames), dtype="<i2").reshape(-1, channels)
    norm = samples.astype(np.float64) / 32768.0
    info.update(channels=channels, bits_per_sample=width * 8, sample_rate=rate,
                frames=frames, duration_seconds=frames / rate, chunks=chunks,
                peak_per_channel=np.max(np.abs(norm), axis=0).tolist(),
                rms_per_channel=np.sqrt(np.mean(norm * norm, axis=0)).tolist(),
                full_scale_samples_per_channel=np.sum((samples == -32768) | (samples == 32767), axis=0).tolist(),
                stereo_correlation=float(np.corrcoef(norm.T)[0, 1]) if channels == 2 else None,
                listening_completed=False, transcription_completed=False,
                clean_reference_segments_selected=False)
    return info


def parse_bank(header, body, include_commands):
    packed, body_size = struct.unpack_from("<II", header)
    offset, slot = packed & 0xffffff, packed >> 24
    if body_size != len(body):
        raise ValueError("SoundArchive body length mismatch")
    if offset < 8 or (offset - 8) % 4 or header[offset:offset + 4] != b"pBAV":
        raise ValueError("Invalid SoundArchive VAB offset")
    programs, tones, waves = struct.unpack_from("<HHH", header, offset + 18)
    tone_base = offset + 32 + 128 * 16
    size_base = tone_base + programs * 16 * 32
    if size_base + 512 > len(header) or waves > 255:
        raise ValueError("VAB size table out of bounds")
    lengths = [n * 8 for n in struct.unpack_from("<256H", header, size_base)[:waves + 1]]
    if sum(lengths) != len(body):
        raise ValueError("VAB sample lengths do not fill body")
    wave_records, start = [], lengths[0]
    for index, length in enumerate(lengths[1:], 1):
        if length % 16:
            raise ValueError("SPU sample not aligned to 16-byte blocks")
        data = body[start:start + length]
        wave_records.append({"wave_id": index, "body_offset": start, "bytes": length,
                             "adpcm_blocks": length // 16,
                             "decoded_samples_upper_bound": length // 16 * 28,
                             "sha256": sha256(data)})
        start += length
    result = {"slot": slot, "vab_offset": offset, "body_bytes": len(body),
              "program_count": programs, "tone_count": tones, "wave_count": waves,
              "command_count": (offset - 8) // 4,
              "initial_padding_bytes": lengths[0], "waves": wave_records}
    if include_commands:
        commands = []
        for index in range((offset - 8) // 4):
            command = header[8 + index * 4:12 + index * 4]
            program, first_tone = command[1] & 127, command[2] >> 4
            count = ((command[3] >> 5) & 3) + 1
            mapped = []
            for tone in range(first_tone, first_tone + count):
                # This minimal mapping is restricted to the confirmed one-program voice bank.
                if programs != 1 or program != 0 or tone >= 16:
                    raise ValueError("Unconfirmed voice program mapping")
                record = header[tone_base + tone * 32:tone_base + (tone + 1) * 32]
                mapped.append({"tone": tone, "wave_id": struct.unpack_from("<H", record, 22)[0],
                               "volume": record[2], "pan": record[3], "center_note": record[4],
                               "fine_shift": record[5], "min_note": record[6], "max_note": record[7]})
            commands.append({"sound_id": index, "command_hex": command.hex(), "tones": mapped,
                             "audible_label": None, "runtime_trigger_verified": False})
        result["commands"] = commands
    return result


def stream_info(source, current, record):
    sector_count = (record["size"] + 2047) // 2048
    byte_count = sector_count * 2352
    source.seek(record["lba"] * 2352)
    raw = source.read(byte_count)
    current.seek(record["lba"] * 2352)
    revised = current.read(byte_count)
    if len(raw) != byte_count or len(revised) != byte_count:
        raise ValueError("Stream outside BIN")
    sectors = np.frombuffer(raw, dtype=np.uint8).reshape(-1, 2352)
    sync = np.array([0] + [255] * 10 + [0], dtype=np.uint8)
    if not np.all(sectors[:, :12] == sync) or not np.all(sectors[:, 15] == 2):
        raise ValueError("Non-Mode2 stream sector")
    if not np.array_equal(sectors[:, 16:20], sectors[:, 20:24]):
        raise ValueError("Duplicated XA subheaders disagree")
    audio = sectors[(sectors[:, 18] & 4) != 0]
    groups = Counter(tuple(int(x) for x in row) for row in audio[:, [16, 17, 19]])
    formats = []
    for (file_number, channel, coding), count in sorted(groups.items()):
        formats.append({"file_number": file_number, "channel": channel, "coding_hex": hex(coding),
                        "sectors": count,
                        "sample_rate": {0: 37800, 1: 18900}.get((coding >> 2) & 3),
                        "audio_channels": {0: 1, 1: 2}.get(coding & 3),
                        "adpcm_bits": {0: 4, 1: 8}.get((coding >> 4) & 3)})
    return {"path": record["path"], "lba": record["lba"], "iso_size": record["size"],
            "raw_sectors": sector_count, "raw_bytes": byte_count,
            "raw_sha256": sha256(raw), "current_raw_sha256": sha256(revised),
            "unchanged_in_current_build": raw == revised,
            "form1_sectors": int(np.sum((sectors[:, 18] & 32) == 0)),
            "form2_sectors": int(np.sum((sectors[:, 18] & 32) != 0)),
            "audio_formats": formats, "speakers_identified": False}


def main():
    source_path = ROOT / "MegaMan X4.bin"
    pointer_path = ROOT / "projects/ver_buki_riko/current_build.json"
    pointer_bytes = pointer_path.read_bytes()
    pointer = json.loads(pointer_bytes)
    current_path = ROOT / pointer["build"] / "riko_motion.bin"
    reference_path = ROOT / "character/ver_buki_riko/riko(zero)_voice.wav"
    source_info, current_info = file_info(source_path), file_info(current_path)
    if source_info["sha256"] != SUPPORTED_SOURCE:
        raise ValueError("Unsupported original BIN")
    if current_info["sha256"] != pointer["bin_sha256"] or source_info["size"] != current_info["size"]:
        raise ValueError("Current build pointer/length mismatch")
    reference = reference_info(reference_path)
    report = {"created_utc": datetime.now(timezone.utc).isoformat(), "mode": "read_only_discovery",
              "source": source_info, "current_build": current_info, "reference": reference,
              "python": sys.version, "numpy": np.__version__, "archives": [], "streams": [],
              "installed_in_active_python": {name: importlib.util.find_spec(name) is not None for name in
                  ("torch", "torchaudio", "soundfile", "librosa", "whisper", "faster_whisper", "transformers")},
              "executables_on_path": {name: shutil.which(name) for name in ("ffmpeg", "ffprobe", "sox", "vgmstream-cli")},
              "model_inference_run": False, "audio_decoding_run": False, "game_run": False,
              "source_script_sha256": sha256(Path(__file__).read_bytes())}
    gpu = shutil.which("nvidia-smi")
    if gpu:
        result = subprocess.run([gpu, "--query-gpu=name,memory.total,driver_version", "--format=csv,noheader"],
                                capture_output=True, text=True, timeout=15, check=True)
        report["gpu"] = result.stdout.strip()
    with source_path.open("rb") as source, current_path.open("rb") as current:
        reader = DiscReader(source, source_info["size"])
        current_reader = DiscReader(current, current_info["size"])
        disc = reader.inspect()
        report["disc_volume_id"] = disc["volume_id"]
        report["disc_sector_headers"] = disc["sector_headers"]
        for record in disc["files"]:
            if record["directory"]:
                continue
            if record["name"].endswith(".ARC;1"):
                payload = reader.read(record["lba"], record["size"])
                revised = current_reader.read(record["lba"], record["size"])
                try:
                    entries = psx_arc(payload)
                except ValueError as error:
                    report["archives"].append({"path": record["path"], "lba": record["lba"],
                                               "size": record["size"], "banks": [],
                                               "unparsed_reason": str(error),
                                               "header_hex": payload[:16].hex()})
                    continue
                banks = []
                for idx, entry in enumerate(entries):
                    header = payload[entry["offset"]:entry["offset"] + entry["size"]]
                    if len(header) < 8:
                        continue
                    packed = struct.unpack_from("<I", header)[0]
                    vh_offset, slot = packed & 0xffffff, packed >> 24
                    if header[vh_offset:vh_offset + 4] != b"pBAV":
                        continue
                    expected_size = struct.unpack_from("<I", header, 4)[0]
                    candidates = [item for item in entries if int(item["type"], 16) >> 16 == 2
                                  and (int(item["type"], 16) >> 8) & 255 == slot
                                  and item["size"] == expected_size]
                    if len(candidates) != 1:
                        raise ValueError(f"Ambiguous VAB/body pairing: {record['path']} entry {idx}, slot {slot}")
                    body_entry = candidates[0]
                    body = payload[body_entry["offset"]:body_entry["offset"] + body_entry["size"]]
                    bank = parse_bank(header, body, record["name"] == "PL01_U.ARC;1" and slot == 3)
                    bank.update(header_entry=entry, body_entry=body_entry,
                                header_unchanged=header == revised[entry["offset"]:entry["offset"] + entry["size"]],
                                body_unchanged=body == revised[body_entry["offset"]:body_entry["offset"] + body_entry["size"]])
                    banks.append(bank)
                report["archives"].append({"path": record["path"], "lba": record["lba"],
                                           "size": record["size"], "banks": banks})
            elif record["name"].endswith((".XA;1", ".STR;1")):
                report["streams"].append(stream_info(source, current, record))
    report["input_preservation"] = {
        "original_unchanged": file_info(source_path)["sha256"] == source_info["sha256"],
        "current_build_unchanged": file_info(current_path)["sha256"] == current_info["sha256"],
        "reference_unchanged": file_info(reference_path)["sha256"] == reference["sha256"],
        "pointer_unchanged": pointer_path.read_bytes() == pointer_bytes}
    if not all(report["input_preservation"].values()):
        raise ValueError("Input changed during discovery")
    output_base = (ROOT / "work/ver_buki_riko/voice_discovery").resolve()
    if not output_base.is_relative_to(ROOT.resolve()):
        raise ValueError("Output outside workspace")
    output = output_base / datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    output.mkdir(parents=True, exist_ok=False)
    with (output / "inventory.local.json").open("x", encoding="utf-8") as stream:
        json.dump(report, stream, ensure_ascii=False, indent=2)
    print((output / "inventory.local.json").relative_to(ROOT))
    print(json.dumps({"archives": len(report["archives"]), "streams": len(report["streams"]),
                      "preservation": report["input_preservation"]}))


if __name__ == "__main__":
    main()
