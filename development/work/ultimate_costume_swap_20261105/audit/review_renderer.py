"""Prepared EXE bytes, independently interpreted and executed; no disk writes."""
import hashlib
import json
import struct
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from capstone import Cs, CS_ARCH_MIPS, CS_MODE_MIPS32, CS_MODE_LITTLE_ENDIAN
from unicorn import Uc, UC_ARCH_MIPS, UC_MODE_MIPS32, UC_MODE_LITTLE_ENDIAN, UC_HOOK_CODE, UC_HOOK_MEM_WRITE
from unicorn import mips_const as r

OUT = Path(__file__).resolve().parent
PREP = OUT.parent / 'renderer'
START, END = 0x800257BC, 0x8002588C
PLAYER, ENGINE = 0x1418C8, 0x1721C0
STOP = 0x80008000


def sha(b):
    return hashlib.sha256(b).hexdigest()


def sl(exe, lo, hi):
    base = struct.unpack_from('<I', exe, 0x18)[0]
    return exe[2048 + lo - base:2048 + hi - base]


def main():
    proposal_bytes = (PREP / 'proposal.json').read_bytes()
    proposal = json.loads(proposal_bytes)
    records = []
    for row in proposal['sources']:
        old = (PREP / (row['project'] + '.exe')).read_bytes()
        new = (ROOT / row['output']).read_bytes()
        assert sha(old) == row['source_exe_sha256'] and sha(new) == row['output_exe_sha256']
        assert len(old) == len(new)
        lo = START - 0x80010000 + 2048
        hi = END - 0x80010000 + 2048
        assert old[:lo] == new[:lo] and old[hi:] == new[hi:]
        assert sha(new[lo:hi]) == proposal['replacement_sha256']
        records.append({'project': row['project'], 'before_sha256': sha(old), 'after_sha256': sha(new),
                        'changed_bytes': sum(a != b for a, b in zip(old, new)), 'outside_208bytes_identical': True})
    md = Cs(CS_ARCH_MIPS, CS_MODE_MIPS32 | CS_MODE_LITTLE_ENDIAN)
    instructions = list(md.disasm(sl(new, START, END), START))
    stores = [(hex(x.address), x.mnemonic, x.op_str) for x in instructions if x.mnemonic.startswith('s') and x.mnemonic in ('sb', 'sh', 'sw', 'swl', 'swr', 'sc')]
    assert len(instructions) == 52 and [x[2] for x in stores] == ['$s0, 0x10($sp)', '$s1, 0x14($sp)', '$ra, 0x18($sp)']
    branch_callers = []
    target = 0x0C000000 | ((START >> 2) & 0x3FFFFFF)
    for i in range(2048, len(old), 4):
        if struct.unpack_from('<I', old, i)[0] == target:
            branch_callers.append(hex(0x80010000 + i - 2048))
    assert branch_callers == ['0x80023ea4']
    # Original caller's visible-player and X-character predicates remain exact.
    assert sl(old, 0x80023E70, 0x80023EAC) == sl(new, 0x80023E70, 0x80023EAC)

    mu = Uc(UC_ARCH_MIPS, UC_MODE_MIPS32 | UC_MODE_LITTLE_ENDIAN)
    mu.mem_map(0, 0x200000)
    trace, writes = [], []
    def on_code(u, pc, size, _):
        if pc == END:
            trace.append(tuple(u.reg_read(x) for x in (r.UC_MIPS_REG_A0, r.UC_MIPS_REG_A1, r.UC_MIPS_REG_A2)))
            for name in ('AT', 'V0', 'V1', 'A0', 'A1', 'A2', 'A3', 'T0', 'T1', 'T2', 'T3', 'T4', 'T5', 'T6', 'T7', 'T8', 'T9'):
                u.reg_write(getattr(r, 'UC_MIPS_REG_' + name), 0x87654321)
            u.reg_write(r.UC_MIPS_REG_PC, u.reg_read(r.UC_MIPS_REG_RA))
    def on_write(u, access, at, size, value, _):
        at &= 0x1FFFFFFF
        assert at in (0x1FEFF0, 0x1FEFF4, 0x1FEFF8) and size == 4
        writes.append(at)
    mu.hook_add(UC_HOOK_CODE, on_code)
    mu.hook_add(UC_HOOK_MEM_WRITE, on_write)

    current = None
    def run(blob, ultimate, owner, temporary, armtype, frame):
        nonlocal current
        if blob != current:
            mu.mem_write(START & 0x1FFFFFFF, blob)
            mu.ctl_remove_cache(START, END)
            current = blob
        p = bytearray((i * 37 + 11) % 256 for i in range(228))
        p[2] = 0
        p[0xA7], p[0xB8], p[0x47] = temporary, armtype, frame
        e = bytearray((i * 19 + 59) % 256 for i in range(100))
        e[0x37], e[0x47] = ultimate, owner
        mu.mem_write(PLAYER, bytes(p)); mu.mem_write(ENGINE, bytes(e))
        mu.reg_write(r.UC_MIPS_REG_A0, PLAYER | 0x80000000)
        mu.reg_write(r.UC_MIPS_REG_SP, 0x801FF000)
        mu.reg_write(r.UC_MIPS_REG_RA, STOP)
        for n in range(8):
            mu.reg_write(getattr(r, 'UC_MIPS_REG_S' + str(n)), 0x12345670 + n)
        trace.clear(); writes.clear()
        mu.emu_start(START, STOP, count=1000)
        assert mu.reg_read(r.UC_MIPS_REG_PC) == STOP
        assert mu.reg_read(r.UC_MIPS_REG_SP) == 0x801FF000
        assert bytes(mu.mem_read(PLAYER, 228)) == bytes(p) and bytes(mu.mem_read(ENGINE, 100)) == bytes(e)
        assert all(mu.reg_read(getattr(r, 'UC_MIPS_REG_S' + str(n))) == 0x12345670 + n for n in range(8))
        assert len(writes) == 3
        return tuple(trace)

    oldcode, newcode = sl(old, START, END), sl(new, START, END)
    native = {}
    for mask in range(16):
        for arm in range(256):
            native[mask, arm] = run(oldcode, 0, mask, mask, arm, 0)
    count = 0
    for mask in range(16):
        for arm in range(256):
            assert run(newcode, 0, mask, mask, arm, 0) == native[mask, arm]
            count += 1
    ultimate_cases = 0
    for ultimate in (1, 255):
        for owner in range(16):
            for temporary in (0, 15):
                for arm in (0, 1, 2):
                    for frame in range(256):
                        expected_mask = 15 if owner == 0 or frame in range(217, 231) else 0
                        assert run(newcode, ultimate, owner, temporary, arm, frame) == native[expected_mask, arm]
                        ultimate_cases += 1
    assert (PREP / 'proposal.json').read_bytes() == proposal_bytes
    report = dict(passed=True, prepared_files=records, exact_prepared_code_sha256=sha(newcode),
                  independent_of_emitter=True, instructions=52, stores=stores,
                  sole_direct_call_site=branch_callers,
                  original_reference_cases=len(native), native_regression_cases=count,
                  ultimate_cases=ultimate_cases, total_candidate_cases=count + ultimate_cases,
                  old_mask_reference_trace_used=True, caller_saved_registers_clobbered=True,
                  player_engine_all_bytes_preserved=True, all_eight_saved_registers_and_stack_preserved=True,
                  limitations=['Actual armor drawing is intercepted to record its ABI arguments; this is not a GPU/render correctness test.',
                               'No prepared resource/art changes are validated by this renderer-only test.',
                               'Approval to activate a new EXE display method is not inferred from CPU test success.'],
                  game_or_pointer_written=False, process_memory_accessed=False)
    (OUT / 'renderer_independent.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf8')
    print(json.dumps({'passed': True, 'candidate_cases': count + ultimate_cases, 'reference_cases': len(native)}))


if __name__ == '__main__':
    main()
