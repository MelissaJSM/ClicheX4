"""승인된 기존 시부키 여섯 포즈의 색 병합 전 명암을 원래 texel에 복원한다.

그림 생성/리사이즈/팔레트/조립/타일 수 변경 없이 실제 표시되는 texel의
색만 바꾼다. gfx0 bounded repack 후 다른 교정 함수를 순차 호출할 수 있다.
"""
import argparse
from collections import defaultdict
import json
from pathlib import Path
import struct
import sys

import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.audit_sprite_consistency_coverage import (
    read_assets, unique_entry, sha, file_sha, write, psx_arc, X_PLACEHOLDERS)
from src.psx_player import bank_offsets, graphics_bank, decode_stream, composition_frame, compose_indices, indexed_atlas
from src.psx_ui_atlas import local_composition
from src.psx_frame_edit import read_indexed_png
from src.psx_compress import encode_stream
from src.psx_bank_repack import repack_graphics_bank

BASE = 'b29e6336a813ce388a36a2966b1fd50f0fccd054ded5520167e271fc11572e2b'
SOURCE = 'out/ver_buki_riko/ultimate_costumes_swapped_20261105_v1/shibuki_riko.bin'
SOURCE_SHA = 'bedba81a4c1263388835e10f57a8e30f6b7e9d9ac6f3f3d3dbf77821f4fb7c08'
D = ROOT / 'work/sprite_consistency_20261105/coverage/shibuki_special'
RECOVERY_SHA = '66b0b4d6d9346757d7938fed256b485017fb97cb38daeab011c511f684203c30'
FRAMES = (101, 102, 103, 104, 231, 232)
PARTS = (0, 5, 6, 7, 8)


def need(value, message):
    if not value:
        raise ValueError(message)


def entry_replace(arc, typ, data):
    entries = [e for e in psx_arc(arc) if int(e['type'], 16) == typ]
    need(len(entries) == 1 and len(data) == entries[0]['size'], 'Unique fixed-size entry required')
    e = entries[0]
    return arc[:e['offset']] + bytes(data) + arc[e['offset'] + e['size']:]


def targets():
    path = D / 'recovery_manifest.json'
    need(file_sha(path) == RECOVERY_SHA, 'Recovery manifest changed')
    manifest = json.loads(path.read_text('utf8'))
    palette = struct.unpack('<16H', (D / 'palette.bin').read_bytes())
    rows = {r['frame']: r for r in manifest['candidates'] if r['kind'] == 'full_detail'}
    need(set(rows) == set(FRAMES), 'Recovery selection differs')
    images = {}
    for n, r in rows.items():
        path = ROOT / r['path']
        need(file_sha(path) == r['png_sha256'], f'Recovery PNG changed: {n}')
        pixels, size = read_indexed_png(path, palette)
        need(size == (160, 160) and sha(pixels) == r['indices_sha256'], 'Recovery indices changed')
        images[n] = np.frombuffer(pixels, np.uint8).reshape(160, 160)
    return images, rows, palette


def native_raw(g, b, n):
    f = graphics_bank(g, b, allow_bank_aliases=True)['frames'][n]
    return decode_stream(g, f['offset'], f['limit'], f['tile_count'] * 128).data, f


def layer(raw, count, c, cb, n):
    comp = composition_frame(c, cb, n)
    if cb:
        comp = local_composition(comp)
    world = np.zeros((160, 160), np.uint8)
    if comp['parts']:
        pix, size, box, _ = compose_indices(raw, count, comp, allowed_cluts={0, 1, 2, 3})
        need(-80 <= box[0] <= box[2] <= 80 and -80 <= box[1] <= box[3] <= 80, 'World canvas overflow')
        world[80 + box[1]:80 + box[3], 80 + box[0]:80 + box[2]] = np.frombuffer(pix, np.uint8).reshape(size[1], size[0])
    return world


