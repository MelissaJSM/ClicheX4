"""최신 부모 EXE를 직접 읽어 8보스 개전 분기 수정과 원래 대기 동작을 독립 검사한다."""
import hashlib
import json
from pathlib import Path
import struct
import sys
from unicorn import Uc, UC_ARCH_MIPS, UC_MODE_MIPS32, UC_MODE_LITTLE_ENDIAN, UC_HOOK_CODE
from unicorn import mips_const as m

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from scripts.discover_inputs import DiscReader
from scripts.restore_boss_intro_voices import patch_exe

RETURN = 0x80004000
TIMER = 0x1721F6
BUSY = 0x173C84
BRANCH = 0x921F8
ENTER = 0x800921E8
WAIT = 0x8009227C
RNG = 0x8002B73C
XA = 0x8001663C
MUSIC = 0x8001653C


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def read_exe(path, name):
    with path.open("rb") as stream:
        reader = DiscReader(stream, path.stat().st_size)
        r = next(r for r in reader.inspect()["files"] if r["path"] == "/" + name + ";1")
        return reader.read(r["lba"], r["size"])


def slice_va(exe, address, length):
    base = struct.unpack_from("<I", exe, 0x18)[0]
    offset = address - base + 2048
    require(2048 <= offset and offset + length <= len(exe), "VA outside EXE")
    return exe[offset:offset + length]


class CPU:
    def __init__(self, exe):
        self.u = Uc(UC_ARCH_MIPS, UC_MODE_MIPS32 | UC_MODE_LITTLE_ENDIAN)
        self.u.ctl_set_cpu_model(m.UC_CPU_MIPS32_4KC)
        self.u.mem_map(0, 0x200000)
        base, size = struct.unpack_from("<II", exe, 0x18)
        self.u.mem_write(base & 0x1FFFFFFF, exe[2048:2048 + size])
        self.rng = 0
        self.calls = []

        def hook(u, pc, size, data):
            if pc == RETURN:
                u.emu_stop()
            elif pc == RNG:
                u.reg_write(m.UC_MIPS_REG_V0, self.rng)
                u.reg_write(m.UC_MIPS_REG_PC, u.reg_read(m.UC_MIPS_REG_RA))
            elif pc in (XA, MUSIC):
                self.calls.append({"api": "xa" if pc == XA else "music",
                                   "a0": u.reg_read(m.UC_MIPS_REG_A0), "a1": u.reg_read(m.UC_MIPS_REG_A1)})
                u.reg_write(m.UC_MIPS_REG_PC, u.reg_read(m.UC_MIPS_REG_RA))
        for address in (RETURN, RNG, XA, MUSIC):
            self.u.hook_add(UC_HOOK_CODE, hook, begin=address, end=address)

    def run(self, address, argument=0):
        u = self.u
        self.calls = []
        u.reg_write(m.UC_MIPS_REG_A0, argument)
        u.reg_write(m.UC_MIPS_REG_SP, 0x801FF000)
        u.reg_write(m.UC_MIPS_REG_RA, RETURN)
        saved = [m.UC_MIPS_REG_S0, m.UC_MIPS_REG_S1, m.UC_MIPS_REG_S2, m.UC_MIPS_REG_S3,
                 m.UC_MIPS_REG_S4, m.UC_MIPS_REG_S5, m.UC_MIPS_REG_S6, m.UC_MIPS_REG_S7, m.UC_MIPS_REG_FP]
        for i, reg in enumerate(saved):
            u.reg_write(reg, 0x12340000 + i)
        before = bytes(u.mem_read(0, 0x200000))
        u.emu_start(address, RETURN, count=10000)
        require(u.reg_read(m.UC_MIPS_REG_PC) == RETURN, "Native function did not return")
        require(u.reg_read(m.UC_MIPS_REG_SP) == 0x801FF000, "Stack pointer changed")
        require(all(u.reg_read(reg) == 0x12340000 + i for i, reg in enumerate(saved)), "Saved register changed")
        after = bytes(u.mem_read(0, 0x200000))
        require(before[:TIMER] == after[:TIMER] and before[TIMER + 1:0x1FEF00] == after[TIMER + 1:0x1FEF00]
                and before[0x1FF000:] == after[0x1FF000:], "Unexpected RAM write outside timer/stack")
        return {"calls": list(self.calls), "timer": after[TIMER]}


