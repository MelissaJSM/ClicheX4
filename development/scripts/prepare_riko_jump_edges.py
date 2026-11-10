"""반전 quad의 U=0 경계를 피하도록 생성 포즈 상단을 무손실 1px 재배치."""
import argparse
import json
from pathlib import Path
import struct
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.project import new_run, write_json
from scripts.discover_inputs import sha256
from scripts.repack_zero import read_inputs
from scripts.extract_zero import save_image
from scripts.build_riko_idle import patch_frames
from src.psx_frame_edit import read_indexed_png
from src.psx_player import composition_frame


def prepare(source, extracted):
    import numpy as np
    from PIL import Image
    source = source.resolve()
    if not source.is_relative_to((ROOT/'work/ver_buki_riko').resolve()):
        raise ValueError('Expected local motion inputs')
    prior = json.loads(source.read_text(encoding='utf-8'))
    selection = json.loads((ROOT/'projects/ver_buki_riko/art_selection.json').read_text(encoding='utf-8'))
    png = ROOT/selection['indexed_png']
    if sha256(png.read_bytes()) != selection['indexed_png_sha256']:
        raise ValueError('Selected art changed')
    palette = (png.parent/'candidate_palette.bin').read_bytes()
    words = struct.unpack('<16H', palette)
    profile, _, arc, gfx_meta, gfx, parts, _ = read_inputs(extracted)
    if prior['source_sha256'] != profile['source_sha256'] or prior['palette_sha256'] != sha256(palette):
        raise ValueError('Source/palette mismatch')
    frames = {}; before = {}; audit = {}
    for key, record in prior['frames'].items():
        n = int(key); path = (source.parent/record['file']).resolve()
        if not path.is_relative_to(source.parent) or sha256(path.read_bytes()) != record['sha256']:
            raise ValueError('Changed motion source or escaped path')
        pixels, size = read_indexed_png(path, words)
        a = np.frombuffer(pixels, dtype=np.uint8).reshape(size[1], size[0])
        before[n] = a
        if n in (22, 23, 24):
            split = 32 if n == 24 else 24
            if np.any(a[:split, -1]):
                raise ValueError('Translation would discard an opaque pixel')
            b = a.copy(); b[:split, 0] = 0; b[:split, 1:] = a[:split, :-1]
            if not np.array_equal(np.bincount(a.ravel(), minlength=16), np.bincount(b.ravel(), minlength=16)):
                raise ValueError('Translation changed the pixel histogram')
            c = composition_frame(parts, 0, n)
            left = min(p['x'] for p in c['parts']); top = min(p['y'] for p in c['parts'])
            exposed = []
            for p in c['parts']:
                if p['flags']:
                    raise ValueError('Edge audit only models plain player parts')
                if p['tile'] % 16 == 0:
                    x = p['x']-left; y = p['y']-top
                    for dy in range(16):
                        if b[y+dy, x]:
                            raise ValueError('Translated sprite still touches reflected U=0 edge')
                        if a[y+dy, x]: exposed.append([x, y+dy, int(a[y+dy, x])])
            frames[n] = (b.tobytes(), size)
            audit[n] = {'translation_xy': [1, 0], 'upper_rows': [0, split],
                        'previously_clipped_pixels': exposed, 'pixels_discarded': 0,
                        'palette_histogram_preserved': True, 'lower_rows_unchanged': True}
        else:
            frames[n] = (pixels, size)
    if set(frames) != {5, 6, *range(21, 35)}:
        raise ValueError('Complete jump family required')
    _, checks = patch_frames(arc, gfx_meta, gfx, parts, frames, palette)
    out = new_run(ROOT, 'ver_buki_riko', 'jump_edge_frames')
    records = {}
    board = Image.new('RGBA', (56*6*2, 64*6*3), (38, 41, 50, 255))
    for n, frame in frames.items():
        name = f'frame_{n:03d}.png'
        picture = save_image(*frame, words, out/name)
        records[str(n)] = {'file': name, 'sha256': sha256((out/name).read_bytes())}
        if n in audit:
            row = (22, 23, 24).index(n)
            old = save_image(before[n].tobytes(), frame[1], words, out/f'before_{n:03d}.png')
            for col, image in enumerate((old, picture)):
                board.alpha_composite(image.convert('RGBA').resize((image.width*6, image.height*6), Image.Resampling.NEAREST),
                                      (col*56*6, row*64*6))
    board.save(out/'edge_alignment_6x.png')
    write_json(out/'motion_set.json', {'source_sha256': profile['source_sha256'], 'palette_sha256': sha256(palette),
                                      'frames': records, 'previous_manifest': str(source),
                                      'previous_manifest_sha256': sha256(source.read_bytes()),
                                      'alignment_audit': audit, 'checks': checks,
                                      'method': 'Lossless crop placement of existing generated art; no new colors or drawing',
                                      'game_logic_changed': False, 'runtime_verified': False})
    print(json.dumps({'output': str(out), 'audit': audit, 'compression': checks['compression']}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--motion-set', type=Path, required=True)
    parser.add_argument('--extract', type=Path, required=True)
    args = parser.parse_args(); prepare(args.motion_set, args.extract)