def composite(layers, pal, mask, arm):
    world = np.zeros((160, 160), np.uint32)
    for bit, cb in ((0, 0), (8, 8), (1, 5), (4, 7), (2, 6)):
        if bit and not mask & bit:
            continue
        indices = layers[cb]
        offset = 0 if cb == 0 else 32 if cb == 7 and arm == 2 else 16
        colors = np.array(pal[offset:offset + 16], np.uint32) + 1
        world[indices > 0] = colors[indices[indices > 0]]
    return world


def restore_visible_texels(raw, count, composition, target):
    before, size, box, provenance = compose_indices(raw, count, composition)
    cropped = target[80 + box[1]:80 + box[3], 80 + box[0]:80 + box[2]].tobytes()
    need(len(cropped) == len(before) and all(bool(a) == bool(b) for a, b in zip(before, cropped)), 'Alpha/silhouette change rejected')
    # Only the source nibble that actually wins the native opaque draw is edited.
    # Flattening into every overlapping part would create opaque hidden texels.
    writes = {}
    for i, (a, b) in enumerate(zip(before, cropped)):
        if a == b:
            continue
        owner = provenance[i]
        need(owner is not None and a and b, 'No original opaque owner')
        key = owner['byte'], owner['shift']
        need(key not in writes or writes[key] == b, 'Conflicting shared source texel')
        writes[key] = b
    result = bytearray(raw)
    for (offset, shift), value in writes.items():
        result[offset] = result[offset] & ~(15 << shift) | value << shift
    result = bytes(result)
    need(compose_indices(result, count, composition)[0] == cropped, 'Shared texel changed another visible pixel')
    before_atlas = np.frombuffer(indexed_atlas(raw, count)[0], np.uint8).reshape(-1, 256)
    after_atlas = np.frombuffer(indexed_atlas(result, count)[0], np.uint8).reshape(-1, 256)
    need(np.array_equal(before_atlas != 0, after_atlas != 0), 'Raw tile alpha changed')
    need(np.array_equal(before_atlas[:, 0], after_atlas[:, 0]), 'GPU tile 0/16 first column changed')
    edges = []
    for p in composition['parts']:
        if p['flip_y']:
            y = p['tile'] // 16 * 16
            x = p['tile'] % 16 * 16
            aa, bb = before_atlas[y, x:x + 16], after_atlas[y, x:x + 16]
            need(np.array_equal(aa > 0, bb > 0), 'FlipY first-row alpha expanded')
            edges.append({'part': p['index'], 'tile': p['tile'], 'color_changes': int((aa != bb).sum()), 'opaque_positions_exact': True})
    return result, {'changed_visible_texels': len(writes), 'raw_alpha_exact': True,
                    'gpu_first_column_values_exact': True, 'flip_y_first_rows': edges}


