"""워크스페이스의 기존 상태/카드를 읽기 전용으로 목록화한다. GUI/게임 쓰기 없음."""
import gzip
import hashlib
import json
from pathlib import Path
import struct
import subprocess

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent / "runtime_candidates.json"
RP = 442
PLAYER = 0x1418C8
CALL = 0x921E8
EXPECTED_PREFIX = bytes.fromhex("e8ffbd271000b0afff0090300800022e")


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def main():
    if OUT.exists():
        raise FileExistsError(OUT)
    command = ["rg", "--files", "--no-ignore", "work", "-g", "*.00?", "-g", "*.gz",
               "-g", "!work/tools/**", "-g", "!work/research/**"]
    found = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, check=True).stdout.splitlines()
    unique, errors, skipped = {}, [], []
    for rel in found:
        path = ROOT / rel
        if path.stat().st_size > 8 * 1024 * 1024:
            skipped.append({"path": path.relative_to(ROOT).as_posix(), "reason": "over8MB_not_standard_checkpoint"})
            continue
        packed = path.read_bytes()
        if packed[:2] != b"\x1f\x8b":
            continue
        digest = sha(packed)
        if digest in unique:
            unique[digest]["aliases"].append(path.relative_to(ROOT).as_posix())
            continue
        try:
            raw = gzip.decompress(packed)
            if raw[:5] != b"ePSXe" or len(raw) < RP + 0x200000:
                continue
            ram = raw[RP:RP + 0x200000]
            authenticated = ram[CALL:CALL + 16] == EXPECTED_PREFIX
            p = ram[PLAYER:PLAYER + 228]
            info = {"path": path.relative_to(ROOT).as_posix(), "aliases": [], "sha256": digest,
                    "bytes": len(packed), "decoded_bytes": len(raw), "psx_ram_offset": RP,
                    "ram_authenticated_by_US_function_prefix": authenticated,
                    "disc_id": raw[7:18].decode("ascii", errors="replace"),
                    "engine_state": ram[0x1721C0], "stage": ram[0x1721CC], "area": ram[0x1721CD],
                    "character": p[2], "player_state": list(p[4:8]), "hp": p[0x5C],
                    "animation": p[0x17], "frame": p[0x47], "boss_flags": p[0xB9],
                    "armor": p[0xA7], "ultimate_or_black": ram[0x1721F7],
                    "world": [struct.unpack_from("<i", p, o)[0] / 65536 for o in (8, 12)],
                    "boss_music_delay_byte": ram[0x1721F6],
                    "xa_busy_word": struct.unpack_from("<I", ram, 0x173C84)[0],
                    "boss_voice_branch_hex": ram[0x921F8:0x921FC].hex(),
                    "boss_voice_function_sha256": sha(ram[0x921E8:0x9227C]),
                    "player_sha256": sha(p), "engine_progress_sha256": sha(ram[0x1721C0:0x172220])}
            unique[digest] = info
        except (ValueError, OSError, struct.error) as exc:
            errors.append({"path": rel, "reason": str(exc)})
    rows = list(unique.values())
    groups = {}
    for r in rows:
        if not r["ram_authenticated_by_US_function_prefix"]:
            continue
        key = f'{r["stage"]}:{r["area"]}:character{r["character"]}'
        groups.setdefault(key, []).append(r)
    summary = []
    for key, items in sorted(groups.items()):
        summary.append({"group": key, "unique_states": len(items),
                        "min_x": min(r["world"][0] for r in items), "max_x": max(r["world"][0] for r in items),
                        "last_world_x_candidates": [r["path"] for r in sorted(items, key=lambda x:x["world"][0], reverse=True)[:3]]})
    cards = json.loads((ROOT / "work/sprite_consistency_20261105/coverage/runtime_card_inventory.json").read_text("utf-8"))
    card_rows = []
    for card in cards["cards"]:
        actual = (ROOT / card["path"]).read_bytes()
        if sha(actual) != card["sha256"]:
            raise ValueError("Card no longer matches earlier read-only inventory")
        card_rows.append({"path": card["path"], "sha256": card["sha256"],
                          "slots": [{k:v for k,v in s.items() if k not in ("raw_hex", "native_progress_words")}
                                    for s in card["x4_slots"] if not s["empty"]]})
    result = {"scope": "기존 work의 상태 gzip/슬롯 및 이미 조사된 카드. 원본 읽기만; 게임 조작 없음.",
              "candidate_files": len(found), "unique_states": len(rows), "groups": summary,
              "states": rows, "cards": card_rows, "errors": errors, "skipped": skipped,
              "source_files_modified": False, "emulator_control": False,
              "warning": "stage/area/world/타이머만으로 보스 개전 직전이라고 확정하지 않는다. 별도 객체 상태·화면 증거 필요."}
    with OUT.open("x", encoding="utf-8") as stream:
        json.dump(result, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    print(json.dumps({"candidate_files": len(found), "unique_states": len(rows), "groups": summary,
                      "errors": len(errors), "cards": len(card_rows)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
