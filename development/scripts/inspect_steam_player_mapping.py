"""Compare original PS1 player banks to extracted Steam PAT/COF/TEX, read-only."""
import json
from pathlib import Path
import struct
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.c01_audio_build import read_disc
from scripts.prepare_riko_ui import entry
from src.psx_player import bank_offsets, graphics_bank, decode_stream, indexed_atlas

WORK = ROOT / 'work/steam_port_research_20261109'


def u32(raw, pos):
    return struct.unpack_from('<I', raw, pos)[0]


def main():
    inventory = json.loads((WORK/'inventory.json').read_text(encoding='utf-8'))
    arcs, _ = read_disc(Path(inventory['ps1_original']['path']), ['PL00_U.ARC', 'PL01_U.ARC', 'PL02_U.ARC'])
    report = {'scope': 'original asset correspondence, not modified Steam installation/runtime', 'players': {}}
    for player in ('pl00', 'pl01', 'pl02'):
        source = arcs[player.upper() + '_U.ARC']
        ps_parts, ps_graphics = entry(source, 3), entry(source, 2)
        files = list((WORK/'extracted'/f'{player}_eng.arc').rglob('*'))
        pat = next(f.read_bytes() for f in files if f.is_file() and f.name.startswith(player.upper()+'.'))
        bank_count = u32(pat, 8)
        cursor, counts = 12, []
        for _ in range(bank_count):
            n = u32(pat, cursor)
            cursor += 4
            assert 0 < n <= 4096
            counts.append(struct.unpack_from('<'+'I'*n, pat, cursor))
            cursor += 4*n
        tables_start = cursor
        quads_start = tables_start + sum(len(c)*4 for c in counts)
        assert quads_start + sum(sum(c)*4 for c in counts) == len(pat)
        ps_offsets = bank_offsets(ps_parts)
        row = {'ps1_parts_bank_count': len(ps_offsets), 'steam_parts_bank_count': bank_count,
               'tables_start': tables_start, 'quads_start': quads_start, 'banks': [], 'graphics': []}
        assert len(ps_offsets) == bank_count
        tc, qc = tables_start, quads_start
        for i, part_counts in enumerate(counts):
            start = ps_offsets[i]
            table_size, quad_size = len(part_counts)*4, sum(part_counts)*4
            ps_count = struct.unpack_from('<H', ps_parts, start+2)[0]
            assert ps_count == len(part_counts)
            headers_equal = pat[tc:tc+table_size] == ps_parts[start:start+table_size]
            quad_equal = pat[qc:qc+quad_size] == ps_parts[start+table_size:start+table_size+quad_size]
            actual_counts = [struct.unpack_from('<H', ps_parts, start+f*4)[0] for f in range(ps_count)]
            row['banks'].append({'bank': i, 'frame_references': ps_count, 'part_counts_equal': list(part_counts) == actual_counts,
                                 'frame_headers_equal': headers_equal, 'part_records_equal': quad_equal,
                                 'steam_table_offset': tc, 'steam_parts_offset': qc})
            tc += table_size
            qc += quad_size
        for bank_id in range(len(bank_offsets(ps_graphics, allow_aliases=True))):
            name = f'{player}_{bank_id:03d}.'
            candidates = [f for f in files if f.is_file() and f.name.startswith(name)]
            if not candidates:
                row['graphics'].append({'bank': bank_id, 'status': 'no_matching_TEX_name'})
                continue
            tex = next(f.read_bytes() for f in candidates if f.read_bytes()[:4] == b'TEX\0')
            cof = next(f.read_bytes() for f in candidates if f.read_bytes()[:4] == b'COF\0')
            # The length-prefixed embedded path is followed by count and 256 Y offsets.
            path_size = cof[16]
            cp = 17+path_size
            n = u32(cof, cp)
            ys = struct.unpack_from('<256I', cof, cp+4)
            assert cp+4+256*4 == len(cof)
            bank = graphics_bank(ps_graphics, bank_id, allow_bank_aliases=True)
            if n != len(bank['frames']):
                row['graphics'].append({'bank': bank_id, 'status': 'reference_counts_differ_mapping_unresolved',
                                         'steam_cof_count': n, 'ps1_reference_count': len(bank['frames'])})
                continue
            tex_start = u32(tex, 16)
            dims = u32(tex, 8)
            width, height = (dims >> 6) & 8191, dims >> 19
            assert tex[13] == 0x12 and width == 256
            pixels = tex[tex_start:]
            assert len(pixels) == width*height
            matched, failures = 0, []
            for f, y0 in zip(bank['frames'], ys):
                raw = decode_stream(ps_graphics, f['offset'], f['limit'], f['tile_count']*128).data
                atlas, mapping, atlas_height = indexed_atlas(raw, f['tile_count'])
                assert y0+atlas_height <= height
                bad = sum(pixels[y0*256+j] != b for j, b in enumerate(atlas) if mapping[j] is not None)
                if bad:
                    failures.append({'frame': f['index'], 'different_loaded_pixels': bad})
                else:
                    matched += 1
            row['graphics'].append({'bank': bank_id, 'references': n, 'exact_index_pixel_matches': matched,
                                     'mismatches': failures, 'texture_size': [width, height], 'cof_count_offset': cp})
        row['all_part_records_match'] = all(b['frame_headers_equal'] and b['part_records_equal'] and b['part_counts_equal'] for b in row['banks'])
        row['all_loaded_pixels_match'] = all('references' in b and b['exact_index_pixel_matches'] == b['references'] for b in row['graphics'])
        report['players'][player] = row
    (WORK/'player_mapping.json').write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(report, ensure_ascii=False))


if __name__ == '__main__':
    main()
