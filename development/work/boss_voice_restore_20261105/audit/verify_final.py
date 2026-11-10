"""최종 BIN 두 개를 원본/부모/JP 출처와 독립 대조한다. 게임/포인터 쓰기 없음."""
from __future__ import annotations
import argparse
import hashlib
import json
import struct
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
AUDIT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(AUDIT))
from scripts.discover_inputs import DiscReader, psx_arc
from scripts.inventory_riko_voice import parse_bank
from scripts.overhaul_audio_verify_cpu import run, banks
from src.psx_sector import rebuild_checks, validate_checks
from src.psx_spu_audio import decode_spu
import player_contract

PLAN = {1: [(3, 4, [3, 4]), (2, 5, [1])], 2: [(9, 8, [18, 19]), (6, 9, [9, 10])],
        3: [(4, 4, [5])], 5: [(4, 4, [6, 7])],
        6: [(9, 4, [12, 13]), (2, 5, [2, 3]), (4, 6, [4]), (3, 7, [14, 15])],
        7: [(10, 10, [2, 3])], 8: [(7, 8, [9, 10])]}
COMBAT = {name: stage for stage in PLAN for name in (f"ST{stage}_1_1.ARC", f"ONPARE{stage}.ARC")}
PLAYERS = ("PL00_U.ARC", "PL01_U.ARC", "PL02_U.ARC")
BRANCH_OFFSET = 0x800921F8 - 0x80010000 + 2048
SIGNAL_CACHE = {}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def digest(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load(path):
    return json.loads(path.read_text("utf-8"))


def signal_metrics(original, encoded, ratio, source_rate, target_rate):
    key = (sha(original), sha(encoded), tuple(ratio), source_rate, target_rate)
    if key not in SIGNAL_CACHE:
        code = '''import json,sys,numpy as np
from scipy.signal import resample_poly
from src.psx_spu_audio import decode_spu
d=json.load(sys.stdin)
a=np.asarray(decode_spu(bytes.fromhex(d["original"])).pcm,dtype=np.float64)
b=np.asarray(decode_spu(bytes.fromhex(d["encoded"])).pcm,dtype=np.float64)
up,down=d["ratio"];back=resample_poly(b,down,up);n=min(len(a),len(back))
print(json.dumps({"correlation":float(np.corrcoef(a[:n],back[:n])[0,1]),"duration_error":len(b)/d["target_rate"]-len(a)/d["source_rate"]}))
'''
        payload = {"original": original.hex(), "encoded": encoded.hex(), "ratio": ratio,
                   "source_rate": source_rate, "target_rate": target_rate}
        completed = subprocess.run([str(ROOT / "work/tools/voice_env/Scripts/python.exe"), "-B", "-c", code],
            input=json.dumps(payload), cwd=ROOT, capture_output=True, text=True, check=True)
        SIGNAL_CACHE[key] = json.loads(completed.stdout)
    return SIGNAL_CACHE[key]


def assets(path, names):
    with path.open("rb") as stream:
        reader = DiscReader(stream, path.stat().st_size)
        disc = reader.inspect()
        records = {r["name"].split(";")[0]: r for r in disc["files"]
                   if not r["directory"] and r["name"].split(";")[0] in names}
        require(set(records) == set(names), "Missing assets")
        return {n: reader.read(r["lba"], r["size"]) for n, r in records.items()}, records, disc["files"]


def bank(arc, wanted):
    entries = psx_arc(arc)
    matches = []
    for hrec, brec in zip(entries, entries[1:]):
        h = arc[hrec["offset"]:hrec["offset"] + hrec["size"]]
        b = arc[brec["offset"]:brec["offset"] + brec["size"]]
        try:
            q = parse_bank(h, b, False)
        except (ValueError, IndexError, struct.error):
            continue
        if q["slot"] == wanted:
            matches.append((h, b, q, hrec, brec))
    require(len(matches) == 1, "Ambiguous requested bank")
    return matches[0]


def tone(h, q, index):
    p = q["vab_offset"] + 32 + 128 * 16 + index * 32
    return h[p:p + 32]


def wave(b, q, index):
    w = q["waves"][index - 1]
    return b[w["body_offset"]:w["body_offset"] + w["bytes"]]


def check_arc(before, after, jp, stage, proof):
    layout = lambda x: [(e["type"], e["offset"], e["size"]) for e in psx_arc(x)]
    require(len(before) == len(after) and layout(before) == layout(after), "ARC layout changed")
    h, b, q, he, be = bank(before, 2)
    nh, nb, nq, nhe, nbe = bank(after, 2)
    jh, jb, jq, _, _ = bank(jp, 2)
    require((he["offset"], be["offset"]) == (nhe["offset"], nbe["offset"]), "Bank moved")
    allowed = bytearray(len(before))
    for e in (he, be):
        allowed[e["offset"]:e["offset"] + e["size"]] = b"\1" * e["size"]
    require(all(x == y or allowed[i] for i, (x, y) in enumerate(zip(before, after))), "Unrelated ARC byte changed")
    for key in ("slot", "vab_offset", "body_bytes", "program_count", "tone_count", "wave_count", "command_count", "initial_padding_bytes"):
        require(q[key] == nq[key], "Capacity/layout changed: " + key)
    tb = q["vab_offset"] + 32 + 128 * 16
    sizebase = tb + q["program_count"] * 16 * 32
    require(h[:tb] == nh[:tb], "Commands or VAB master/program changed")
    require(h[sizebase + (q["wave_count"] + 1) * 2:] == nh[sizebase + (q["wave_count"] + 1) * 2:], "Unused bank tail changed")
    target_tones = {n for _, _, tones in PLAN[stage] for n in tones}
    target_waves = {target for _, target, _ in PLAN[stage]}
    tone_rows = []
    for source, target, indices in PLAN[stage]:
        for n in indices:
            jt, nt = tone(jh, jq, n), tone(nh, nq, n)
            delta = nt[4] - jt[4]
            expected = bytearray(jt)
            expected[4] += delta
            struct.pack_into("<H", expected, 22, target)
            require(0 <= delta <= 12 and bytes(expected) == nt, "Tone differs from JP beyond wave/center")
            require(struct.unpack_from("<H", jt, 22)[0] == source, "Incorrect JP source wave")
            tone_rows.append({"packed_tone": n, "source_wave": source, "target_wave": target, "center_note_increase": delta})
    for n in range(q["program_count"] * 16):
        if n not in target_tones:
            require(tone(h, q, n) == tone(nh, nq, n), "Unrelated tone changed")
            wi = struct.unpack_from("<H", tone(h, q, n), 22)[0]
            if wi in target_waves and wave(b, q, wi) != wave(nb, nq, wi):
                require(tone(h, q, n)[2] == 0, "Audible non-target tone shares replaced wave")
    for i in range(1, q["wave_count"] + 1):
        if i not in target_waves:
            require(wave(b, q, i) == wave(nb, nq, i), "Unrelated SFX/C06 waveform changed")
    proofs = {r["target_wave"]: r for r in proof["waves"]}
    sample_rows = []
    for source, target, indices in PLAN[stage]:
        p = proofs[target]
        jraw, actual = wave(jb, jq, source), wave(nb, nq, target)
        require(sha(jraw) == p["source_raw_sha256"], "JP source SHA differs")
        length = p.get("result_bytes", len(actual))
        raw = actual[:length]
        require(sha(raw) == p["result_raw_sha256"] and not any(actual[length:]), "Encoded sample/padding differs")
        if p["reencoded"]:
            require(p["center_note_increase"] > 0, "Unnecessary resampling")
            raw_file = ROOT / p["raw_path"]
            require(raw_file.resolve().is_relative_to(ROOT / "work/boss_voice_restore_20261105")
                    and raw_file.read_bytes() == raw, "Prepared raw file differs")
            # Independent signal comparison, using decoder+scipy rather than the prepare quantizer.
            metrics = signal_metrics(jraw, raw, p["resample_ratio"], p["source_rate"], p["target_rate"])
            corr, duration_error = metrics["correlation"], metrics["duration_error"]
            require(abs(duration_error) < .004 and corr > .85, "Duration/signal correspondence failed")
            require(abs(corr - p["comparison_to_source_correlation"]) < 1e-9, "Reported correlation differs")
            sample_rows.append({"source_wave": source, "target_wave": target, "source_sha256": sha(jraw),
                               "encoded_sha256": sha(raw), "reencoded": True, "correlation": corr,
                               "duration_error_seconds": duration_error, "zero_padding": len(actual) - length})
        else:
            require(raw == jraw, "Unconverted sample is not original JP ADPCM")
            sample_rows.append({"source_wave": source, "target_wave": target, "source_sha256": sha(jraw),
                               "encoded_sha256": sha(raw), "reencoded": False, "original_JP_exact": True,
                               "zero_padding": len(actual) - length})
        if len(actual) > length:
            require(any(raw[i + 1] & 1 for i in range(0, len(raw), 16)), "Padding has no preceding ADPCM end flag")
    commands = []
    reached = set()
    for command in range(nq["command_count"]):
        c = nh[8 + command * 4:12 + command * 4]
        if c[0] & 0xC0 != 0x80 or c[0] & 63 != 2:
            continue
        ids = {(c[1] & 127) * 16 + (c[2] >> 4) + i for i in range(((c[3] >> 5) & 3) + 1)}
        if ids & target_tones:
            commands.append(command)
            reached |= ids & target_tones
    require(reached == target_tones, "Target tone not reached by a key-on command")
    return {"only_boss_bank2_changed": True, "non_target_tones_waves_commands_and_master_preserved": True,
            "target_tones": tone_rows, "samples": sample_rows, "commands_reaching_target_tones": commands,
            "changed_bytes": sum(x != y for x, y in zip(before, after))}, (he, be)


def compare_sectors(source, target, replacements, records):
    payloads = {}
    for name, body in replacements.items():
        r = records[name]
        require(len(body) == r["size"], "Replacement file size changed")
        for i in range((len(body) + 2047) // 2048):
            lba = r["lba"] + i
            require(lba not in payloads, "Overlapping replacement files")
            payloads[lba] = body[i * 2048:(i + 1) * 2048]
    count, changed = 0, []
    with source.open("rb") as a, target.open("rb") as b:
        while True:
            old = a.read(2352)
            new = b.read(2352)
            if not old:
                require(not new, "Target has extra sectors")
                break
            require(len(new) == 2352, "Target truncated")
            if old != new:
                require(count in payloads, "Non-target sector changed")
                p = payloads[count]
                expected = rebuild_checks(old[:24] + p + old[24 + len(p):])
                require(new == expected, "Sector differs beyond exact approved payload/checksum")
                validate_checks(new)
                changed.append(count)
            count += 1
    return {"all_sectors_compared": count, "changed_sector_count": len(changed), "changed_lbas": changed,
            "all_other_raw_sectors_exact": True, "sector_headers_and_tail_padding_preserved": True,
            "changed_EDC_ECC_valid": True}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--first-sha", required=True)
    parser.add_argument("--second-sha", required=True)
    parser.add_argument("--prepared", type=Path, required=True)
    args = parser.parse_args()
    result_path = AUDIT / "final_independent.json"
    require(not result_path.exists(), "Final evidence already exists")
    protection = load(AUDIT / "protection_before.json")
    for rel, p in protection["files"].items():
        path = ROOT / rel
        require(path.stat().st_size == p["size"] and digest(path) == p["sha256"], "Protected input changed: " + rel)
    prepared = args.prepared.resolve()
    require(prepared.is_relative_to(ROOT / "work/boss_voice_restore_20261105"), "Unexpected prepared path")
    jp, _, _ = assets(ROOT / "Rockman X4.bin", set(COMBAT))
    projects = {}
    for project, expected in (("ver_buki_riko", args.first_sha), ("ver_rin_nana", args.second_sha)):
        spec = protection["projects"][project]
        stem = "shibuki_riko" if project == "ver_buki_riko" else "rin_nana"
        source = ROOT / spec["bin"]
        target = ROOT / "out" / project / "boss_voice_restored_20261105_v2" / (stem + ".bin")
        require(target.resolve() != source.resolve() and digest(target) == expected, "Target identity differs")
        names = set(COMBAT) | set(PLAYERS) | {"SLUS_005.61"}
        old, records, oldiso = assets(source, names)
        new, newrecords, newiso = assets(target, names)
        require(records == newrecords and oldiso == newiso, "ISO layout changed")
        proposal = load(prepared / project / "proposal.json")
        proof = load(prepared / project / "verification.json")
        require(proposal["baseline_sha256"] == spec["bin_sha256"] and set(proposal["files"]) == set(COMBAT), "Wrong proposal")
        x = old["SLUS_005.61"]
        require(x[BRANCH_OFFSET:BRANCH_OFFSET + 4] == bytes.fromhex("18004014"), "Parent branch differs")
        expected_exe = x[:BRANCH_OFFSET] + bytes(4) + x[BRANCH_OFFSET + 4:]
        require(new["SLUS_005.61"] == expected_exe, "Unapproved EXE change")
        native = load(AUDIT / "current_intro_native.json")
        require(native["passed"] and native["patched_current_exe_sha256"] == sha(expected_exe), "Current CPU proof stale")
        reports = {}
        cpu_cases = []
        for name, stage in COMBAT.items():
            p = proposal["files"][name]
            require(sha(old[name]) == p["before"] and sha(new[name]) == p["after"]
                    and new[name] == (ROOT / p["path"]).read_bytes(), "Actual ARC differs from proposal")
            report, _ = check_arc(old[name], new[name], jp[name], stage, proof[name])
            for player in PLAYERS:
                loaded = {**banks(new[player]), **banks(new[name])}
                jloaded = {**banks(old[player]), **banks(jp[name])}
                prior_loaded = {**banks(old[player]), **banks(old[name])}
                for command in report["commands_reaching_target_tones"]:
                    current = run(new["SLUS_005.61"], loaded, 2, command)
                    origin = run(old["SLUS_005.61"], jloaded, 2, command)
                    prior = run(old["SLUS_005.61"], prior_loaded, 2, command)
                    require(current and len(current) == len(origin) == len(prior), "JP/native call multiplicity differs")
                    targeted = {r["packed_tone"] for r in report["target_tones"]}
                    for c, jc, pc in zip(current, origin, prior):
                        if c["program"] * 16 + c["tone"] in targeted:
                            require(all(c[k] == jc[k] for k in ("bank", "program", "tone", "channel", "note", "fine", "left", "right", "tone_volume")),
                                    "JP/native key-on settings differ: " + repr((name, player, command, c, jc)))
                            require(c["pcm_nonzero"] and c["left"] > 0 and c["right"] > 0, "Restored call is silent")
                        elif pc["tone_volume"] == 0:
                            # An existing muted tone may share a reclaimed wave. Keep its exact muted settings;
                            # its raw hash can change without making this untouched tone audible.
                            require(all(c[k] == pc[k] for k in c if k not in ("wave_sha256", "pcm_nonzero"))
                                    and c["left"] == c["right"] == 0, "Untouched muted tone became audible")
                        else:
                            require(c == pc, "Untouched stacked sound changed")
                    cpu_cases.append({"arc": name, "player": player, "command": command, "calls": current})
            reports[name] = report
        protected = player_contract.preserve_player_audio(old, new)
        player_cases = player_contract.inspect(new)
        require(player_cases == player_contract.inspect(old), "Player calls differ from parent")
        for player in PLAYERS:
            require(old[player] == new[player], "Player graphics/UI/audio ARC changed")
        sectors = compare_sectors(source, target, {name: new[name] for name in set(COMBAT) | {"SLUS_005.61"}}, records)
        cue = target.with_suffix(".cue").read_text("ascii")
        original_cue = source.with_suffix(".cue").read_text("ascii")
        require(cue == original_cue and f'FILE "{stem}.bin" BINARY' in cue, "CUE structure/reference changed")
        projects[project] = {"bin": target.relative_to(ROOT).as_posix(), "bin_sha256": expected,
            "parent_sha256": spec["bin_sha256"], "EXE_only_one_instruction_changed": True,
            "EXE_SHA256": sha(expected_exe), "combat_ARCs": reports, "protected_player_audio_banks": protected,
            "player_native_cases": len(player_cases), "boss_native_cases": cpu_cases,
            "non_target_graphics_UI_dialogue_XA_movie_exact": True, **sectors}
    for rel, p in protection["files"].items():
        require(digest(ROOT / rel) == p["sha256"], "Protected input changed during audit: " + rel)
    result = {"passed": True, "projects": projects, "protected_file_count": protection["file_count"],
              "protected_files_before_after_exact": True, "SPU_dispatch_SDK_mocked": True,
              "runtime_or_listening_verified_by_this_audit": False, "disc_or_pointer_modified": False,
              "limitations": ["실제보스앞CD스트리밍/청취/모든전투호출실기는별도", "재인코딩6파형의대역폭은원본보다낮으며무손실이라고하지않음"]}
    with result_path.open("x", encoding="utf-8") as stream:
        json.dump(result, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    print(json.dumps({"passed": True, "projects": {k: {"sha": v["bin_sha256"], "sectors": v["changed_sector_count"], "boss_native_cases": len(v["boss_native_cases"])} for k, v in projects.items()}}))


if __name__ == "__main__":
    main()
