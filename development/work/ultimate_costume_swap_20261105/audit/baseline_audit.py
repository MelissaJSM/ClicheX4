"""Ultimate 전후 교환 전의 실제 디스크 프레임/공유/팔레트 읽기 전용 감사."""
import hashlib
import json
import struct
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
import numpy as np
from PIL import Image, ImageDraw
from scripts.discover_inputs import DiscReader, psx_arc
from scripts.overhaul_sprites_audit import render, rgba, metrics
from scripts.prepare_riko_ui import entry
from src.psx_player import bank_offsets, graphics_bank, composition_frame, decode_stream

OUT = Path(__file__).resolve().parent
EXPECTED = {'ver_buki_riko': '852813890c3c9f8e0394026f8c243f6c323f1a9c0f4e1941eaa920b85bdecc4e', 'ver_rin_nana': 'aca6d7839ad1956ea837b07d1105a7609817cd30fd0e6ceffe13e6dd611ad6fe'}
SKIP = {105, *range(175, 183)}
SPECIAL = [0, 109, 112, 114, 131, 133, 136, 140, 148, 149, 150, 156, 157, 158, 162, 170, 174, 183, 204, 208, 210, 213, 215, *range(217, 231), 233]

def sha(x):
    return hashlib.sha256(x).hexdigest()

def digest(p):
    h = hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda: f.read(8 * 1024 * 1024), b''):
            h.update(b)
    return h.hexdigest()

def load(p):
    with p.open('rb') as f:
        d = DiscReader(f, p.stat().st_size)
        rows = {r['name'].split(';')[0]: r for r in d.inspect()['files']}
        names = ['PL02_U.ARC', 'SLUS_005.61']
        return {n: d.read(rows[n]['lba'], rows[n]['size']) for n in names}, {n: rows[n] for n in names}

def forms(arc, n):
    words = struct.unpack_from('<64H', entry(arc, 9))
    base, metadata = render(arc, 0, 0, n)
    pre = rgba(base, words)
    post = pre.copy()
    layers = []
    for bank in (8, 5, 7, 6):
        indices, meta = render(arc, 0, bank, n)
        im = rgba(indices, words[32:48] if bank == 7 else words[16:32])
        post.alpha_composite(im)
        layers.append({'bank': bank, 'opaque_pixels': int(np.sum(np.asarray(im)[:, :, 3] != 0)), 'parts': len(meta['parts']), 'clut_flags': sorted({p['clut'] for p in meta['parts']}), 'tiles': sorted({p['tile'] for p in meta['parts']})})
    return pre, post, base, metadata, layers

