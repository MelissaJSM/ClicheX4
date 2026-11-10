"""원본 MIPS 캡슐 소유권과 팔레트 경로를 격리 메모리에서 검사한다."""
import hashlib
import json
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from scripts.discover_inputs import DiscReader, psx_arc
from capstone import Cs, CS_ARCH_MIPS, CS_MODE_MIPS32, CS_MODE_LITTLE_ENDIAN
from unicorn import Uc, UC_ARCH_MIPS, UC_MODE_MIPS32, UC_MODE_LITTLE_ENDIAN, UC_HOOK_CODE, UC_HOOK_MEM_WRITE
from unicorn import mips_const as m

OUT = Path(__file__).resolve().parent
PLAYER = 0x1418C8
ENGINE = 0x1721C0
PAL_SOURCE = 0x4000
PAL_DEST = 0x9000
RETURN = 0x80008000


def sha(b):
    return hashlib.sha256(b).hexdigest()


def load_exe(path):
    with path.open('rb') as f:
        d = DiscReader(f, path.stat().st_size)
        r = next(x for x in d.inspect()['files'] if x['name'] == 'SLUS_005.61;1')
        return d.read(r['lba'], r['size'])


def code(exe, start, end):
    base = struct.unpack_from('<I', exe, 0x18)[0]
    return exe[2048 + start - base:2048 + end - base]


def cpu(exe):
    u = Uc(UC_ARCH_MIPS, UC_MODE_MIPS32 | UC_MODE_LITTLE_ENDIAN)
    u.mem_map(0, 0x200000)
    u.mem_map(0x1F800000, 4096)
    base, size = struct.unpack_from('<II', exe, 0x18)
    u.mem_write(base & 0x1FFFFFFF, exe[2048:2048 + size])
    u.reg_write(m.UC_MIPS_REG_SP, 0x801FF000)
    u.reg_write(m.UC_MIPS_REG_RA, RETURN)
    return u


def finish(u, entry, exit_pc=RETURN):
    def stop(mu, pc, size, _):
        if pc == exit_pc:
            mu.emu_stop()
    handle = u.hook_add(UC_HOOK_CODE, stop)
    u.emu_start(entry, 0, count=200000)
    u.hook_del(handle)
    assert u.reg_read(m.UC_MIPS_REG_PC) == exit_pc


def capsule(exe, ultimate, part, event):
    u = cpu(exe)
    obj = 0xA000
    u.reg_write(m.UC_MIPS_REG_S0, 0x80000000 + obj)
    u.reg_write(m.UC_MIPS_REG_S1, 0x80000000 + PLAYER)
    u.mem_write(obj + 2, bytes([part]))
    u.mem_write(obj + 0x45, bytes([event]))
    for at in (PLAYER + 0xA7, PLAYER + 0xB8, ENGINE + 0x47, ENGINE + 0x48):
        u.mem_write(at, b'\0')
    u.mem_write(ENGINE + 0x37, bytes([ultimate]))
    writes = []
    def trace(mu, access, at, size, value, _):
        p = at & 0x1FFFFFFF
        if p in (obj + 0x45, PLAYER + 0xA7, PLAYER + 0xB8, ENGINE + 0x47, ENGINE + 0x48):
            writes.append({'pc': hex(mu.reg_read(m.UC_MIPS_REG_PC)), 'address': hex(p | 0x80000000), 'value': value, 'size': size})
    u.hook_add(UC_HOOK_MEM_WRITE, trace)
    # The actual game's event/ownership branch. Animation stepping and drawing
    # are outside this deliberately narrow isolated native execution.
    finish(u, 0x800C7070, 0x800C7140)
    result = dict(ultimate=ultimate, part=part, animation_event=event,
                  player_armor=u.mem_read(PLAYER + 0xA7, 1)[0],
                  player_arm_type=u.mem_read(PLAYER + 0xB8, 1)[0],
                  engine_armor=u.mem_read(ENGINE + 0x47, 1)[0],
                  engine_arm_type=u.mem_read(ENGINE + 0x48, 1)[0], writes=writes)
    expected_armor = (15 if ultimate else [1, 2, 4, 4, 8][part]) if event else 0
    expected_arm = (2 if ultimate or part == 3 else 1 if part == 2 else 0) if event else 0
    assert result['player_armor'] == result['engine_armor'] == expected_armor
    assert result['player_arm_type'] == result['engine_arm_type'] == expected_arm
    assert not event or writes[-1]['address'] == '0x80172207'
    return result


