"""생성한 대표 포즈를 선택 팔레트로 정규화하고 기존 파츠/공유/압축 적합성을 조사. BIN 쓰기 없음."""
import argparse
import json
from pathlib import Path
import struct
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.repack_zero import read_inputs
from scripts.project import new_run, write_json
from scripts.discover_inputs import sha256
from scripts.extract_zero import save_image
from src.psx_player import graphics_bank, composition_frame, decode_stream, compose_indices
from src.psx_frame_edit import frame_coverage, edit_frame_indices
from src.psx_compress import encode_stream


def prepare(source, extracted, frame_number, height):
    import numpy as np
    from PIL import Image
    source = source.resolve()
    if not source.is_relative_to((ROOT/'work/ver_buki_riko/art_pilot').resolve()):
        raise ValueError('Expected preserved local generated art')
    profile, _, _, _, gfx, parts, _ = read_inputs(extracted)
    selected = json.loads((ROOT/'projects/ver_buki_riko/art_selection.json').read_text(encoding='utf-8'))
    base = ROOT/selected['indexed_png']
    if sha256(base.read_bytes()) != selected['indexed_png_sha256']:
        raise ValueError('Selected Riko art changed')
    words = struct.unpack('<16H', (base.parent/'candidate_palette.bin').read_bytes())
    colors = np.array([[(w & 31)*255//31, ((w >> 5) & 31)*255//31, ((w >> 10) & 31)*255//31]
                       for w in words[1:]], dtype=np.int32)
    bank = graphics_bank(gfx, 0); descriptor = bank['frames'][frame_number]
    decoded = decode_stream(gfx, descriptor['offset'], descriptor['limit'], descriptor['tile_count']*128)
    composition = composition_frame(parts, 0, frame_number)
    coverage, size, bounds = frame_coverage(decoded.data, descriptor['tile_count'], composition)
    if any(len(c) > 1 for c in coverage):
        raise ValueError('Sample target has overlapping parts')
    rgba = Image.open(source).convert('RGBA'); data = np.array(rgba)
    ys, xs = np.nonzero(data[:, :, 3] >= 128)
    if not len(xs):
        raise ValueError('Generated image is empty')
    bbox = (int(xs.min()), int(ys.min()), int(xs.max()+1), int(ys.max()+1))
    cropped = rgba.crop(bbox); width = round(cropped.width*height/cropped.height)
    if height <= 0 or height > size[1] or width > size[0]:
        raise ValueError('Requested sample size exceeds frame canvas')
    sampled = np.array(cropped.resize((width, height), Image.Resampling.NEAREST))
    visible = sampled[:, :, 3] >= 128
    small = np.zeros((height, width), dtype=np.uint8)
    distances = np.sum((sampled[:, :, :3][visible].astype(np.int32)[:, None]-colors[None])**2, axis=2)
    small[visible] = np.argmin(distances, axis=1)+1
    cover = np.array([bool(c) for c in coverage]).reshape(size[1], size[0])
    choices = []
    for y in range(size[1]-height+1):
        for x in range(size[0]-width+1):
            outside = int(np.sum(visible & ~cover[y:y+height, x:x+width]))
            # 게임 기준점은 고정. 후보 배치는 범위 적합 우선, 그 안에서 중앙/하단을 선호한다.
            distance = abs((x+width/2)-(-bounds[0]))+abs(y+height-size[1])
            choices.append((outside, distance, x, y))
    outside, _, x, y = min(choices)
    canvas = np.zeros((size[1], size[0]), dtype=np.uint8)
    canvas[y:y+height, x:x+width] = small
    out = new_run(ROOT, 'ver_buki_riko', 'pose_samples')
    picture = save_image(canvas.tobytes(), size, words, out/f'frame_{frame_number:03d}.png')
    picture.resize((size[0]*6, size[1]*6), Image.Resampling.NEAREST).save(out/'preview_6x.png')
    compression = None; affected = []; error = None
    if not outside:
        try:
            packed = edit_frame_indices(decoded.data, descriptor['tile_count'], composition, canvas.tobytes(), size)
            encoded = encode_stream(packed)
            if decode_stream(encoded, 0, len(encoded), len(packed)).data != packed:
                raise ValueError('Sample compression roundtrip mismatch')
            compression = {'encoded_bytes': len(encoded), 'original_bytes': decoded.end-decoded.start,
                           'fits': len(encoded) <= decoded.end-decoded.start}
            (out/'candidate.packed4').write_bytes(packed)
            (out/'candidate.compressed').write_bytes(encoded)
            for other in bank['frames']:
                if other['offset'] != descriptor['offset']:
                    continue
                c = composition_frame(parts, 0, other['index'])
                a = compose_indices(decoded.data, descriptor['tile_count'], c)[0]
                b = compose_indices(packed, descriptor['tile_count'], c)[0]
                if a != b:
                    affected.append(other['index'])
        except ValueError as exc:
            error = str(exc)
    report = {'source': str(source), 'source_sha256': sha256(source.read_bytes()),
              'original_bin_sha256': profile['source_sha256'], 'selected_reference_sha256': selected['indexed_png_sha256'],
              'bank': 0, 'frame': frame_number, 'canvas_size': size, 'bounds': bounds, 'origin': [-bounds[0], -bounds[1]],
              'generated_crop': bbox, 'sample_size': [width, height], 'placement_xy': [x, y],
              'opaque_pixels': int(np.sum(canvas != 0)), 'opaque_colors': len(set(canvas.flat)-{0}),
              'outside_existing_parts': outside, 'pixels_clipped': 0, 'compression': compression,
              'affected_shared_frames': affected, 'error': error, 'game_applied': False, 'style_approved': False,
              'placement_is_art_interpretation': True, 'animation_timing_modified': False}
    write_json(out/'report.json', report)
    print(json.dumps({'output': str(out), 'outside': outside, 'compression': compression, 'affected': affected}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--extract', type=Path, required=True)
    parser.add_argument('--frame', type=int, choices=(7, 22), required=True)
    parser.add_argument('--height', type=int, required=True)
    args = parser.parse_args()
    prepare(args.source, args.extract, args.frame, args.height)