def board(folder, frames):
    w, h, cols = 256, 216, 4
    page = Image.new('RGB', (w * cols, h * ((len(frames) + cols - 1) // cols)), (28, 34, 45))
    dr = ImageDraw.Draw(page)
    for i, n in enumerate(frames):
        x, y = (i % cols) * w, (i // cols) * h
        dr.text((x + 6, y + 3), f'{n}: PRE swimsuit | POST jacket', fill='white')
        for k, mode in enumerate(('pre', 'post')):
            im = Image.open(folder / mode / f'{n:03}.png').convert('RGBA')
            im = im.crop((128, 108, 192, 208)).resize((128, 200), Image.Resampling.NEAREST)
            page.paste(im, (x + k * 128, y + 16), im)
    page.save(folder / 'special_before.png')

def main():
    source, _ = load(ROOT / 'MegaMan X4.bin')
    original = source['PL02_U.ARC']
    results = {}
    for project, expected in EXPECTED.items():
        pbytes = (ROOT / 'projects' / project / 'current_build.json').read_bytes()
        pointer = json.loads(pbytes)
        path = ROOT / Path(pointer['cue']).with_suffix('.bin')
        assert pointer['sha256'] == expected and digest(path) == expected
        assets, records = load(path)
        arc = assets['PL02_U.ARC']
        folder = OUT / project
        folder.mkdir(exist_ok=False)
        (folder / 'source_PL02_U.ARC').write_bytes(arc)
        (folder / 'pointer_before.json').write_bytes(pbytes)
        (folder / 'pre').mkdir()
        (folder / 'post').mkdir()
        g, c, pal = [entry(arc, k) for k in (2, 3, 9)]
        base_bank = graphics_bank(g, 0, allow_bank_aliases=True)
        groups = {}
        for f in base_bank['frames']:
            groups.setdefault(f['offset'], []).append(f['index'])
        rows = []
        for f in base_bank['frames']:
            n = f['index']
            if n in SKIP:
                continue
            pre, post, indices, meta, layers = forms(arc, n)
            pre.save(folder / 'pre' / f'{n:03}.png')
            post.save(folder / 'post' / f'{n:03}.png')
            a, b = np.asarray(pre), np.asarray(post)
            pre_opaque, post_opaque = a[:, :, 3] > 0, b[:, :, 3] > 0
            original_pre, _, _, _, _ = forms(original, n)
            old_indices, old_meta = render(original, 0, 0, n)
            rows.append({'frame': n, 'tile_count': f['tile_count'], 'bytes_in_4096_decode_buffer': f['tile_count'] * 128, 'remaining_decode_buffer_bytes': 4096 - f['tile_count'] * 128, 'stream_offset': f['offset'], 'stream_aliases': groups[f['offset']], 'pre_rgba_sha256': sha(a.tobytes()), 'post_rgba_sha256': sha(b.tobytes()), 'pre_metrics': metrics(indices), 'post_opaque_pixels': int(post_opaque.sum()), 'post_colors': len(np.unique(b[post_opaque], axis=0)), 'old_post_pixels_outside_old_pre_alpha': int(np.sum(post_opaque & ~pre_opaque)), 'old_pre_pixels_outside_old_post_alpha': int(np.sum(pre_opaque & ~post_opaque)), 'pre_post_rgba_equal': bool(np.array_equal(a, b)), 'pre_indices_equal_original_X4': bool(np.array_equal(indices, old_indices)), 'pre_stream_equal_original_X4': meta['raw_sha256'] == old_meta['raw_sha256'], 'base_parts': len(meta['parts']), 'base_flags': sorted({p['flags'] for p in meta['parts']}), 'base_clut_flags': sorted({p['clut'] for p in meta['parts']}), 'layers': layers})
        graphics = []
        all_raw = 0
        for gb in range(len(bank_offsets(g, allow_aliases=True))):
            b = graphics_bank(g, gb, allow_bank_aliases=True)
            unique = {}
            for f in b['frames']:
                key = (f['offset'], f['tile_count'])
                if key not in unique:
                    d = decode_stream(g, f['offset'], f['limit'], f['tile_count'] * 128)
                    unique[key] = {'offset': f['offset'], 'end': d.end, 'tile_count': f['tile_count'], 'raw_sha256': sha(d.data), 'encoded_bytes': d.end - f['offset']}
                all_raw += 1
            graphics.append({'bank': gb, 'base': b['base'], 'end': b['end'], 'frames': len(b['frames']), 'max_tiles': max(f['tile_count'] for f in b['frames']), 'unique_stream_count': len(unique), 'total_stream_bytes': sum(v['encoded_bytes'] for v in unique.values()), 'tail_slack': b['end'] - max(v['end'] for v in unique.values()), 'streams': list(unique.values())})
        composition = []
        for cb in range(len(bank_offsets(c))):
            frame_count = composition_frame(c, cb, 0)['bank_frame_count']
            parts = [composition_frame(c, cb, n)['parts'] for n in range(frame_count)]
            composition.append({'bank': cb, 'base': bank_offsets(c)[cb], 'end': (bank_offsets(c) + [len(c)])[cb + 1], 'frames': frame_count, 'max_parts': max(map(len, parts)), 'blank_frames': [n for n, p in enumerate(parts) if not p], 'unknown_flags_values': sorted({q['unknown_flags'] for p in parts for q in p})})
        rows_palette = [pal[i:i + 32] for i in range(0, len(pal), 32)]
        palette_differences = [{'row': i, 'sha256': sha(v), 'rgb555_words': list(struct.unpack('<16H', v))} for i, v in enumerate(rows_palette) if i < 4]
        report = {'project': project, 'source_bin': path.relative_to(ROOT).as_posix(), 'source_sha256': expected, 'resources': {n: {'record': records[n], 'sha256': sha(v)} for n, v in assets.items()}, 'graphics_entry_sha256': sha(g), 'composition_entry_sha256': sha(c), 'palette_entry_sha256': sha(pal), 'graphics_bank_offsets': bank_offsets(g, allow_aliases=True), 'composition_bank_offsets': bank_offsets(c), 'all_decoded_graphics_references': all_raw, 'gameplay_decoded_pre_post_pairs': len(rows), 'skipped_placeholder_frames': sorted(SKIP), 'tile_histogram_bank0': dict(Counter(f['tile_count'] for f in base_bank['frames'])), 'frames_at_32tile_limit': [f['index'] for f in base_bank['frames'] if f['tile_count'] == 32], 'frames_post_alpha_exceeds_pre': [r['frame'] for r in rows if r['old_post_pixels_outside_old_pre_alpha']], 'total_post_pixels_outside_pre_alpha': sum(r['old_post_pixels_outside_old_pre_alpha'] for r in rows), 'pre_post_equal_frames': [r['frame'] for r in rows if r['pre_post_rgba_equal']], 'graphics': graphics, 'composition': composition, 'first_palette_rows': palette_differences, 'frames': rows, 'scope': 'Static exact disc decoding. Post colors use established normal-body and armor/arm palette interpretation; not a new runtime or flashing-state proof. Cropped comparison sheet only, uncropped RGBA PNGs retained.', 'protection': {'game_written': False, 'pointer_written': False, 'save_written': False, 'emulator_controlled': False}}
        (folder / 'before.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf8')
        board(folder, SPECIAL)
        results[project] = {k: report[k] for k in ('source_sha256', 'all_decoded_graphics_references', 'gameplay_decoded_pre_post_pairs', 'frames_at_32tile_limit', 'frames_post_alpha_exceeds_pre', 'total_post_pixels_outside_pre_alpha', 'pre_post_equal_frames')}
        print(json.dumps({'project': project, 'pairs': len(rows), 'overlay_only_swap_would_leave_jacket_frames': len(report['frames_post_alpha_exceeds_pre']), 'tiles32': len(report['frames_at_32tile_limit']), 'special217_230': [{'frame': r['frame'], 'pre_opaque': r['pre_metrics']['opaque_pixels'], 'post_opaque': r['post_opaque_pixels'], 'pre_equals_US': r['pre_indices_equal_original_X4']} for r in rows if 217 <= r['frame'] <= 230]}, ensure_ascii=True), flush=True)
        assert (ROOT / 'projects' / project / 'current_build.json').read_bytes() == pbytes
    (OUT / 'summary.json').write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding='utf8')

if __name__ == '__main__':
    main()
