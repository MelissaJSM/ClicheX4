"""실제 X4 명령 디스패처로 주인공 무음/X6/낙봉파39명령의 회귀를 검사한다.

SPU SDK는 기존 격리 하네스의 모킹이며 실기/청취 검사로 보고하지 않는다.
모든 게임 파일은 rb로만 읽고 출력은 이 audit 디렉터리에만 새로 기록한다.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
AUDIT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from scripts.discover_inputs import DiscReader
from scripts.overhaul_audio_verify_cpu import banks, run

PLAYERS = ("PL00_U.ARC", "PL01_U.ARC", "PL02_U.ARC")
SFX = {
    0: ("3849f73da2ec664732118255463da30fcd8438fc29ef37db4b0b18c1b8c51029", 59, 83, 90, 0, 1),
    1: ("3849f73da2ec664732118255463da30fcd8438fc29ef37db4b0b18c1b8c51029", 59, 83, 90, 0, 1),
    12: ("bca9ec5b6b47b1247ec483f6b95cb8de3d94c58e03132255c63df5f434e4cfbc", 60, 80, 100, 1, 2),
}


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def digest(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for data in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            h.update(data)
    return h.hexdigest()


def read(path, expected):
    require(digest(path) == expected, "Unsupported input hash")
    names = set(PLAYERS) | {"SLUS_005.61"}
    with path.open("rb") as stream:
        reader = DiscReader(stream, path.stat().st_size)
        files = {r["name"].split(";")[0]: r for r in reader.inspect()["files"]
                 if not r["directory"] and r["name"].split(";")[0] in names}
        require(set(files) == names, "Missing requested resources")
        result = {name: reader.read(r["lba"], r["size"]) for name, r in files.items()}
    return result


def inspect(assets):
    rows = []
    for name in PLAYERS:
        loaded = banks(assets[name])
        for command in range(13):
            calls = run(assets["SLUS_005.61"], loaded, 3, command)
            require(calls, "No native sound call")
            if command in SFX:
                expected, note, center, volume, tone, wave = SFX[command]
                require(len(calls) == 1, "Unexpected stacked C01 effect")
                c = calls[0]
                require(c["wave_sha256"] == expected and c["bank"] == 3
                        and c["channel"] == 20 and c["note"] == note and c["center"] == center
                        and c["tone_volume"] == volume and c["fine"] == 0
                        and c["tone"] == tone and c["wave"] == wave
                        and c["left"] > 0 and c["right"] > 0 and c["pcm_nonzero"],
                        "X6 hurt/death contract failed")
                kind = "X6_nonvoice_hurt" if command != 12 else "X6_nonvoice_death"
            elif command == 10 and name == "PL01_U.ARC":
                require(all(c["bank"] == 1 and c["pcm_nonzero"] for c in calls), "Rakuhouha effect missing")
                kind = "Rakuhouha_nonvoice_effect"
            else:
                require(all(c["bank"] == 3 and not c["pcm_nonzero"] for c in calls), "Protagonist voice unmuted")
                kind = "muted_protagonist_voice"
            rows.append({"player": name, "command": command, "kind": kind, "calls": calls})
    return rows


def preserve_player_audio(before, after):
    rows = []
    for name in PLAYERS:
        old, new = banks(before[name]), banks(after[name])
        require(set(old) == set(new), "Player audio bank set changed")
        for slot in old:
            require(old[slot][0] == new[slot][0] and old[slot][1] == new[slot][1],
                    f"Protected player audio bytes changed: {name} bank{slot}")
            rows.append({"player": name, "slot": slot, "header_and_body_exact": True})
    return rows


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--project", choices=("ver_buki_riko", "ver_rin_nana"))
    p.add_argument("--target-bin", type=Path)
    p.add_argument("--target-sha")
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    output = a.output.resolve()
    require(output.is_relative_to(AUDIT) and not output.exists(), "Output must be a new audit JSON")
    target_mode = a.target_bin is not None or a.target_sha is not None
    require(not target_mode or (a.project and a.target_bin and a.target_sha), "Target needs project/path/hash")
    before = json.loads((AUDIT / "protection_before.json").read_text("utf-8"))
    projects = {}
    for project, spec in before["projects"].items():
        if a.project and project != a.project:
            continue
        source = ROOT / spec["bin"]
        old = read(source, spec["bin_sha256"])
        expected = inspect(old)
        current = expected
        protected = preserve_player_audio(old, old)
        if target_mode:
            target = a.target_bin.resolve()
            require(target != source.resolve() and not target.samefile(source), "Source cannot be target")
            new = read(target, a.target_sha)
            protected = preserve_player_audio(old, new)
            current = inspect(new)
            require(current == expected, "Player command output changed")
        projects[project] = {"parent_sha256": spec["bin_sha256"], "target_sha256": a.target_sha,
                             "cases": len(current), "all_player_calls_equal_parent": current == expected,
                             "protected_audio_banks": protected,
                             "rows": current}
    require(bool(projects), "No project selected")
    result = {"passed": True, "native_X4_dispatcher": "0x8001540C/0x800154E8",
              "SPU_SDK_mocked": True, "runtime_verified": False, "listening_verified": False,
              "source_games_modified": False, "projects": projects}
    with output.open("x", encoding="utf-8") as stream:
        json.dump(result, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    print(json.dumps({"passed": True, "cases": sum(v["cases"] for v in projects.values()),
                      "target_comparison": target_mode, "output": output.relative_to(ROOT).as_posix()}))


if __name__ == "__main__":
    main()