def patch_special_detail(data, baseline, *, expected_input_sha=None):
    """Apply before/after another semantic patch only with an explicit input SHA."""
    need(sha(baseline) == BASE, 'Unsupported baseline')
    need(sha(data) == (expected_input_sha or BASE), 'Unsupported input SHA')
    need(len(data) == len(baseline), 'ARC size changed')
    g, c, p = (unique_entry(data, t) for t in (2, 3, 9))
    bg, bc, bp = (unique_entry(baseline, t) for t in (2, 3, 9))
    need(p == bp and bank_offsets(g, allow_aliases=True) == bank_offsets(bg, allow_aliases=True), 'Palette/graphics layout changed')
    need(bank_offsets(c) == bank_offsets(bc), 'Parts bank layout changed')
    desired, recovery, palette = targets()
    need(tuple(struct.unpack_from('<16H', p)) == palette, 'Recovery palette mismatch')
    bank = graphics_bank(g, 0, allow_bank_aliases=True)
    aliases = defaultdict(list)
    for f in bank['frames']:
        aliases[f['offset']].append(f['index'])
    encoded = {}; changed_raw = {}; frame_proofs = []
    for n in FRAMES:
        raw, f = native_raw(g, 0, n); base_raw, bf = native_raw(bg, 0, n)
        need(raw == base_raw and f['tile_count'] == bf['tile_count'] <= 32, 'Selected raw frame already modified')
        need(aliases[f['offset']] == [n], 'New stream sharing requires explicit handling')
        for cb in PARTS:
            def semantic(comp):
                return [{k: v for k, v in pp.items() if k not in ('index', 'record_offset')} for pp in comp['parts']]
            need(semantic(composition_frame(c, cb, n)) == semantic(composition_frame(bc, cb, n)), 'Selected composition changed')
        # A same numeric reference in another parts bank is a different object
        # resource, not a gfx0 alias. Main X rendering uses 0/5/6/7/8; every
        # other graphics bank and the complete composition entry stay exact.
        cp = composition_frame(c, 0, n)
        base_tiles = {pp['tile'] for pp in cp['parts']}
        armor_tiles = {pp['tile'] for cb in PARTS[1:] for pp in composition_frame(c, cb, n)['parts']}
        need(not base_tiles & armor_tiles, 'Shared base/armor tile ownership')
        new, proof = restore_visible_texels(raw, f['tile_count'], cp, desired[n])
        need(np.array_equal(layer(new, f['tile_count'], c, 0, n), desired[n]), 'Full recovered canvas differs')
        changed_raw[n] = new; encoded[n] = encode_stream(new)
        frame_proofs.append({'frame': n, 'tile_count': f['tile_count'], 'recovery': recovery[n],
                             'before_raw_sha256': sha(raw), 'after_raw_sha256': sha(new),
                             'encoded_size': len(encoded[n]), 'base_armor_tiles_disjoint': True, **proof})
    ng, packing = repack_graphics_bank(g, 0, encoded)
    result = entry_replace(data, 2, ng)
    need(entry_replace(result, 2, g) == data, 'Other ARC entries changed')
    checks = 0; changed = []
    for gb in range(len(bank_offsets(g, allow_aliases=True))):
        for old in graphics_bank(g, gb, allow_bank_aliases=True)['frames']:
            n = old['index']; a, af = native_raw(g, gb, n); b, bf = native_raw(ng, gb, n)
            need(af['tile_count'] == bf['tile_count'], 'Tile count changed')
            want = changed_raw[n] if gb == 0 and n in changed_raw else a
            need(b == want, f'Decoded reference differs {gb}/{n}')
            if a != b:
                changed.append([gb, n])
            else:
                ad = decode_stream(g, af['offset'], af['limit'], af['tile_count'] * 128)
                bd = decode_stream(ng, bf['offset'], bf['limit'], bf['tile_count'] * 128)
                need(g[af['offset']:ad.end] == ng[bf['offset']:bd.end], 'Unselected compressed stream changed')
            checks += 1
    need(changed == [[0, n] for n in FRAMES], 'Unexpected decoded reference change')
    pal = struct.unpack_from('<64H', p); layer_checks = 0; mask_checks = []
    for n in range(237):
        if n in X_PLACEHOLDERS:
            continue
        old, f = native_raw(g, 0, n); new, _ = native_raw(ng, 0, n)
        before = {cb: layer(old, f['tile_count'], c, cb, n) for cb in PARTS}
        after = {cb: layer(new, f['tile_count'], c, cb, n) for cb in PARTS}
        for cb in PARTS:
            want = desired[n] if n in FRAMES and cb == 0 else before[cb]
            need(np.array_equal(after[cb], want), f'Layer mismatch {n}/{cb}')
            need(np.array_equal(before[cb] > 0, after[cb] > 0), 'Layer alpha changed')
            layer_checks += 1
        if n not in FRAMES:
            continue
        for arm in (1, 2):
            for mask in range(16):
                a = composite(before, pal, mask, arm); b = composite(after, pal, mask, arm)
                expected_layers = {**before, 0: desired[n]}
                need(np.array_equal(b, composite(expected_layers, pal, mask, arm)), 'Armor compositing changed')
                need(np.array_equal(a > 0, b > 0), 'Armor silhouette changed')
                mask_checks.append({'frame': n, 'mask': mask, 'arm': arm, 'visible_base_color_changes': int((a != b).sum()), 'armor_owned_layers_exact': True})
    return result, {'input_sha256': sha(data), 'output_sha256': sha(result), 'frames': frame_proofs,
                    'packing': packing, 'decoded_references_checked': checks, 'layer_checks': layer_checks,
                    'mask_checks': mask_checks, 'changed_decoded_refs': changed,
                    'all_nonselected_raw_and_encoded_streams_exact': True,
                    'all_composition_palette_audio_animation_entries_exact': True,
                    'alpha_coordinates_tile_counts_all_exact': True,
                    'armor_policy': '아머 전용 레이어는 불변; 덮이지 않은 기본층의 복원 색은 부분/풀아머에서도 의도적으로 표시된다.',
                    'runtime_verified': False, 'game_bin_written': False}


