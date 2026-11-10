"""제작 패처와 별도로 피격음의 한 바이트 변경 및 실제 명령 회귀를 검사한다."""
from __future__ import annotations
import hashlib
import json
import math
from pathlib import Path
import struct
import sys

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from scripts.discover_inputs import DiscReader, psx_arc
from scripts.overhaul_audio_verify_cpu import banks, run
PREPARED = OUT.parent / "audio/prepared_v1"
PLAYERS = ("PL00_U.ARC", "PL01_U.ARC", "PL02_U.ARC")
HURT = "3849f73da2ec664732118255463da30fcd8438fc29ef37db4b0b18c1b8c51029"


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def digest(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def load(path):
    return json.loads(path.read_text("utf-8"))


def assets(path, names):
    with path.open("rb") as stream:
        reader = DiscReader(stream, path.stat().st_size)
        records = {r["name"].split(";")[0]: r for r in reader.inspect()["files"] if not r["directory"]}
        return {name: reader.read(records[name]["lba"], records[name]["size"]) for name in names}


def check_delta(before, after):
    require(len(before) == len(after), "ARC size differs")
    es = psx_arc(before)
    require([(x["index"], x["offset"], x["size"], x["type"]) for x in es] ==
            [(x["index"], x["offset"], x["size"], x["type"]) for x in psx_arc(after)], "ARC structure changed")
    before_banks, after_banks = banks(before), banks(after)
    h, b, q = before_banks[3]
    found = [e for e in es if before[e["offset"]:e["offset"]+e["size"]] == h]
    require(len(found) == 1, "Ambiguous bank3 header")
    tone = q["vab_offset"] + 32 + 128 * 16
    require(h[tone+2] == 90 and struct.unpack_from("<H", h, tone+22)[0] == 1,
            "Unexpected original hurt tone")
    offset = found[0]["offset"] + tone + 2
    require(q["waves"][0]["sha256"] == HURT, "Wrong X6 hurt sample")
    expected = bytearray(before)
    expected[offset] = 104
    require(after == bytes(expected), "Change outside exact hurt volume byte")
    for slot in before_banks:
        a, b2 = before_banks[slot], after_banks[slot]
        require(a[1] == b2[1] and a[2]["waves"] == b2[2]["waves"], "Raw sample/offset changed")
        if slot != 3:
            require(a == b2, "Other sound bank changed")
    return offset


def main():
    before_report = load(OUT / "protection_before.json")
    result = {"passed": True, "projects": {}, "negative_tests": [],
        "independent_dispatcher_SDK_mocked": True, "full_native_SDK_evidence": [],
        "real_hardware_mix_or_listening_verified": False}
    count = 0
    for mode, baseline in before_report["projects"].items():
        proposal = load(PREPARED / mode / "proposal.json")
        verification_path = PREPARED / mode / "verification.json"
        verification = load(verification_path)
        source = ROOT / baseline["bin"]
        require(digest(source) == baseline["bin_sha256"] == proposal["baseline_sha256"], "Parent hash differs")
        old = assets(source, set(PLAYERS) | {"SLUS_005.61", "ST6_1_1.ARC", "ONPARE6.ARC"})
        rows = {}
        for name in PLAYERS:
            desc = proposal["files"][name]
            current = (ROOT / desc["path"]).read_bytes()
            require(sha(old[name]) == desc["before"] and sha(current) == desc["after"], "Proposal hash differs")
            offset = check_delta(old[name], current)
            before_banks, after_banks = banks(old[name]), banks(current)
            cases = []
            for command in range(13):
                a = run(old["SLUS_005.61"], before_banks, 3, command)
                b = run(old["SLUS_005.61"], after_banks, 3, command)
                count += 2
                if command in (0, 1):
                    require(len(a) == len(b) == 1, "Hurt command gained another channel")
                    require(a[0]["wave_sha256"] == b[0]["wave_sha256"] == HURT and b[0]["tone_volume"] == 104,
                            "Wrong hurt routing")
                    require(b[0]["left"] > a[0]["left"] and b[0]["right"] > a[0]["right"], "Gain did not rise")
                    for key in a[0]:
                        if key not in ("tone_volume", "left", "right"):
                            require(a[0][key] == b[0][key], "Other hurt parameter changed")
                else:
                    require(a == b, "Other player command changed")
                if command not in (0, 1, 12) and not (command == 10 and name == "PL01_U.ARC"):
                    require(all(not c["pcm_nonzero"] for c in b), "Protagonist voice is no longer silent")
                cases.append({"command": command, "before": a, "after": b})
            peacock = []
            for stage in ("ST6_1_1.ARC", "ONPARE6.ARC"):
                for command in (196, 199):
                    a = run(old["SLUS_005.61"], {**before_banks, **banks(old[stage])}, 2, command)
                    b = run(old["SLUS_005.61"], {**after_banks, **banks(old[stage])}, 2, command)
                    count += 2
                    require(a == b and all(c["left"] > 0 and c["pcm_nonzero"] for c in b), "C06 player-bank voice changed")
                    peacock.append({"stage": stage, "command": command, "unchanged": True})
            v = verification["checks"][name]
            require(v["offset"] == offset and v["volume_after"] == 104 and len(v["native_cases"]) == 13,
                    "Actual SDK report does not match this resource")
            for c in v["native_cases"]:
                if c["command"] in (0, 1):
                    a, b = c["before"][0], c["after"][0]
                    require(a["volume_left"] == a["volume_right"] == 4131 and
                            b["volume_left"] == b["volume_right"] == 7366 and
                            b["wave_sha256"] == HURT and b["pitch"] == 1024 and b["native_SDK_unmocked"],
                            "Actual SDK gain mismatch")
                    require(b["solo_peak_bound_at_full_ADSR"] < 32767, "Isolated hurt clipping")
                else:
                    require(c["before"] == c["after"], "SDK non-hurt regression")
            for item in verification["unchanged_native_code"]:
                start, end = int(item["start"], 16), int(item["end"], 16)
                require(sha(old["SLUS_005.61"][start-0x10000+2048:end-0x10000+2048]) == item["sha256"],
                        "Actual SDK bytes differ from current parent")
            mutants = []
            x = bytearray(current); x[offset] = 127; mutants.append(("unapproved_gain", bytes(x)))
            x = bytearray(current); x[4096] ^= 1; mutants.append(("unrelated_graphic", bytes(x)))
            x = bytearray(current); x[offset+32] ^= 1; mutants.append(("death_tone_changed", bytes(x)))
            for reason, mutant in mutants:
                try:
                    check_delta(old[name], mutant)
                except ValueError:
                    result["negative_tests"].append({"mode": mode, "file": name, "case": reason, "rejected": True})
                else:
                    raise ValueError("Unsafe mutation accepted")
            rows[name] = {"before_sha256": sha(old[name]), "after_sha256": sha(current),
                "changed_offset": offset, "changed_bytes": 1, "all_other_bytes_exact": True,
                "native_dispatcher_cases": cases, "C06_shared_player_bank_regression": peacock}
        result["projects"][mode] = {"parent_sha256": baseline["bin_sha256"], "files": rows}
        result["full_native_SDK_evidence"].append({"path": verification_path.relative_to(ROOT).as_posix(),
            "sha256": digest(verification_path), "code_and_resource_bound": True, "SDK_mocked": False})
    result["dispatcher_executions"] = count
    result["hurt_gain_db"] = 20 * math.log10(7366 / 4131)
    result["negative_count"] = len(result["negative_tests"])
    target = OUT / "audio_independent.json"
    with target.open("x", encoding="utf-8") as stream:
        json.dump(result, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    print(json.dumps({"passed": True, "executions": count, "negative_tests": len(result["negative_tests"]),
        "gain_db": result["hurt_gain_db"], "evidence": target.relative_to(ROOT).as_posix()}))


if __name__ == "__main__":
    main()
