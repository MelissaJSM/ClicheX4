"""지원 원본의 13개 플레이어 음성을 새 작업 디렉터리에 복원한다."""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import sys
import wave

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.discover_inputs import DiscReader, psx_arc, file_info, sha256
from scripts.inventory_riko_voice import parse_bank
from src.psx_spu_audio import decode_spu, validate_oneshot_template, vag_container

SOURCE_HASH = "3ceab06ac99add4035f912188bcbf5b16c02056f46a33d38ff0c8dbce6cb613b"
REFERENCE_HASH = "d0ba1fde6fddb1440fb021dd2bf2c504ee3d0f2039e12d0dece1dd0fef23da46"
BASE_HASH = "a5ecfbc6ec0e1da1ab40248a474fb7a6e82a60866095e5ac3744a919770d01da"


def save_wav(path, pcm, sample_rate):
    if path.exists():
        raise ValueError("Refusing to overwrite WAV")
    with wave.open(str(path), "wb") as target:
        target.setparams((1, 2, sample_rate, len(pcm), "NONE", "not compressed"))
        target.writeframes(struct.pack("<" + "h" * len(pcm), *pcm))


def prepare(output):
    output = output.resolve()
    if not output.is_relative_to((ROOT / "work/ver_buki_riko/voice_production").resolve()) or output.exists():
        raise ValueError("Expected a new voice production directory")
    original = ROOT / "MegaMan X4.bin"
    reference = ROOT / "character/ver_buki_riko/riko(zero)_voice.wav"
    parent = ROOT / "out/ver_buki_riko/riko_illustrations_20261025T232733128418Z"
    current = parent / "riko_motion.bin"
    input_info = [file_info(p) for p in (original, current, reference)]
    if [item["sha256"] for item in input_info] != [SOURCE_HASH, BASE_HASH, REFERENCE_HASH]:
        raise ValueError("Source, accepted build or reference changed")
    with original.open("rb") as stream:
        reader = DiscReader(stream, original.stat().st_size)
        records = reader.inspect()["files"]
        record = next(x for x in records if x["path"] == "/ARC/PL01_U.ARC;1")
        arc = reader.read(record["lba"], record["size"])
        exe_record = next(x for x in records if x["name"] == "SLUS_005.61;1")
        exe = reader.read(exe_record["lba"], exe_record["size"])
    with current.open("rb") as stream:
        current_arc = DiscReader(stream, current.stat().st_size).read(record["lba"], record["size"])
    entries = psx_arc(arc)
    header_entry = entries[12]
    body_entry = entries[13]
    if header_entry["type"] != "0x6" or body_entry["type"] != "0x20301":
        raise ValueError("Unexpected voice bank")
    header = arc[header_entry["offset"]:header_entry["offset"] + header_entry["size"]]
    body = arc[body_entry["offset"]:body_entry["offset"] + body_entry["size"]]
    for entry in (header_entry, body_entry):
        span = slice(entry["offset"], entry["offset"] + entry["size"])
        if current_arc[span] != arc[span]:
            raise ValueError("Accepted build voice bank differs from original")
    bank = parse_bank(header, body, True)
    table_offset = 0x8011c9e8 - 0x80010000 + 2048
    pitch_table = struct.unpack_from("<192H", exe, table_offset)
    # US note2pitch2 at 0x800E2598: tone fine is added to the call's fine.
    def pitch(tone):
        fine = (tone["fine_shift"] * 2) >> 3
        semitone = tone["min_note"] + 60 - tone["center_note"] + fine // 16
        value = pitch_table[(semitone % 12) * 16 + fine % 16]
        octave = semitone // 12 - 5
        return value << octave if octave >= 0 else value >> -octave
    output.mkdir(parents=True, exist_ok=False)
    (output / "source_bank.adpcm").write_bytes(body)
    report = {"inputs": input_info, "parent_build": str(parent.relative_to(ROOT)),
              "arc_record": {**record, "sha256": sha256(arc)}, "parent_arc_sha256": sha256(current_arc),
              "voice_header_entry": header_entry, "voice_body_entry": body_entry,
              "pitch_basis": "US note2pitch2 and original pitch lookup table; live register check pending",
              "pitch_table_sha256": sha256(exe[table_offset:table_offset + 384]),
              "commands": [], "unmodified_roundtrip": None}
    split = []
    for waveform in bank["waves"]:
        start = waveform["body_offset"]
        split.append(body[start:start + waveform["bytes"]])
    if b"".join(split) != body:
        raise ValueError("Unchanged sample split/reassembly failed")
    report["unmodified_roundtrip"] = {"byte_identical": True, "sha256": sha256(b"".join(split))}
    for command in bank["commands"]:
        wave_ids = {tone["wave_id"] for tone in command["tones"]}
        if len(wave_ids) != 1:
            raise ValueError("Unconfirmed multiple-wave voice command")
        wave_id = wave_ids.pop()
        waveform = bank["waves"][wave_id - 1]
        raw = split[wave_id - 1]
        capacity = validate_oneshot_template(raw)
        decoded = decode_spu(raw)
        pitches = [pitch(tone) for tone in command["tones"]]
        rate = round(pitches[0] * 44100 / 4096)
        name = f"voice_{command['sound_id']:02d}"
        save_wav(output / (name + ".wav"), decoded.pcm, rate)
        (output / (name + ".adpcm")).write_bytes(raw)
        (output / (name + ".vag")).write_bytes(vag_container(raw, rate, name))
        report["commands"].append({**command, **waveform, "name": name, "spu_pitches": pitches,
                                   "sample_rates_exact": [p * 44100 / 4096 for p in pitches],
                                   "wav_sample_rate": rate, "pcm_samples": capacity,
                                   "duration_seconds": capacity / (pitches[0] * 44100 / 4096),
                                   "raw_sha256": sha256(raw), "wav_sha256": sha256((output / (name + ".wav")).read_bytes())})
    (output / "manifest.local.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"output": str(output.relative_to(ROOT)), "count": len(report["commands"]),
                      "original_split_roundtrip": True}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    prepare(parser.parse_args().output)
