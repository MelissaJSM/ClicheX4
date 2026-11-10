"""현재 입력과 사용자 진행을 읽기만 하여 새 보호 기준을 기록한다."""
from __future__ import annotations
from datetime import datetime, timezone
import importlib.util
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("prior_snapshot", ROOT / "work/boss_voice_restore_20261105/audit/snapshot_protection.py")
old = importlib.util.module_from_spec(spec)
spec.loader.exec_module(old)
EXPECTED = {
    "ver_buki_riko": ("shibuki_riko", "ef2fcec562f02f6ba6b372e26b021924ea595abe4d654a9fc4e632a529804bb7"),
    "ver_rin_nana": ("rin_nana", "c84dcda554ae6320c9808fc55088731a7f90dc9bda391d5c0674645315b56b31"),
}


def main():
    target = OUT / "protection_before.json"
    if target.exists():
        raise FileExistsError("사전 보호 기준은 덮어쓰지 않는다")
    previous = old.load("work/boss_voice_restore_20261105/audit/protection_before.json")
    inventory, changes = {}, []

    def add(relative, role, expected=None, allow_current=False):
        path = (ROOT / relative).resolve()
        if not path.is_relative_to(ROOT) or not path.is_file():
            raise ValueError("Missing/outside input: " + str(relative))
        rel = path.relative_to(ROOT).as_posix()
        actual = old.file_sha(path)
        if expected and expected != actual:
            if not allow_current:
                raise ValueError("Immutable input changed: " + rel)
            changes.append({"path": rel, "prior_sha256": expected, "current_sha256": actual,
                            "action": "현재 파일을 새 기준으로 보존. 과거 내용으로 복원하지 않음."})
        if rel in inventory:
            inventory[rel]["roles"].append(role)
            return inventory[rel]
        inventory[rel] = {"size": path.stat().st_size, "sha256": actual,
            "mtime_utc": datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).isoformat(),
            "roles": [role], "input_only": True}
        return inventory[rel]

    for rel, item in previous["files"].items():
        progress = any(part in rel for part in ("/memcards/", "/sstates/", "/cards/", "/legacy_cards/", "/test_cards/"))
        pointer = rel.endswith("current_build.json")
        add(rel, "previous_protected", item["sha256"], progress or pointer)
    for path in (ROOT / "character").rglob("*"):
        if path.is_file():
            add(path.relative_to(ROOT).as_posix(), "user_character_reference")
    for folder in ("ePSXe2018/sstates", "ePSXe2018/memcards"):
        for path in (ROOT / folder).rglob("*"):
            if path.is_file():
                add(path.relative_to(ROOT).as_posix(), "original_epsxe2018_current_progress")
    add("ePSXe2018/ePSXe.exe", "original_epsxe2018_executable")
    for row in old.load("work/boss_voice_restore_20261105/runtime/test_cards_before.json"):
        add(row["path"], "previous_boss_voice_test_card", allow_current=True)
    projects = {}
    for mode, (stem, expected) in EXPECTED.items():
        rel = f"projects/{mode}/current_build.json"
        ptr = old.load(rel)
        if ptr["sha256"] != expected:
            raise ValueError("Current source pointer differs: " + mode)
        add(rel, "activation_pointer_before")
        add(f"projects/{mode}/project.json", "project_configuration_before")
        bin_rel = ptr["build"] + "/" + stem + ".bin"
        add(bin_rel, "current_parent_BIN", expected)
        add(ptr["cue"], "current_parent_CUE")
        resource_file = OUT / (mode + "_resources_before.json")
        old.write_new(resource_file, old.resources(ROOT / bin_rel))
        projects[mode] = {"bin": bin_rel, "bin_sha256": expected, "cue": ptr["cue"],
            "resource_inventory": resource_file.relative_to(ROOT).as_posix(),
            "resource_inventory_sha256": old.file_sha(resource_file)}
    proc = subprocess.run(["powershell", "-NoProfile", "-Command",
        "@(Get-Process -Name ePSXe -ErrorAction SilentlyContinue | Select-Object Id,Path) | ConvertTo-Json -Compress"],
        capture_output=True, text=True, check=True)
    processes = json.loads(proc.stdout.strip() or "[]")
    if isinstance(processes, dict):
        processes = [processes]
    result = {"passed": True, "created_utc": datetime.now(timezone.utc).isoformat(),
        "scope": "원본·첫 출시본·설정화·현재 부모·포인터·명시된 저장상태/카드의 읽기 전용 사전 기록. 전체 작업폴더 백업 아님.",
        "file_count": len(inventory), "files": inventory, "projects": projects,
        "changes_since_previous_baseline": changes, "epsxe_processes": processes,
        "keys_sent": False, "process_memory_written": False, "original_inputs_modified": False,
        "cards_or_states_modified": False, "old_progress_restored": False}
    old.write_new(target, result)
    print(json.dumps({"passed": True, "files": len(inventory), "changes": changes,
        "epsxe_processes": processes, "path": target.relative_to(ROOT).as_posix()}, ensure_ascii=False))


if __name__ == "__main__":
    main()