def preview(before, after, path):
    arcs = []
    for arc in (before, after):
        g, c, p = (unique_entry(arc, t) for t in (2, 3, 9))
        arcs.append((g, c, struct.unpack_from('<64H', p)))
    board = Image.new('RGB', (5 * 256, 6 * 300), '#252b36'); draw = ImageDraw.Draw(board)
    for row, n in enumerate(FRAMES):
        for col, (which, ref, mask, label) in enumerate(((0, 0, 0, 'idle0'), (0, n, 0, 'base before'), (1, n, 0, 'base restored'), (0, n, 15, 'Fourth before'), (1, n, 15, 'Fourth restored'))):
            g, c, pal = arcs[which]; raw, f = native_raw(g, 0, ref)
            words = composite({cb: layer(raw, f['tile_count'], c, cb, ref) for cb in PARTS}, pal, mask, 1)
            rgba = np.zeros((160, 160, 4), np.uint8); active = words > 0; color = words[active] - 1
            rgba[active] = np.stack(((color & 31) * 255 // 31, (color >> 5 & 31) * 255 // 31, (color >> 10 & 31) * 255 // 31, np.full(color.shape, 255)), axis=1)
            im = Image.fromarray(rgba).crop((48, 38, 112, 107)).resize((256, 276), Image.Resampling.NEAREST)
            board.paste(im, (col * 256, row * 300 + 24), im)
            draw.text((col * 256 + 4, row * 300 + 4), f'{ref} {label}', fill='white')
    board.save(path)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(); out = args.output.resolve()
    need(out.is_relative_to(D.resolve()) and not out.exists(), 'Fresh recovery output directory required')
    source = ROOT / SOURCE; need(file_sha(source) == SOURCE_SHA, 'Source BIN mismatch')
    assets, records = read_assets(source, ['PL00_U.ARC']); baseline = assets['PL00_U.ARC']
    result, proof = patch_special_detail(baseline, baseline)
    repeated, _ = patch_special_detail(baseline, baseline)
    need(result == repeated, 'Preparation is not reproducible')
    out.mkdir(parents=True); target = out / 'PL00_U.ARC'; target.write_bytes(result)
    need(target.read_bytes() == result, 'ARC write/readback mismatch')
    write(out / 'verification.json', {'passed': True, 'reproducible': True, **proof})
    write(out / 'proposal.json', {'project': 'ver_buki_riko', 'baseline': SOURCE, 'baseline_sha256': SOURCE_SHA,
          'files': {'PL00_U.ARC': {'before': BASE, 'after': sha(result), 'size': len(result), 'path': target.relative_to(ROOT).as_posix(), 'record': records['PL00_U.ARC']}},
          'function': 'scripts.restore_shibuki_special_detail.patch_special_detail',
          'integration': '후속 ref142 교정은 이 결과 bytes에 semantic 함수로 적용; gfx bank 바이트 차분 병합 금지.',
          'runtime_verified': False})
    preview(baseline, result, out / 'base_fourth_comparison.png')
    need(file_sha(source) == SOURCE_SHA, 'Source BIN changed')
    print(json.dumps({'output': out.relative_to(ROOT).as_posix(), 'sha256': sha(result), 'references': proof['decoded_references_checked'], 'layers': proof['layer_checks'], 'mask_checks': len(proof['mask_checks'])}))


if __name__ == '__main__':
    main()
