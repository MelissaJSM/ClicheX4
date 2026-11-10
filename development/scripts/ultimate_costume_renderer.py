"""Prepare and CPU-check the bounded Ultimate costume display change.

This emits an EXE proposal only. It never writes a disc or emulator state.
The acquired armor bytes and all gameplay functions remain unchanged.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.psx_korean_font import Assembly

WORK = ROOT / 'work/ultimate_costume_swap_20261105/renderer'
START, END = 0x800257BC, 0x8002588C
DRAW_PART = 0x8002588C
PLAYER = 0x1418C8
ENGINE = 0x1721C0
STOP = 0x80008000
SOURCE_EXE_SHA256 = '0c31a48e68fb86e441dcc1b2b09007e62d2a2b9df206de0658cd1619d709e797'
SOURCE_FUNCTION_SHA256 = '45f8ec322f44bb3ca4675e068824bfd7fa3a2df8bd72922ab629b2597cc1fc2e'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def off(address):
    return address - 0x80010000 + 2048


def emit():
    """Same 208-byte function allocation; all stores are stack-local.

    Native caller 0x80023EA4 only invokes this function for X objects.
    Persisted engine ownership avoids a jacket flash while arrival restores
    the transient player armor byte. Main-bank 217..230 retain effect layers;
    their replacement body is authored independently in bank0.
    """
    a = Assembly()
    i, b = a.imm, a.branch
    i(9, 'sp', 'sp', -32)
    i(43, 's0', 'sp', 16)
    i(43, 's1', 'sp', 20)
    i(43, 'ra', 'sp', 24)
    a.move('s0', 'a0')
    i(15, 't0', 'zero', 0x8017)
    i(36, 'v0', 't0', 0x21F7)
    i(15, 's1', 'zero', 0x8014)
    i(36, 's1', 's1', 0x196F)
    b(4, 'v0', 'zero', 'ready')
    i(36, 'v1', 't0', 0x2207)
    i(36, 'v0', 'a0', 0x47)
    i(11, 's1', 'v1', 1)
    i(9, 'v0', 'v0', -217)
    i(11, 'v0', 'v0', 14)
    a.reg(0x25, 's1', 's1', 'v0')
    a.reg(0x23, 's1', 'zero', 's1')
    i(12, 's1', 's1', 15)
    a.label('ready')
    for bit, part, next_label in ((8, 3, 'head'), (1, 0, 'arm')):
        i(12, 'v0', 's1', bit)
        b(4, 'v0', 'zero', next_label)
        a.move('a0', 's0')
        i(9, 'a1', 'zero', part)
        a.jump(3, DRAW_PART)
        i(9, 'a2', 'zero', 0x7843)
        a.label(next_label)
    i(12, 'v0', 's1', 4)
    b(4, 'v0', 'zero', 'body')
    i(15, 'v0', 'zero', 0x8014)
    i(36, 'v0', 'v0', 0x1980)
    i(9, 'a2', 'zero', 0x7843)
    i(14, 'v0', 'v0', 2)
    i(11, 'v0', 'v0', 1)
    a.reg(0x21, 'a2', 'a2', 'v0')
    a.move('a0', 's0')
    a.jump(3, DRAW_PART)
    i(9, 'a1', 'zero', 2)
    a.label('body')
    i(12, 'v0', 's1', 2)
    b(4, 'v0', 'zero', 'done')
    a.move('a0', 's0')
    i(9, 'a1', 'zero', 1)
    a.jump(3, DRAW_PART)
    i(9, 'a2', 'zero', 0x7843)
    a.label('done')
    i(35, 'ra', 'sp', 24)
    i(35, 's1', 'sp', 20)
    i(35, 's0', 'sp', 16)
    a.emit(0x03E00008)  # jr ra; release stack in its delay slot
    i(9, 'sp', 'sp', 32)
    code = a.finish()
    if len(code) != END - START:
        raise ValueError('Display function exceeds original allocation')
    return code


def patch_executable(exe):
    if len(exe) != 1179648 or sha(exe) != SOURCE_EXE_SHA256:
        raise ValueError('Unsupported executable or already patched input')
    if sha(exe[off(START):off(END)]) != SOURCE_FUNCTION_SHA256:
        raise ValueError('Unsupported renderer')
    new = bytearray(exe)
    new[off(START):off(END)] = emit()
    if len(new) != len(exe) or new[:off(START)] != exe[:off(START)] or new[off(END):] != exe[off(END):]:
        raise ValueError('Change outside display function')
    return bytes(new)


def prepare():
    import capstone
    from scripts.c01_audio_build import read_disc, require
    from src.psx_disc import file_hash
    sources = {
        'ver_buki_riko': ('out/ver_buki_riko/black_monochrome_riko_20261105_v1/shibuki_riko.bin',
                         '852813890c3c9f8e0394026f8c243f6c323f1a9c0f4e1941eaa920b85bdecc4e'),
        'ver_rin_nana': ('out/ver_rin_nana/black_red_rin_20261105_v1/rin_nana.bin',
                        'aca6d7839ad1956ea837b07d1105a7609817cd30fd0e6ceffe13e6dd611ad6fe'),
    }
    config = json.loads((ROOT / 'config/shibuki_x_us.json').read_text('utf8'))
    original, _ = read_disc(ROOT / 'MegaMan X4.bin', ['SLUS_005.61'])
    original = original['SLUS_005.61']
    require(sha(original) == config['executable']['sha256'], 'Unexpected US executable')
    before = original[off(START):off(END)]
    replacement = emit()
    cs = capstone.Cs(capstone.CS_ARCH_MIPS,
                    capstone.CS_MODE_MIPS32 | capstone.CS_MODE_LITTLE_ENDIAN)
    WORK.mkdir(parents=True, exist_ok=True)
    records = []
    for project, (path, expected) in sources.items():
        require(file_hash(ROOT / path) == expected, 'Unsupported parent BIN')
        resources, _ = read_disc(ROOT / path, ['SLUS_005.61', 'PL02_U.ARC'])
        from scripts.prepare_riko_ui import entry
        palette = entry(resources['PL02_U.ARC'], 9)
        require(palette[32:64] == palette[64:96], 'Pre-capsule arm CLUT colors differ')
        exe = resources['SLUS_005.61']
        require(exe[off(START):off(END)] == before, 'Renderer already changed')
        caller = 0x80023E90
        require(exe[off(caller):off(caller + 28)] == original[off(caller):off(caller + 28)],
                'X-only caller changed')
        new = patch_executable(exe)
        require(len(new) == len(exe) and new[:off(START)] == exe[:off(START)] and
                new[off(END):] == exe[off(END):], 'Change outside display function')
        (WORK / (project + '.exe')).write_bytes(exe)
        output = WORK / (project + '.renderer.exe')
        output.write_bytes(new)
        records.append({'project': project, 'parent_bin': path, 'parent_bin_sha256': expected,
                        'source_exe_sha256': sha(exe), 'output_exe_sha256': sha(new),
                        'output': output.relative_to(ROOT).as_posix(),
                        'changed_bytes': sum(x != y for x, y in zip(exe, new)),
                        'outside_function_byte_identical': True})
    for name, data in [('original', before), ('proposal', replacement)]:
        (WORK / (name + '_function.txt')).write_text('\n'.join(
            f'{ins.address:08X} {ins.bytes.hex():8} {ins.mnemonic} {ins.op_str}'
            for ins in cs.disasm(data, START)) + '\n', 'utf8')
    report = {'kind': 'prepared_display_code_not_applied_to_bin', 'range': [hex(START), hex(END)],
              'bytes': len(replacement), 'original_sha256': sha(before),
              'replacement_sha256': sha(replacement), 'sources': records,
              'gameplay_state_written': False, 'requires_special_body_assets': list(range(217, 231)),
              'runtime_verified': False}
    (WORK / 'proposal.json').write_text(json.dumps(report, indent=2) + '\n', 'utf8')
    print(json.dumps(report))


def cpu():
    import unicorn as uc
    from unicorn import mips_const as m
    code = emit()
    before = (WORK / 'ver_rin_nana.exe').read_bytes()[off(START):off(END)]
    machine = uc.Uc(uc.UC_ARCH_MIPS, uc.UC_MODE_MIPS32 | uc.UC_MODE_LITTLE_ENDIAN)
    machine.mem_map(0, 0x200000)
    machine.mem_write(DRAW_PART & 0x1FFFFFFF, b'\x08\x00\xe0\x03\x00\x00\x00\x00')
    calls, writes = [], []
    def on_code(u, address, size, _):
        if address == DRAW_PART:
            calls.append([u.reg_read(m.UC_MIPS_REG_A0), u.reg_read(m.UC_MIPS_REG_A1),
                          u.reg_read(m.UC_MIPS_REG_A2)])
            # A valid callee may clobber every caller-saved register.
            for name in ('V0', 'V1', 'A0', 'A1', 'A2', 'A3', 'T0', 'T1', 'T2', 'T3',
                         'T4', 'T5', 'T6', 'T7', 'T8', 'T9'):
                u.reg_write(getattr(m, 'UC_MIPS_REG_' + name), 0xBADBAD00)
            u.reg_write(m.UC_MIPS_REG_PC, u.reg_read(m.UC_MIPS_REG_RA))
    def on_write(u, access, address, size, value, _):
        writes.append((address, size))
        if not 0x1FEFE0 <= address & 0x1FFFFFFF <= 0x1FEFFC:
            raise ValueError('Unexpected non-stack store: ' + hex(address))
    machine.hook_add(uc.UC_HOOK_CODE, on_code)
    machine.hook_add(uc.UC_HOOK_MEM_WRITE, on_write)
    def run(data, special, owned, transient, arm_type, frame):
        calls.clear(); writes.clear()
        machine.mem_write(START & 0x1FFFFFFF, data)
        machine.ctl_remove_cache(START, END)
        player = bytearray(228); player[0xA7] = transient; player[0xB8] = arm_type; player[0x47] = frame
        engine = bytearray(100); engine[0x37] = special; engine[0x47] = owned
        machine.mem_write(PLAYER, bytes(player)); machine.mem_write(ENGINE, bytes(engine))
        for register, value in ((m.UC_MIPS_REG_A0, PLAYER | 0x80000000), (m.UC_MIPS_REG_SP, 0x801FF000),
                                (m.UC_MIPS_REG_S0, 0x12345678), (m.UC_MIPS_REG_S1, 0x76543210),
                                (m.UC_MIPS_REG_RA, STOP)):
            machine.reg_write(register, value)
        machine.emu_start(START, STOP, count=1500)
        if machine.reg_read(m.UC_MIPS_REG_PC) != STOP:
            raise ValueError('Function did not return')
        if [machine.reg_read(r) for r in (m.UC_MIPS_REG_SP, m.UC_MIPS_REG_S0, m.UC_MIPS_REG_S1)] != [0x801FF000, 0x12345678, 0x76543210]:
            raise ValueError('Callee-saved register or stack corruption')
        if machine.mem_read(PLAYER, len(player)) != player or machine.mem_read(ENGINE, len(engine)) != engine:
            raise ValueError('Gameplay state changed')
        return list(calls)
    checks = 0
    # Every native armor-mask and arm-type byte, with deliberately disruptive callees.
    for armor in range(16):
        for arm_type in range(256):
            expected = run(before, 0, armor, armor, arm_type, 0)
            actual = run(code, 0, armor, armor, arm_type, 0)
            if actual != expected:
                raise ValueError('Native Fourth/base display changed')
            checks += 1
    for owned in (0, 15):
        for transient in (0, 15):
            for arm_type in (0, 1, 2):
                for frame in range(256):
                    mask = 15 if owned == 0 or 217 <= frame <= 230 else 0
                    expected = [[PLAYER | 0x80000000, part, 0x7844 if part == 2 and arm_type == 2 else 0x7843]
                                for bit, part in ((8, 3), (1, 0), (4, 2), (2, 1)) if mask & bit]
                    if run(code, 1, owned, transient, arm_type, frame) != expected:
                        raise ValueError('Wrong Ultimate display selection')
                    checks += 1
    # Exercise the same input guards used to prepare the proposal.
    source_exe = (WORK / 'ver_rin_nana.exe').read_bytes()
    mutations = []
    for offset in (0, 12, 64, 128, 204):
        bad = bytearray(source_exe); bad[off(START) + offset] ^= 1
        mutations.append(('renderer_offset_' + str(offset), bytes(bad)))
    outside = bytearray(source_exe); outside[off(0x80023E9C)] ^= 1
    mutations.extend([('caller_changed', bytes(outside)), ('truncated', source_exe[:-1]),
                      ('already_patched', patch_executable(source_exe))])
    rejected = []
    for label, candidate in mutations:
        try:
            patch_executable(candidate)
        except ValueError:
            rejected.append(label)
        else:
            raise ValueError('Mutation accepted: ' + label)
    result = {'unicorn_version': uc.__version__, 'cases': checks, 'native_equivalence_cases': 4096,
              'ultimate_frame_state_cases': 3072, 'stores_only_in_stack': True,
              'player_and_engine_preserved': True, 'callee_saved_registers_preserved': True,
              'caller_saved_register_clobber_test': True, 'rejected_inputs': rejected,
              'runtime_verified': False, 'replacement_sha256': sha(code)}
    (WORK / 'cpu_verification.json').write_text(json.dumps(result, indent=2) + '\n', 'utf8')
    print(json.dumps(result))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=('prepare', 'cpu'))
    args = parser.parse_args()
    {'prepare': prepare, 'cpu': cpu}[args.action]()
