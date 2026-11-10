"""Independent final save-atlas pixels, origins, palettes and direct UV audit."""
import hashlib
import json
import struct
from pathlib import Path
from native_contracts import ROOT
import numpy as np
from PIL import Image
from scripts.discover_inputs import DiscReader, psx_arc
from src.psx_ui_atlas import aliased_composition, local_composition, tile_pixels
from src.psx_static_effect import compose_static
from check_special import entries, compose, full

OUT = Path(__file__).resolve().parent
PREP = OUT.parent / 'ui/prepared_v1'


def sha(b): return hashlib.sha256(b).hexdigest()


def ui(menu, texture, frame, base):
    result = Image.new('RGBA', (384, 384))
    po = struct.unpack_from('<I', menu, 4)[0]
    comp = aliased_composition(menu, 2, frame)
    for p in comp['parts']:
        c = local_composition({**comp, 'parts': [p]})
        data, size, bb, _ = compose_static(texture, c)
        indices = np.frombuffer(data, np.uint8).reshape(size[1], size[0])
        words = struct.unpack_from('<16H', menu, po + (base + p['clut']) * 32)
        table = np.array([[(w >> s & 31) * 255 // 31 for s in (0, 5, 10)] + [255 if i else 0] for i, w in enumerate(words)], np.uint8)
        result.alpha_composite(Image.fromarray(table[indices]), (160 + bb[0], 160 + bb[1]))
    return result


def fourth(menu, texture, mask, arm):
    image = ui(menu, texture, 44, 8)
    for bit, frame in ((1, 45), (2, 46), (4, 47), (8, 48)):
        if mask & bit:
            image.alpha_composite(ui(menu, texture, frame, 10 if bit == 4 and arm == 2 else 8))
    return image


def main():
    proof = {}
    uv = json.loads((OUT / 'menu_uv_audit.json').read_text('utf8'))
    for project in ('ver_buki_riko', 'ver_rin_nana'):
        proposal = json.loads((PREP / project / 'proposal.json').read_text('utf8'))
        path = ROOT / proposal['baseline']
        with path.open('rb') as f:
            d = DiscReader(f, path.stat().st_size)
            rs = {r['name'].split(';')[0]: r for r in d.inspect()['files']}
            original = {n: d.read(rs[n]['lba'], rs[n]['size']) for n in proposal['files']}
        prepared = {n: (ROOT / v['path']).read_bytes() for n, v in proposal['files'].items()}
        for n, row in proposal['files'].items():
            assert sha(original[n]) == row['before'] and sha(prepared[n]) == row['after']
            assert len(original[n]) == len(prepared[n]) == row['size']
        old, new = original['MOJIPAT.ARC'], prepared['MOJIPAT.ARC']
        oa, na = entries(original['LOAD_U.ARC']), entries(prepared['LOAD_U.ARC'])
        assert set(oa) == set(na) and all(oa[k] == na[k] for k in oa if k != 0x10008)
        ot, nt = oa[0x10008], na[0x10008]
        ooff, noff = struct.unpack_from('<4I', old), struct.unpack_from('<4I', new)
        assert ooff == noff and old[:ooff[2]] == new[:noff[2]] and old[ooff[3]:] == new[noff[3]:]
        frames = []
        for n in range(52):
            a, b = ui(old, ot, n, 8), ui(new, nt, n, 8)
            assert a.tobytes() == b.tobytes()
            frames.append({'frame': n, 'RGBA_sha256': sha(b.tobytes())})
        for row in (8, 27):
            assert ui(old, ot, 43, row).tobytes() == ui(new, nt, 43, row).tobytes()
        equipment = []
        for arm in (1, 2):
            for mask in range(16):
                a, b = fourth(old, ot, mask, arm), fourth(new, nt, mask, arm)
                assert a.tobytes() == b.tobytes()
                for flip in (False, True):
                    aa, bb = np.array(a), np.array(b)
                    assert np.array_equal(aa[:, ::-1] if flip else aa, bb[:, ::-1] if flip else bb)
                equipment.append([mask, arm, sha(b.tobytes())])
        base_arc = (OUT / project / 'source_PL02_U.ARC').read_bytes()
        es = entries(base_arc)
        jacket, swimsuit = ui(new, nt, 52, 30), ui(new, nt, 53, 31)
        assert jacket.tobytes() == full(es, 0).tobytes()
        assert swimsuit.tobytes() == compose(es, 0, 0).tobytes()
        old_jacket = np.asarray(ui(old, ot, 52, 30))
        new_jacket = np.asarray(jacket)
        opaque = old_jacket[:, :, 3] > 0
        assert np.array_equal(old_jacket[opaque], new_jacket[opaque])
        added = int(np.sum((old_jacket[:, :, 3] == 0) & (new_jacket[:, :, 3] > 0)))
        assert added == (9 if project == 'ver_buki_riko' else 1)
        direct = {y * 16 + x for y in (13, 14, 15) for x in range(13)}
        for row in uv['projects'][project]['direct_loading_rectangles']: direct.update(row['tiles'])
        assert all(tile_pixels(ot, t) == tile_pixels(nt, t) for t in direct)
        changed_tiles = [t for t in range(256) if tile_pixels(ot, t) != tile_pixels(nt, t)]
        assert not direct & set(changed_tiles)
        expected_code = (OUT.parent / 'ui/save_code' / project / 'SLUS_005.61').read_bytes()
        assert prepared['SLUS_005.61'] == expected_code
        for n, row in proposal['files'].items(): assert sha((ROOT / row['path']).read_bytes()) == row['after']
        proof[project] = dict(final_resource_hashes={n: sha(b) for n, b in prepared.items()},
                              old_52_frames_RGBA_origin_preserved=frames,
                              normal_fourth_32_combinations_both_orientations_preserved=equipment,
                              normal_and_black_zero_frame43_exact=True,
                              jacket_old_opaque_all_preserved=True, jacket_added_gameplay_pixels=added,
                              jacket_and_swimsuit_RGBA_exact_gameplay_idle=True,
                              frame52_RGBA_sha256=sha(jacket.tobytes()), frame53_RGBA_sha256=sha(swimsuit.tobytes()),
                              all_menu_palettes_and_other_banks_preserved=True,
                              loading_other_entries_preserved=True, direct_UV_tiles_checked=sorted(direct),
                              direct_UV_tiles_all_preserved=True, changed_texture_tiles=changed_tiles,
                              executable_matches_independently_CPU_checked_preparation=True,
                              native_frame53_report='menu_frame53_' + project + '.json')
    report = dict(passed=True, projects=proof, scope='Frozen prepared_v1 resources; static exact pixels plus separately linked native constructor and frame selection checks.',
                  runtime_verified=False, game_or_pointer_written=False, process_memory_accessed=False)
    (OUT / 'ui_assets_independent.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf8')
    print(json.dumps({'passed': True, 'projects': list(proof)}))


if __name__ == '__main__': main()
