"""기존 C06 호출과 보호 거부 검사를 읽기 전용으로 감사한다."""
import json
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import player_contract as contract
from scripts.discover_inputs import DiscReader, psx_arc
from scripts.overhaul_audio_verify_cpu import banks, run


def main():
    out = Path(__file__).resolve().parent / "baseline_checks.json"
    if out.exists():
        raise FileExistsError(out)
    specs = json.loads((out.parent / "protection_before.json").read_text("utf-8"))["projects"]
    rows, rejection = [], []
    for project, spec in specs.items():
        path = ROOT / spec["bin"]
        assets = contract.read(path, spec["bin_sha256"])
        with path.open("rb") as stream:
            reader = DiscReader(stream, path.stat().st_size)
            disc = reader.inspect()
            for stage, commands in ((5, (178,)), (6, (196, 199)), (7, (190,))):
                for name in (f"ST{stage}_1_1.ARC", f"ONPARE{stage}.ARC"):
                    rec = next(r for r in disc["files"] if r["name"] == name + ";1")
                    boss = reader.read(rec["lba"], rec["size"])
                    for player in contract.PLAYERS:
                        loaded = {**banks(assets[player]), **banks(boss)}
                        for command in commands:
                            calls = run(assets["SLUS_005.61"], loaded, 2, command)
                            contract.require(calls and all(c["pcm_nonzero"] and c["tone_volume"] > 0
                                             and c["left"] > 0 and c["right"] > 0 for c in calls),
                                             "Existing C06 sound missing")
                            rows.append({"project": project, "boss": name, "player": player,
                                         "command": command, "calls": calls})
        raw = assets["PL00_U.ARC"]
        entries = psx_arc(raw)
        bh, _, q = banks(raw)[3]
        header = next(e for e in entries if raw[e["offset"]:e["offset"] + e["size"]] == bh)
        for label, offset in (("VAB_master_volume", header["offset"] + q["vab_offset"] + 24),
                              ("protagonist_command2", header["offset"] + 8 + 2 * 4),
                              ("tone0_ADSR", header["offset"] + q["vab_offset"] + 32 + 128 * 16 + 16)):
            changed = bytearray(raw)
            changed[offset] ^= 1
            revised = {**assets, "PL00_U.ARC": bytes(changed)}
            try:
                contract.preserve_player_audio(assets, revised)
            except ValueError as exc:
                rejection.append({"project": project, "case": label, "rejected": True, "reason": str(exc)})
            else:
                raise AssertionError("Mutation accepted: " + label)
        try:
            contract.read(path, "0" * 64)
        except ValueError as exc:
            rejection.append({"project": project, "case": "wrong_parent_sha", "rejected": True, "reason": str(exc)})
        else:
            raise AssertionError("Wrong parent accepted")
    result = {"passed": True, "existing_C06_native_dispatch_calls": len(rows), "cases": rows,
              "negative_cases": rejection, "SPU_SDK_mocked": True,
              "runtime_or_listening_verified": False, "games_or_protected_files_modified": False}
    with out.open("x", encoding="utf-8") as stream:
        json.dump(result, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    print(json.dumps({"passed": True, "C06_cases": len(rows), "negative_cases": len(rejection)}))


if __name__ == "__main__":
    main()
