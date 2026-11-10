"""Independently execute prepared save constructors; never write save data."""
import hashlib
import json
import struct
from pathlib import Path
from native_contracts import ROOT, cpu, finish
from unicorn import UC_HOOK_CODE, UC_HOOK_MEM_WRITE
from unicorn import mips_const as r

OUT = Path(__file__).resolve().parent
LO, HI = 0x8001BCAC, 0x8001C008
OBJ, SAVE, STACK = 0x1FA000, 0x1FB000, 0x1FF000


def sha(b): return hashlib.sha256(b).hexdigest()
def off(at): return at - 0x80010000 + 2048


def main():
    records = []
    for project in ('ver_buki_riko', 'ver_rin_nana'):
        old = (OUT.parent / 'renderer' / (project + '.exe')).read_bytes()
        path = OUT.parent / 'ui/save_code' / project / 'SLUS_005.61'
        new = path.read_bytes()
        allowed = set(range(off(0x8001BD1C), off(0x8001BD9C))) | set(range(off(0x8001BE60), off(0x8001BE64)))
        diff = [i for i, (a, b) in enumerate(zip(old, new)) if a != b]
        assert len(old) == len(new) and diff and set(diff) <= allowed
        machine = cpu(old)
        allocations, writes = [], []
        fail = False
        def allocator(u, pc, size, _):
            if pc == 0x8002AE50:
                value = 0 if fail else 0x80000000 + OBJ + len(allocations) * 256
                allocations.append(value)
                u.reg_write(r.UC_MIPS_REG_V0, value)
                u.reg_write(r.UC_MIPS_REG_PC, u.reg_read(r.UC_MIPS_REG_RA))
        def writing(u, access, address, size, value, _):
            at = address & 0x1FFFFFFF
            assert OBJ <= at < OBJ + 2048 or STACK - 64 <= at < STACK
            writes.append(at)
        machine.hook_add(UC_HOOK_CODE, allocator)
        machine.hook_add(UC_HOOK_MEM_WRITE, writing)
        current = None
        def run(exe, character, special, mask, arm, mode, failed):
            nonlocal fail, current
            blob = exe[off(LO):off(HI)]
            if current != blob:
                machine.mem_write(LO & 0x1FFFFFFF, blob)
                machine.ctl_remove_cache(LO, HI)
                current = blob
            fail = failed
            allocations.clear(); writes.clear()
            save = bytearray((i * 37 + 17) & 255 for i in range(256))
            save[0], save[0x29], save[3], save[2] = character, special, mask, arm
            machine.mem_write(SAVE, bytes(save)); machine.mem_write(OBJ, bytes(2048))
            machine.mem_write(0x1721BC, struct.pack('<I', SAVE | 0x80000000))
            machine.mem_write(0x141BDF, b'\x12'); machine.mem_write(0x1721C1, b'\x34')
            for function in (LO, 0x8001BE10):
                for reg, val in [('A0', 77), ('A1', 123), ('A2', mode), ('SP', 0x80000000 | STACK), ('RA', 0x80008000)]:
                    machine.reg_write(getattr(r, 'UC_MIPS_REG_' + reg), val)
                for n in range(8): machine.reg_write(getattr(r, 'UC_MIPS_REG_S' + str(n)), 0x13579B00 + n)
                finish(machine, function)
                assert machine.reg_read(r.UC_MIPS_REG_SP) == STACK | 0x80000000
                assert all(machine.reg_read(getattr(r, 'UC_MIPS_REG_S' + str(n))) == 0x13579B00 + n for n in range(8))
            assert bytes(machine.mem_read(SAVE, 256)) == bytes(save)
            assert bytes(machine.mem_read(0x1721BC, 4)) == struct.pack('<I', SAVE | 0x80000000)
            return bytes(machine.mem_read(OBJ, 2048)), list(allocations)
        tests = 0
        selections = []
        for character in (0, 1, 255):
            for special in (0, 1, 255):
                for mask in range(16):
                    for arm in (0, 1, 2, 255):
                        for mode in (0, 1):
                            for failed in (False, True):
                                before, ba = run(old, character, special, mask, arm, mode, failed)
                                after, aa = run(new, character, special, mask, arm, mode, failed)
                                if character == 0 and special:
                                    expected = bytearray(2048)
                                    if not failed:
                                        expected[:256] = before[:256]
                                        expected[0x47] = 53 if mask else 52
                                        struct.pack_into('<H', expected, 0x42, 0x784F if mask else 0x784E)
                                        assert aa == [OBJ | 0x80000000]
                                    else:
                                        assert aa == [0]
                                    assert after == bytes(expected)
                                else:
                                    assert (before, ba) == (after, aa)
                                tests += 1
        assert path.read_bytes() == new
        records.append(dict(project=project, source_exe_sha256=sha(old), prepared_exe_sha256=sha(new),
                            changed_bytes=len(diff), allowed_intervals_only=True, combined_constructor_cases=tests,
                            normal_fourth_zero_black_empty_native_equivalence=True,
                            ultimate_pre_frame=52, ultimate_post_frame=53,
                            saved_record_all256bytes_preserved=True, save_pointer_preserved=True,
                            writes_only_display_objects_and_stack=True,
                            arm_types_exercised=[0, 1, 2, 255], allocation_failure_exercised=True,
                            stack_and_saved_registers_preserved=True))
    report = dict(passed=True, projects=records, candidate_cases=sum(x['combined_constructor_cases'] for x in records),
                  scope='Prepared executable only; native save base+overlay constructors run in sequence with allocator intercepted. No game/card write or actual UI draw.',
                  game_or_pointer_written=False, process_memory_accessed=False)
    (OUT / 'save_code_independent.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf8')
    print(json.dumps({'passed': True, 'candidate_cases': report['candidate_cases']}))


if __name__ == '__main__': main()