def main():
    output = OUT / "current_intro_native.json"
    require(not output.exists(), "Evidence already exists")
    before = json.loads((OUT / "protection_before.json").read_text("utf-8"))
    exes = {project: read_exe(ROOT / r["bin"], "SLUS_005.61") for project, r in before["projects"].items()}
    require(len(set(map(sha, exes.values()))) == 1, "Current project EXEs differ")
    source = next(iter(exes.values()))
    require(sha(source) == "1789ef719487b3e49571ccc2f419d6eb36c16f03709a16cb74f856d433f699ab", "Unsupported current EXE")
    ref = read_exe(ROOT / "MegaMan X4.bin", "SLUS_005.61")
    jp = read_exe(ROOT / "Rockman X4.bin", "SLPS_009.02")
    maps = json.loads((ROOT / "work/boss_voice_restore_20261105/calls/xa_mapping.json").read_text("utf-8"))
    ranges = [(0x800921E8, 0xF0, "play_boss_voice and music delay"),
              (0x80105FC8, 39, "13x3 track IDs"),
              (0x8001663C, 0x80, "XA wrapper"), (0x8001653C, 0x90, "music wrapper")]
    for boss in maps["us"]["bosses"]:
        for clip in boss["clips"]:
            ranges.append((int(clip["entry_address"], 16), 4, "XA start/end/channel entry"))
    ranges = list(dict.fromkeys(ranges))
    for address, length, label in ranges:
        require(slice_va(source, address, length) == slice_va(ref, address, length), "Original/current data differ: " + label)
    us_tracks = slice_va(source, 0x80105FC8, 39)
    jp_tracks = slice_va(jp, 0x80106104, 39)
    require(us_tracks == jp_tracks, "JP/current track selection differs")
    for index in range(13):
        require(list(us_tracks[index * 3:index * 3 + 3]) == maps["us"]["bosses"][index]["track_ids"]
                == maps["jp"]["bosses"][index]["track_ids"], "Mapping JSON differs from source table")
    offset = BRANCH - 0x10000 + 2048
    require(source[offset:offset + 4] == bytes.fromhex("18004014"), "Original branch differs")
    patched = source[:offset] + bytes(4) + source[offset + 4:]
    expected_by_builder, builder_offset = patch_exe(source)
    require(patched == expected_by_builder and offset == builder_offset, "Builder patch differs from independent splice")
    new_cpu, old_cpu = CPU(patched), CPU(source)
    cases = 0
    for boss in range(13):
        for rng in range(256):
            track = us_tracks[boss * 3 + rng % 3]
            expected = {"calls": [{"api": "xa", "a0": track, "a1": 127}], "timer": 1}
            for cpu in (new_cpu, old_cpu):
                cpu.rng = rng
                cpu.u.mem_write(TIMER, b"\x77")
            require(new_cpu.run(ENTER, boss) == expected, "Patched current dispatch differs")
            require(old_cpu.run(ENTER, boss) == (expected if boss >= 8 else {"calls": [], "timer": 60}),
                    "Unpatched current behavior differs")
            cases += 1
    waits = []
    for label, cpu in (("parent", old_cpu), ("patched", new_cpu)):
        cpu.u.mem_write(TIMER, b"\1")
        for busy in (1, 1, 1, 0):
            cpu.u.mem_write(BUSY, bytes([busy]))
            row = cpu.run(WAIT)
            require(row["timer"] == (1 if busy else 0) and len(row["calls"]) == (0 if busy else 1), "Wait behavior differs")
            waits.append({"case": label, "busy": busy, **row})
    negative = []
    for label, bad in (("already_patched", patched), ("truncated", source[:-1]),
                       ("unrelated_byte", source[:3000] + bytes([source[3000] ^ 1]) + source[3001:])):
        try:
            patch_exe(bad)
        except ValueError as exc:
            negative.append({"case": label, "rejected": True, "reason": str(exc)})
        else:
            raise ValueError("Invalid EXE accepted")
    result = {"passed": True, "current_exe_sha256": sha(source), "patched_current_exe_sha256": sha(patched),
              "source_exe_hashes": {p: sha(v) for p, v in exes.items()},
              "original_reference_exe_sha256": sha(ref), "JP_exe_sha256": sha(jp),
              "source_equivalent_ranges": [{"address": hex(a), "size": n, "label": label,
                    "sha256": sha(slice_va(source, a, n))} for a, n, label in ranges],
              "all_13x256_current_parent_cases": cases, "all_13x256_patched_current_cases": cases,
              "native_function_executions": cases * 2 + len(waits), "wait_results": waits,
              "saved_registers_and_non_timer_RAM_preserved": True, "rejections": negative,
              "patch_file_offset": offset, "patch_bytes": 4, "actually_different_bytes": 3,
              "builder_script_sha256": sha((ROOT / "scripts/restore_boss_intro_voices.py").read_bytes()),
              "XA_calls_stubbed": True, "CD_streaming_verified": False,
              "game_or_state_files_modified": False,
              "scope": "실제 현재 EXE의 원래/수정 개전 호출 및 timer 검사. 전체게임/CD/청취 실기 아님."}
    with output.open("x", encoding="utf-8") as stream:
        json.dump(result, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    print(json.dumps({"passed": True, "current_cases": cases, "native_executions": result["native_function_executions"],
                      "rejections": len(negative), "patched_exe": sha(patched)}))


if __name__ == "__main__":
    main()
