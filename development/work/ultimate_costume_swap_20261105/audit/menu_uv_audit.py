"""Actual menu background primitives and shared LOAD atlas ownership audit."""
import hashlib
import json
import struct
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from scripts.discover_inputs import DiscReader
from src.psx_ui_atlas import aliased_composition
from capstone import Cs, CS_ARCH_MIPS, CS_MODE_MIPS32, CS_MODE_LITTLE_ENDIAN
from native_contracts import cpu, finish, code

OUT = Path(__file__).resolve().parent


def sha(b):
    return hashlib.sha256(b).hexdigest()


def background(exe, buffer):
    u = cpu(exe)
    u.mem_write(0x1F800000, struct.pack('<I', buffer))
    u.mem_write(0x142F80, struct.pack('<I', 0x801B0000))
    u.mem_write(0x1B0000, bytes(0x1000))
    finish(u, 0x80016124)
    start = 0x139268 + buffer * 340
    sprites = []
    for i in range(17):
        p = bytes(u.mem_read(start + i * 20, 20))
        x, y, tu, tv, clut, w, h = struct.unpack_from('<hhBBHHH', p, 8)
        assert p[7] == 0x65 and tv == 208 and h == 48
        assert (tu, w) in ((0, 112), (112, 96), (0, 16))
        assert tu + w <= 208
        sprites.append(dict(index=i, screen=[x, y], uv=[tu, tv], size=[w, h], clut=clut))
    return dict(buffer=buffer, native_function='0x80016124', primitive_count=17,
                primitive_start=hex(start | 0x80000000), sprites=sprites,
                texture_x_inclusive=[0, 207], texture_y_inclusive=[208, 255],
                function_and_GPU_packet_SDK_executed_without_mocks=True)


def main():
    result = {}
    for project in ('ver_buki_riko', 'ver_rin_nana'):
        before = json.loads((OUT / project / 'before.json').read_text('utf8'))
        p = ROOT / before['source_bin']
        with p.open('rb') as f:
            d = DiscReader(f, p.stat().st_size)
            records = {r['name'].split(';')[0]: r for r in d.inspect()['files']}
            assets = {n: d.read(records[n]['lba'], records[n]['size']) for n in ('SLUS_005.61', 'MOJIPAT.ARC')}
        exe, menu = assets['SLUS_005.61'], assets['MOJIPAT.ARC']
        assert sha(exe) == before['resources']['SLUS_005.61']['sha256']
        bg = [background(exe, n) for n in (0, 1)]
        direct = set()
        tables = []
        for n in range(9):
            x, y, tile, w, h, clut = struct.unpack_from('<hhBBBB', exe, 0xDED04 + n * 8)
            starts = list(exe[0xDED04 + 72:0xDED04 + 84]) if n == 6 else [tile]
            touches = sorted({s + dy * 16 + dx for s in starts for dy in range(h) for dx in range(w)})
            direct.update(touches)
            tables.append(dict(row=n, table_address=hex(0x800EE504 + n * 8), screen=[x, y],
                               tiles=touches, clut=clut))
        owners = {}
        for n in range(aliased_composition(menu, 2, 0)['bank_frame_count']):
            for q in aliased_composition(menu, 2, n)['parts']:
                tile = q['page'] * 256 + q['tile']
                owners.setdefault(tile, set()).add(n)
        right = [y * 16 + x for y in (13, 14, 15) for x in (13, 14, 15)]
        assert not set(right) & direct
        right_owners = {str(t): sorted(owners.get(t, set())) for t in right}
        other_banks = {}
        for bank, tile_base in ((0, 0x1F00), (2, 0x1E00), (3, 0x1DE0)):
            count = aliased_composition(menu, bank, 0)['bank_frame_count']
            tiles = sorted({p['page'] * 256 + p['tile'] for n in range(count) for p in aliased_composition(menu, bank, n)['parts']})
            other_banks[str(bank)] = dict(frame_count=count, constructor_tile_base=hex(tile_base),
                                          relative_tile_min=min(tiles), relative_tile_max=max(tiles),
                                          absolute_tile_min=hex(tile_base + min(tiles)), absolute_tile_max=hex(tile_base + max(tiles)))
        # All bottom right candidate tiles fall in 0x1E00 + 221..255. The
        # separate menu font bank and weapon icon bank cannot reach them.
        for bank in ('0', '3'):
            b = other_banks[bank]
            lo, hi = int(b['absolute_tile_min'], 16), int(b['absolute_tile_max'], 16)
            assert not any(lo <= 0x1E00 + t <= hi for t in right)
        result[project] = dict(source_bin=before['source_bin'], source_sha256=before['source_sha256'],
                               exe_sha256=sha(exe), menu_sha256=sha(menu), native_background=bg,
                               direct_loading_rectangles=tables, direct_loading_bottom_right_intersection=[],
                               bottom_right_tiles=right, bottom_right_save_frame_owners=right_owners,
                               other_menu_bank_ranges=other_banks,
                               required_protection='Preserve or repack every existing save-frame owner; absent background ownership does not mean a tile is free.')
    exe = assets['SLUS_005.61']
    md = Cs(CS_ARCH_MIPS, CS_MODE_MIPS32 | CS_MODE_LITTLE_ENDIAN)
    text = '\n'.join(f'{i.address:08x}: {i.mnemonic} {i.op_str}' for i in md.disasm(code(exe, 0x80016124, 0x80016334), 0x80016124))
    (OUT / 'menu_background_native_disassembly.txt').write_text(text, encoding='utf8')
    report = dict(passed=True, projects=result, native_background_runs=4,
                  game_or_pointer_written=False, process_memory_accessed=False,
                  scope='Actual background packet generation and known direct-loading/menu-composition references; not emulator rendering.')
    (OUT / 'menu_uv_audit.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf8')
    print(json.dumps({'passed': True, 'native_background_runs': 4,
                      'owners': {p: r['bottom_right_save_frame_owners'] for p, r in result.items()}}))


if __name__ == '__main__':
    main()
