"""현재 입력/완성본/진행/음향 보호 기준을 읽고 이 감사 폴더에만 기록한다."""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
import subprocess
import struct
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from scripts.discover_inputs import DiscReader, psx_arc
from scripts.overhaul_audio_audit import bank_commands

OUT = Path(__file__).resolve().parent
EXPECTED = {
    "ver_buki_riko": ("shibuki_riko", "5a57b31c7a4410d697183a01b2246a28344c847cefb331d27aad56135e7a924d"),
    "ver_rin_nana": ("rin_nana", "de818d585fe1a4455d9b07551f3161b24357e3a1a2343d84102628a1fde55679"),
}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def file_sha(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load(rel):
    return json.loads((ROOT / rel).read_text("utf-8"))


def write_new(path, value):
    with path.open("x", encoding="utf-8") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write("\n")


def resources(path):
    result = {"source": path.relative_to(ROOT).as_posix(), "arcs": {}, "other_form1": {}, "raw_streams": {}}
    with path.open("rb") as stream:
        reader = DiscReader(stream, path.stat().st_size)
        disc = reader.inspect()
        result["disc"] = {k: v for k, v in disc.items() if k != "files"}
        result["iso_files"] = disc["files"]
        for rec in disc["files"]:
            if rec.get("directory"):
                continue
            name = rec["path"]
            if name.startswith("/XA/") or name.endswith(".STR;1") or rec["size"] > 32 * 1024 * 1024:
                count = (rec["size"] + 2047) // 2048
                stream.seek(rec["lba"] * 2352)
                raw = stream.read(count * 2352)
                if len(raw) != count * 2352:
                    raise ValueError("Truncated stream " + name)
                result["raw_streams"][name] = {"lba": rec["lba"], "sectors": count, "sha256": sha(raw)}
                continue
            raw = reader.read(rec["lba"], rec["size"])
            if name.startswith("/ARC/") and name.endswith(".ARC;1"):
                try:
                    entries = psx_arc(raw)
                except ValueError as exc:
                    result["arcs"][name] = {"sha256": sha(raw), "size": len(raw), "lba": rec["lba"],
                                            "entries": None, "parser_limitation": str(exc)}
                    continue
                row = {"sha256": sha(raw), "size": len(raw), "lba": rec["lba"], "entries": entries}
                if name in ("/ARC/PL00_U.ARC;1", "/ARC/PL01_U.ARC;1", "/ARC/PL02_U.ARC;1"):
                    banks = []
                    for a, b in zip(entries, entries[1:]):
                        head = raw[a["offset"]:a["offset"] + a["size"]]
                        body = raw[b["offset"]:b["offset"] + b["size"]]
                        try:
                            parsed = bank_commands(head, body)
                        except (ValueError, IndexError, struct.error):
                            continue
                        if parsed["slot"] == 3:
                            banks.append({"header_entry": a["index"], "body_entry": b["index"], "bank": parsed})
                    if len(banks) != 1:
                        raise ValueError("Expected one player bank3: " + name)
                    row["protected_player_bank3"] = banks[0]
                result["arcs"][name] = row
            else:
                result["other_form1"][name] = {"lba": rec["lba"], "size": len(raw), "sha256": sha(raw)}
    return result


def main():
    output = OUT / "protection_before.json"
    if output.exists():
        raise FileExistsError("Existing before snapshot is immutable")
    initial = load("work/sprite_consistency_20261105/protection_before.json")
    if len(initial) != 31:
        raise ValueError("Unexpected prior protection inventory")
    inventory = {}

    def add(rel, role, expected=None, size=None):
        path = (ROOT / rel).resolve()
        if not path.is_relative_to(ROOT) or not path.is_file():
            raise ValueError("Missing/outside input: " + str(rel))
        key = path.relative_to(ROOT).as_posix()
        actual = file_sha(path)
        if expected is not None and actual != expected:
            raise ValueError("Protected source hash mismatch: " + key)
        if size is not None and path.stat().st_size != size:
            raise ValueError("Protected source size mismatch: " + key)
        if key in inventory:
            inventory[key]["roles"].append(role)
            return inventory[key]
        row = {"size": path.stat().st_size, "sha256": actual, "expected_sha256": expected,
               "roles": [role], "input_only": True}
        inventory[key] = row
        return row

    for rel, old in initial.items():
        add(rel, "previous_31_protected", old["sha256"], old["size"])
    final = load("work/sprite_consistency_20261105/runtime/final_integrity.json")
    if not final["passed"]:
        raise ValueError("Previous final integrity failed")
    for row in final["card_clones"]:
        for key in ("original", "clone"):
            item = row[key]
            add(item["path"], "previous_runtime_card_" + key, item["actual_sha256"], item["size"])
    for row in load("work/audio_c01_revision_20261105/local_inventory/x5_x6_discs.json")["discs"]:
        rel = Path(row["path"]).relative_to(ROOT).as_posix()
        add(rel, "provided_X5_X6_input", row["sha256"], row["size"])
    for path in ROOT.glob("*.cue"):
        add(path.relative_to(ROOT).as_posix(), "original_cue")
    add("out/ver_buki_riko/final_v1_0_0/game/shibuki_riko.cue", "first_release_cue")
    projects = {}
    for mode, (stem, expected) in EXPECTED.items():
        pointer_rel = f"projects/{mode}/current_build.json"
        pointer = load(pointer_rel)
        if pointer["sha256"] != expected:
            raise ValueError("Current pointer baseline differs")
        add(pointer_rel, "activation_pointer_before")
        bin_rel = pointer["build"] + "/" + stem + ".bin"
        add(bin_rel, "current_parent_BIN", expected)
        add(pointer["cue"], "current_parent_CUE")
        material = resources(ROOT / bin_rel)
        filename = mode + "_resources_before.json"
        write_new(OUT / filename, material)
        projects[mode] = {"bin": bin_rel, "bin_sha256": expected, "cue": pointer["cue"],
                          "resource_inventory": (OUT / filename).relative_to(ROOT).as_posix(),
                          "resource_inventory_sha256": file_sha(OUT / filename)}
    add("out/sprite_consistency_20261105/ALL_SPRITES.html", "current_sprite_album",
        "0997b82203efe919b859e0716ba684d160f09c3c2543024117244d0fa4a17fa3")
    process = subprocess.run(["powershell", "-NoProfile", "-Command",
        "@(Get-Process -Name ePSXe -ErrorAction SilentlyContinue | Select-Object Id,Path) | ConvertTo-Json -Compress"],
        capture_output=True, text=True, check=True)
    observed = json.loads(process.stdout.strip() or "[]")
    if isinstance(observed, dict):
        observed = [observed]
    result = {"schema_version": 1, "created_utc": datetime.now(timezone.utc).isoformat(),
        "scope": "31개 기존 보호파일과 명시된 새 입력·현재부모·카드사본의 읽기 전용 사전 해시. 프로젝트 전체 파일 목록 아님.",
        "passed": True, "previous_protected_count": len(initial), "file_count": len(inventory),
        "files": inventory, "projects": projects, "epsxe_processes": observed,
        "process_observation": "Get-Process 목록 읽기만. 메모리 접근·입력·포커스·종료 없음.",
        "keys_sent": False, "process_memory_written": False, "cards_or_states_modified": False,
        "original_inputs_modified": False}
    write_new(output, result)
    print(json.dumps({"passed": True, "files": len(inventory), "original_31_verified": True,
                      "epsxe_processes": observed, "output": output.relative_to(ROOT).as_posix()}, ensure_ascii=False))


if __name__ == "__main__":
    main()
