"""Execute native menu subtype-2 initialization and frame-table selection."""
import argparse
import hashlib
import json
import struct
from pathlib import Path
from native_contracts import ROOT, cpu, finish
from unicorn import mips_const as r
from src.psx_ui_atlas import aliased_composition


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--menu', type=Path, required=True)
    parser.add_argument('--project', choices=('ver_buki_riko', 'ver_rin_nana'), required=True)
    args = parser.parse_args()
    menu = args.menu.read_bytes()
    count = aliased_composition(menu, 2, 0)['bank_frame_count']
    assert count == 54, 'The prepared frame-53 bank must have 54 frames'
    exe = (ROOT / 'work/ultimate_costume_swap_20261105/renderer' / (args.project + '.exe')).read_bytes()
    menu_address, obj = 0x1F3000, 0xA000
    bank = struct.unpack_from('<I', menu, 8)[0]
    rows = []
    for frame in (0, 43, 44, 51, 52, 53):
        u = cpu(exe)
        u.mem_write(menu_address, menu)
        initial = bytearray(96)
        initial[1], initial[2], initial[0x47] = 0x2A, 2, frame
        struct.pack_into('<hh', initial, 8, 0, 208)
        struct.pack_into('<hh', initial, 12, 0, 136)
        u.mem_write(obj, bytes(initial))
        u.reg_write(r.UC_MIPS_REG_A0, 0x80000000 + obj)
        finish(u, 0x800CFEE0)
        initialized = bytes(u.mem_read(obj, 96))
        expected_pointer = 0x80000000 + menu_address + bank
        assert struct.unpack_from('<I', initialized, 0x3C)[0] == expected_pointer
        assert struct.unpack_from('<H', initialized, 0x40)[0] == 0x1E00
        assert initialized[0x47] == frame
        u.reg_write(r.UC_MIPS_REG_A0, 0x80000000 + obj)
        finish(u, 0x80024334, 0x80024414)
        sp = u.reg_read(r.UC_MIPS_REG_SP) & 0x1FFFFFFF
        part_count = struct.unpack('<I', u.mem_read(sp + 0x40, 4))[0]
        selected = struct.unpack('<I', u.mem_read(sp + 0x10, 4))[0]
        header = struct.unpack_from('<I', menu, bank + frame * 4)[0]
        assert part_count == (header & 0xFFFF)
        assert selected == expected_pointer + (header >> 16) * 4
        parts = aliased_composition(menu, 2, frame)['parts']
        assert len(parts) == part_count
        assert selected >= expected_pointer + count * 4
        assert selected + part_count * 4 <= 0x80000000 + menu_address + struct.unpack_from('<I', menu, 12)[0]
        rows.append({'frame': frame, 'native_selected_part_count': part_count,
                     'native_selected_parts_pointer': hex(selected), 'native_frame_unchanged': True})
    out = Path(__file__).resolve().parent / ('menu_frame53_' + args.project + '.json')
    report = dict(passed=True, project=args.project, menu=str(args.menu),
                  menu_sha256=hashlib.sha256(menu).hexdigest(),
                  source_exe_sha256=hashlib.sha256(exe).hexdigest(),
                  frame_count=54, actual_native_init='0x800CFEE0', actual_native_draw_header='0x80024334..0x80024414',
                  cases=rows, fixed_53_frame_rejection_observed=False,
                  scope='Native subtype-2 initialization and composition header selection, stopped before GPU primitive emission.',
                  game_or_state_written=False, process_memory_accessed=False)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf8')
    print(json.dumps({'passed': True, 'menu_sha256': report['menu_sha256'], 'output': str(out)}))


if __name__ == '__main__':
    main()