def palette(exe, source, weapon=None, override=None):
    assert (weapon is None) != (override is None)
    u = cpu(exe)
    u.mem_write(PLAYER, bytes(0xE4))
    u.mem_write(PAL_SOURCE, source)
    u.mem_write(0x1F800024, struct.pack('<II', 0x80000000 + PAL_SOURCE, 0x80000000 + PAL_DEST))
    sentinel = bytes([0xA5]) * 0x400
    u.mem_write(PAL_DEST, sentinel)
    u.reg_write(m.UC_MIPS_REG_A0, 0x80000000 + PLAYER)
    expected = bytearray(sentinel)
    if override is not None:
        u.reg_write(m.UC_MIPS_REG_A1, override)
        start = override * 32
        expected[:32] = source[start:start + 32]
        expected[0x260:0x2A0] = source[start + 32:start + 96]
        function = 0x800362F8
    else:
        u.mem_write(PLAYER + 0x93, bytes([weapon]))
        start = 0 if not weapon else 96 + (weapon - 1) * 128
        if weapon:
            expected[:64] = source[start:start + 64]
            expected[0x260:0x2A0] = source[start + 64:start + 128]
        else:
            expected[:32] = source[:32]
            expected[0x260:0x2A0] = source[32:96]
        function = 0x800361F8
    assert len(expected) == 0x400
    finish(u, function)
    actual = bytes(u.mem_read(PAL_DEST, 0x400))
    assert actual == bytes(expected)
    base, armor, arm = actual[:32], actual[0x260:0x280], actual[0x280:0x2A0]
    return dict(weapon=weapon, override=override, source_byte_offset=start,
                native_function=hex(function), exact_expected_palette_copy=True,
                base_row_sha256=sha(base), armor_row_sha256=sha(armor), arm_type2_row_sha256=sha(arm),
                armor_equals_arm_type2=armor == arm,
                base_vs_armor_changed_indices=[i for i in range(16) if base[i*2:i*2+2] != armor[i*2:i*2+2]],
                base_words=list(struct.unpack('<16H', base)),
                armor_words=list(struct.unpack('<16H', armor)),
                arm_type2_words=list(struct.unpack('<16H', arm)))


def main():
    original = load_exe(ROOT / 'MegaMan X4.bin')
    ranges = {'capsule_grant_event': (0x800C7070, 0x800C7140),
              'player_palette_copy_reset_set': (0x800361B0, 0x800363B8),
              'player_beam_in': (0x80031410, 0x80031550),
              'generic_base_draw': (0x80024334, 0x800248EC),
              'armor_draw': (0x800257BC, 0x8002588C),
              'player_draw_caller': (0x80023DF0, 0x80023EC0)}
    md = Cs(CS_ARCH_MIPS, CS_MODE_MIPS32 | CS_MODE_LITTLE_ENDIAN)
    text = []
    for name, (lo, hi) in ranges.items():
        text.append('\n' + name)
        text.extend(f'{i.address:08x}: {i.mnemonic} {i.op_str}' for i in md.disasm(code(original, lo, hi), lo))
    (OUT / 'ownership_palette_native_disassembly.txt').write_text('\n'.join(text), encoding='utf8')
    reports = {}
    for project in ('ver_buki_riko', 'ver_rin_nana'):
        before = json.loads((OUT / project / 'before.json').read_text('utf8'))
        exe = load_exe(ROOT / before['source_bin'])
        matches = {name: {'unchanged_original_code': code(exe, *r) == code(original, *r),
                          'sha256': sha(code(exe, *r)), 'start': hex(r[0]), 'end': hex(r[1])}
                   for name, r in ranges.items()}
        assert all(x['unchanged_original_code'] for x in matches.values())
        arc = (OUT / project / 'source_PL02_U.ARC').read_bytes()
        row = next(e for e in psx_arc(arc) if int(e['type'], 16) == 9)
        pal = arc[row['offset']:row['offset'] + row['size']]
        checks = [palette(exe, pal, weapon=w) for w in range(9)]
        checks += [palette(exe, pal, override=n) for n in (0x23, 0x32, 0x49)]
        reports[project] = dict(source_sha256=before['source_sha256'], exe_sha256=sha(exe),
                                original_code_ranges=matches, palette_checks=checks,
                                ownership_checks=[capsule(exe, u, p, e) for u, p, e in [(1, 0, 0), (1, 0, 1)] + [(0, p, 1) for p in range(5)]])
    report = dict(passed=True, native_cpu_palette_cases=24, native_cpu_ownership_cases=14,
                  projects=reports,
                  scope='Isolated unmodified native event branch and palette functions; not emulator gameplay or capsule end-to-end test.',
                  limitations=['Actual VRAM upload is not executed by this audit.', 'Full capsule animation stepping is outside event-branch execution.', 'No new costume renderer is exercised yet.'],
                  game_files_written=False, user_states_written=False, process_memory_accessed=False)
    (OUT / 'native_contracts.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf8')
    print(json.dumps({'passed': True, 'palette_cases': 24, 'ownership_cases': 14}))


if __name__ == '__main__':
    main()
