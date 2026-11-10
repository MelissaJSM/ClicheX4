"""최종 디스크를 승인 자원에서 독립 재구성하여 전섹터 대조한다. 읽기 전용."""
import argparse
import json
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(OUT))
from verify_audio import assets, check_delta, digest, load, require, sha, PLAYERS, PREPARED
from scripts.discover_inputs import DiscReader
from src.psx_sector import rebuild_checks, validate_checks


def records(path):
    with path.open("rb") as stream:
        reader = DiscReader(stream, path.stat().st_size)
        return reader.inspect()["files"]


def compare_sectors(source, target, replacements, by_name):
    payloads = {}
    for name, data in replacements.items():
        r = by_name[name]
        require(len(data) == r["size"], "Replacement length differs")
        for pos in range(0, len(data), 2048):
            lba = r["lba"] + pos // 2048
            require(lba not in payloads, "Overlapping replacement files")
            payloads[lba] = data[pos:pos+2048]
    count, changed = 0, []
    with source.open("rb") as left, target.open("rb") as right:
        while previous := left.read(2352):
            current = right.read(2352)
            require(len(previous) == len(current) == 2352, "Disc truncated")
            if previous != current:
                require(count in payloads, "Non-target sector changed")
                data = payloads[count]
                expected = rebuild_checks(previous[:24] + data + previous[24+len(data):])
                require(current == expected, "Raw sector differs beyond approved payload and checksums")
                validate_checks(current)
                changed.append(count)
            count += 1
        require(not right.read(1), "Target has extra data")
    return {"all_sectors_compared": count, "changed_sector_count": len(changed), "changed_lbas": changed,
        "all_other_raw_sectors_exact": True, "headers_and_partial_sector_padding_exact": True,
        "EDC_ECC_verified": True}


def protection_check(snapshot):
    for rel, item in snapshot["files"].items():
        path = ROOT / rel
        require(path.stat().st_size == item["size"] and digest(path) == item["sha256"], "Protected input changed: " + rel)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", choices=("ver_buki_riko", "ver_rin_nana"), required=True)
    parser.add_argument("--sha256", required=True)
    parser.add_argument("--capsule-proposal", type=Path)
    args = parser.parse_args()
    snapshot = load(OUT / "protection_before.json")
    protection_check(snapshot)
    require(load(OUT / "audio_independent.json")["passed"], "Audio independent check incomplete")
    spec = snapshot["projects"][args.project]
    source = ROOT / spec["bin"]
    stem = "shibuki_riko" if args.project == "ver_buki_riko" else "rin_nana"
    target = ROOT / "out" / args.project / "hurt_capsule_fix_20261106_v1" / (stem + ".bin")
    require(source.resolve() != target.resolve() and not source.samefile(target), "Source/output alias")
    require(digest(source) == spec["bin_sha256"] and digest(target) == args.sha256, "Source/target hash differs")
    iso = records(source)
    require(iso == records(target), "ISO structure differs")
    by_name = {r["name"].split(";")[0]: r for r in iso if not r["directory"]}
    names = set(PLAYERS) | {"SLUS_005.61"}
    old, actual = assets(source, names), assets(target, names)
    require(old["SLUS_005.61"] == actual["SLUS_005.61"], "EXE changed")
    proposal = load(PREPARED / args.project / "proposal.json")
    require(proposal["baseline_sha256"] == spec["bin_sha256"], "Proposal parent differs")
    expected, delta = {}, {}
    for name in PLAYERS:
        desc = proposal["files"][name]
        data = (ROOT / desc["path"]).read_bytes()
        require(sha(old[name]) == desc["before"] and sha(data) == desc["after"], "Prepared resource hash differs")
        offset = check_delta(old[name], data)
        expected[name] = data
        delta[name] = {"hurt_volume_offset": offset, "before": 90, "after": 104}
    capsule = None
    require(args.capsule_proposal is None,
            "최종 범위는 두 모드 피격음만이다. 미재현 캡슐 자원 변경을 허용하지 않음")
    for name in PLAYERS:
        require(actual[name] == expected[name], "Final ARC differs from exact prepared resource: " + name)
        delta[name]["final_sha256"] = sha(actual[name])
    sectors = compare_sectors(source, target, expected, by_name)
    require(sectors["changed_sector_count"] == 3, "Each mode must change exactly three sectors")
    cue = target.with_suffix(".cue").read_bytes()
    require(cue == source.with_suffix(".cue").read_bytes() and f'FILE "{stem}.bin" BINARY'.encode() in cue,
            "CUE track structure/link changed")
    protection_check(snapshot)
    report = {"passed": True, "project": args.project, "bin": target.relative_to(ROOT).as_posix(),
        "bin_sha256": args.sha256, "parent_sha256": spec["bin_sha256"], "EXE_identical": True,
        "EXE_sha256": sha(actual["SLUS_005.61"]), "resource_changes": delta, "capsule": capsule,
        "capsule_graphics_and_timing_unchanged": True,
        "capsule_issue_status": "현재 후반 불일치 미재현. 수정 완료가 아니며 사용자 장면 확인 대기.",
        "ISO_layout_identical": True, "CUE_structure_and_link_valid": True,
        "all_boss_voices_XA_text_UI_non_target_art_unchanged": True, **sectors,
        "protected_files_count": snapshot["file_count"], "protected_files_before_after_exact": True,
        "audio_independent_evidence": {"path": (OUT / "audio_independent.json").relative_to(ROOT).as_posix(),
            "sha256": digest(OUT / "audio_independent.json")},
        "game_runtime_tested_by_this_audit": False, "game_or_state_or_pointer_written": False}
    output = OUT / (args.project + "_disc_independent.json")
    with output.open("x", encoding="utf-8") as stream:
        json.dump(report, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    print(json.dumps({"passed": True, "project": args.project, "sectors": sectors["all_sectors_compared"],
        "changed": sectors["changed_sector_count"], "output": output.relative_to(ROOT).as_posix()}))


if __name__ == "__main__":
    main()
