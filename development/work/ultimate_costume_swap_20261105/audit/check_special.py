"""Read back prepared special ARC assets and execute native 32-tile decoding."""
import hashlib
import json
import struct
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
import numpy as np
from PIL import Image
from scripts.discover_inputs import psx_arc
from scripts.overhaul_nana_buffer_watch import cpu_checks
from src.psx_player import graphics_bank, composition_frame, decode_stream, bank_offsets, compose_indices

OUT = Path(__file__).resolve().parent
PREP = OUT.parent / 'core/prepared_special_v1'
SPECIAL = set(range(217, 231))
SKIP = {105, *range(175, 183)}


def sha(b):
    return hashlib.sha256(b).hexdigest()


def entries(arc):
    return {int(e['type'], 16): arc[e['offset']:e['offset'] + e['size']] for e in psx_arc(arc)}


def compose(es, frame, cb):
    f = graphics_bank(es[2], 0, allow_bank_aliases=True)['frames'][frame]
    raw = decode_stream(es[2], f['offset'], f['limit'], f['tile_count'] * 128).data
    comp = composition_frame(es[3], cb, frame)
    if cb:
        comp = {**comp, 'parts': [{**p, 'clut': 0} for p in comp['parts']]}
    arr = np.zeros((384, 384), np.uint8)
    if comp['parts']:
        p, size, bounds, _ = compose_indices(raw, f['tile_count'], comp, allowed_cluts={0, 1, 2, 3})
        little = np.frombuffer(p, np.uint8).reshape(size[1], size[0])
        arr[160 + bounds[1]:160 + bounds[3], 160 + bounds[0]:160 + bounds[2]] = little
    words = struct.unpack_from('<64H', es[9]) if not cb else struct.unpack_from('<16H', es[9], 64 if cb == 7 else 32)
    colors = np.array([[(w >> s & 31) * 255 // 31 for s in (0, 5, 10)] + [255 if i % 16 else 0] for i, w in enumerate(words)], np.uint8)
    return Image.fromarray(colors[arr])


def full(es, frame):
    result = compose(es, frame, 0)
    for bank in (8, 5, 7, 6):
        result.alpha_composite(compose(es, frame, bank))
    return result


def records(es, bank, frame):
    return [(p['flags'], p['tile'], p['x'], p['y']) for p in composition_frame(es[3], bank, frame)['parts']]


def main():
    results = {}
    for project in ('ver_buki_riko', 'ver_rin_nana'):
        folder = PREP / project
        proposal = json.loads((folder / 'proposal.json').read_text('utf8'))
        before = (OUT / project / 'source_PL02_U.ARC').read_bytes()
        after = (folder / 'PL02_U.ARC').read_bytes()
        assert sha(before) == proposal['source_arc_sha256'] and sha(after) == proposal['after_sha256']
        assert len(before) == len(after)
        a, b = entries(before), entries(after)
        assert set(a) == set(b)
        assert all(a[k] == b[k] for k in a if k not in (2, 3))
        assert bank_offsets(a[2], allow_aliases=True) == bank_offsets(b[2], allow_aliases=True)
        assert bank_offsets(a[3]) == bank_offsets(b[3])
        changed_graphics = []
        for bank in range(len(bank_offsets(a[2], allow_aliases=True))):
            old = graphics_bank(a[2], bank, allow_bank_aliases=True)
            new = graphics_bank(b[2], bank, allow_bank_aliases=True)
            assert (old['base'], old['end'], len(old['frames'])) == (new['base'], new['end'], len(new['frames']))
            for of, nf in zip(old['frames'], new['frames']):
                oraw = decode_stream(a[2], of['offset'], of['limit'], of['tile_count'] * 128).data
                nraw = decode_stream(b[2], nf['offset'], nf['limit'], nf['tile_count'] * 128).data
                if oraw != nraw:
                    changed_graphics.append([bank, of['index']])
                    assert bank == 0 and of['index'] in SPECIAL
        assert changed_graphics == [[0, n] for n in sorted(SPECIAL)]
        changed_parts = []
        for bank in range(len(bank_offsets(a[3]))):
            count = composition_frame(a[3], bank, 0)['bank_frame_count']
            assert composition_frame(b[3], bank, 0)['bank_frame_count'] == count
            for n in range(count):
                if records(a, bank, n) != records(b, bank, n):
                    changed_parts.append([bank, n])
                    assert bank in (0, 5) and n in SPECIAL
        checked = 0
        for n in range(237):
            if n in SKIP or n in SPECIAL:
                continue
            assert compose(a, n, 0).tobytes() == compose(b, n, 0).tobytes()
            assert full(a, n).tobytes() == full(b, n).tobytes()
            checked += 1
        image_proof = []
        for row in proposal['registration']:
            n = row['frame']
            native_image = full(b, n).crop((80, 80, 336, 240))
            shown = Image.open(folder / f'after_{n:03}.png').convert('RGBA')
            assert native_image.size == shown.size and native_image.tobytes() == shown.tobytes()
            lower = None
            if row['kind'] == 'hover':
                cut = row['cut_y_local']
                old_image = full(a, n).crop((80, 80, 336, 240))
                lower = native_image.crop((0, cut, 256, 160)).tobytes() == old_image.crop((0, cut, 256, 160)).tobytes()
                assert lower
            image_proof.append({'frame': n, 'RGBA_sha256': sha(native_image.tobytes()), 'prepared_preview_exact': True, 'hover_lower_RGBA_exact': lower})
        bank = graphics_bank(b[2], 0, allow_bank_aliases=True)
        assert max(f['tile_count'] for f in bank['frames']) <= 32
        frames = {f['index']: (f, decode_stream(b[2], f['offset'], f['limit'], f['tile_count'] * 128).data) for f in bank['frames'] if f['index'] in SPECIAL}
        exe = (OUT.parent / f'renderer/{project}.exe').read_bytes()
        actual = cpu_checks(exe, b, bank, frames)
        plain = cpu_checks(exe, b, bank, frames, observe_writes=False)
        assert actual == plain and len(actual) == 14
        results[project] = {'source_sha256': sha(before), 'prepared_sha256': sha(after),
                            'all_512_graphics_references_decoded': True,
                            'changed_graphics': changed_graphics, 'changed_parts': changed_parts,
                            'unchanged_pre_and_full_RGBA_pairs': checked,
                            'palette_animation_sound_and_other_entries_unchanged': True,
                            'bank_offsets_and_lengths_preserved': True,
                            'native_decode_upload_queue': actual, 'observed_and_unobserved_native_equal': True,
                            'prepared_RGBA_readback': image_proof}
    report = {'passed': True, 'projects': results, 'native_decoder_cases': 28,
              'native_execution_runs_including_unobserved': 56,
              'scope': 'Prepared special ARC only; no intro correction, no save UI or complete integrated BIN validation.',
              'visual_review': 'Both prepared special_review.png files were viewed. Existing pose fragments form the replacement body; this is not a one-to-one original swimsuit Nova/hover asset swap.',
              'runtime_verified': False, 'game_or_pointer_written': False}
    (OUT / 'special_independent.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf8')
    print(json.dumps({'passed': True, 'native_cases': 28, 'runtime_verified': False}))


if __name__ == '__main__':
    main()
