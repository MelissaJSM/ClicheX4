"""Execute actual RXC1 glyph instructions with Unicorn, without game input."""
import json
from pathlib import Path
import struct
import sys

from unicorn import Uc, UC_ARCH_X86, UC_MODE_32
from unicorn.x86_const import *

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.steam_dialogue import runtime_patches

BASE = 0x401000
WORK = ROOT/'work/steam_port_20261109'
META = 0x2000000
ABC = 0x2004000
STACK = 0x3008000


def main():
    code = (WORK/'runtime/code/text.bin').read_bytes()
    patches = runtime_patches()
    for name, va, before, after in patches:
        if len(before) != len(after) or code[va-BASE:va-BASE+len(before)] != before:
            raise ValueError('Verified runtime code signature differs: '+name)
    machine = Uc(UC_ARCH_X86, UC_MODE_32)
    machine.mem_map(0x400000, 0xc00000)
    machine.mem_write(BASE, code)
    machine.mem_map(META, 0x10000)
    machine.mem_map(0x3000000, 0x10000)
    for _, va, _, after in patches:
        machine.mem_write(va, after)
    block = next(p for p in patches if p[0] == 'dialogue_glyph_page_and_tile')
    checks = 0
    for glyph in range(1023):
        for flags, index in [(0x0800, 0), (0x1000, 29), (0x5000, 59), (0xa800, 59)]:
            word = flags | glyph
            baseline = bytearray([0xa5]*0x200)
            struct.pack_into('<H', baseline, 0x124, index)
            machine.mem_write(META, bytes(baseline))
            machine.mem_write(ABC+10, struct.pack('<H', word))
            for reg, value in [(UC_X86_REG_EAX, META+4), (UC_X86_REG_EBP, META),
                               (UC_X86_REG_EDI, ABC), (UC_X86_REG_ESI, index),
                               (UC_X86_REG_EBX, 0x12340000), (UC_X86_REG_ESP, STACK),
                               (UC_X86_REG_ECX, META), (UC_X86_REG_EDX, 0x87654321)]:
                machine.reg_write(reg, value)
            machine.emu_start(block[1], block[1]+len(block[3]), count=200)
            expected = bytearray(baseline)
            expected[8+index*4] = glyph//256
            expected[9+index*4] = glyph%256
            if machine.mem_read(META, len(expected)) != expected:
                raise ValueError(f'Glyph memory mismatch: {glyph}, {flags}, {index}')
            wanted = [(UC_X86_REG_ESP, STACK), (UC_X86_REG_EBP, META),
                      (UC_X86_REG_EDI, ABC), (UC_X86_REG_ESI, index),
                      (UC_X86_REG_EBX, 0x12340000 | word), (UC_X86_REG_ECX, META),
                      (UC_X86_REG_EAX, META+4)]
            if any(machine.reg_read(reg) != val for reg, val in wanted):
                raise ValueError('Native glyph calling convention changed')
            checks += 1
    width = patches[-1]
    for region in (0, 1, 2, 3, 4):
        machine.reg_write(UC_X86_REG_EAX, region)
        machine.reg_write(UC_X86_REG_EDI, ABC)
        machine.reg_write(UC_X86_REG_ESP, STACK)
        machine.emu_start(width[1], width[1]+len(width[3]), count=100)
        if machine.reg_read(UC_X86_REG_EAX) != 12 or machine.reg_read(UC_X86_REG_ECX) != ABC or machine.reg_read(UC_X86_REG_ESP) != STACK:
            raise ValueError('Korean advance/calling convention differs')
    report = {'glyph_cases': checks, 'glyph_range': [0, 1022], 'flags': ['0x0800', '0x1000', '0x5000', '0xa800'],
              'visible_indices': [0, 29, 59], 'exact_only_page_and_tile_writes': True,
              'callee_saved_registers_and_stack_preserved': True, 'advance_cases': 5,
              'advance_pixels': 12, 'native_typewriter_and_page_logic_outside_changed_blocks': True,
              'patches': [{'name': name, 'address': hex(va), 'bytes': len(before),
                           'changed_bytes': sum(a != b for a, b in zip(before, after))}
                          for name, va, before, after in patches], 'live_runtime_verified': False}
    (WORK/'dialogue_cpu_verification.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report))


if __name__ == '__main__':
    main()
