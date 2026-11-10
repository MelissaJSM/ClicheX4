"""이전 1차 호흡 재현용: 분리된 중간 자세는 사용자 거부. 현재는 prepare_riko_idle_coherent 사용."""
import argparse
import json
from pathlib import Path
import struct
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.project import new_run, write_json, checked_path
from scripts.discover_inputs import sha256
from scripts.extract_zero import save_image
from scripts.repack_zero import read_inputs
from scripts.build_riko_idle import patch_idle
from src.psx_frame_edit import read_indexed_png


def prepare(generated, blink, extracted):
    import numpy as np
    from PIL import Image
    generated = generated.resolve()
    if not generated.is_relative_to((ROOT/'work/ver_buki_riko/idle_breathing').resolve()):
        raise ValueError('Expected preserved generated breathing asset')
    selection = json.loads((ROOT/'projects/ver_buki_riko/art_selection.json').read_text(encoding='utf-8'))
    source = checked_path(ROOT, selection['indexed_png'], ROOT/'out/ver_buki_riko')
    if sha256(source.read_bytes()) != selection['indexed_png_sha256']:
        raise ValueError('Selected v2 hash changed')
    palette = (source.parent/'candidate_palette.bin').read_bytes()
    words = struct.unpack('<16H', palette)
    pixels, size = read_indexed_png(source, words)
    blink_pixels, blink_size = read_indexed_png(blink.resolve(), words)
    if size != (56, 48) or blink_size != size:
        raise ValueError('Expected aligned idle canvases')
    original = np.frombuffer(pixels, dtype=np.uint8).reshape(48, 56)
    colors = np.array([[(w&31)*255//31, ((w>>5)&31)*255//31, ((w>>10)&31)*255//31]
                       for w in words[1:]], dtype=np.int32)
    image = Image.open(generated).convert('RGBA')
    rgba = np.array(image.resize(size, Image.Resampling.NEAREST))
    opaque = rgba[:, :, 3] >= 128
    normalized = np.zeros((48, 56), dtype=np.uint8)
    distances = np.sum((rgba[:, :, :3][opaque].astype(np.int32)[:, None]-colors[None])**2, axis=2)
    normalized[opaque] = np.argmin(distances, axis=1)+1
    # 생성본은 상체가 3px 내려왔다. (-1,-2) 정렬 후 무릎/망토 연결 띠만 취한다.
    # 얼굴·상체는 선택된 v2 픽셀을 1px 이동, 부츠 하단/발은 원래 좌표 그대로 보존한다.
    relaxed = original.copy()
    relaxed[:33] = 0
    relaxed[1:33] = original[:32]
    relaxed[33:39, :55] = normalized[35:41, 1:56]
    relaxed[33:39, 55] = 0
    transition = relaxed.copy()
    transition[:30] = original[:30]
    closing = transition.copy()
    blink_array = np.frombuffer(blink_pixels, dtype=np.uint8).reshape(48, 56)
    closing[11:14, 17:20] = blink_array[11:14, 17:20]
    arrays = {0: relaxed, 1: relaxed, 2: relaxed, 146: transition, 147: original, 148: closing}
    frames = {n: (a.tobytes(), size) for n, a in arrays.items()}
    profile, _, arc, gfx_meta, gfx, parts, _ = read_inputs(extracted)
    _, checks = patch_idle(arc, gfx_meta, gfx, parts, frames, palette)
    for n, a in arrays.items():
        if not np.array_equal(a[39:], original[39:]):
            raise ValueError(f'Foot anchor changed in {n}')
    out = new_run(ROOT, 'ver_buki_riko', 'breathing_frames')
    images = {n: save_image(*frames[n], words, out/f'idle_{n:03d}.png') for n in arrays}
    save_image(normalized.tobytes(), size, words, out/'generated_normalized.png')
    sequence = [0, 146, 147, 148, 0, 146, 147, 148, 0, 1, 2, 1]
    ticks = [21, 12, 42, 12, 54, 12, 42, 12, 24, 3, 3, 3]
    durations = [round(t*1000/60/10)*10 for t in ticks]
    for scale in (1, 4, 8):
        pictures = [images[n].resize((56*scale, 48*scale), Image.Resampling.NEAREST) for n in sequence]
        pictures[0].save(out/f'idle_preview_{scale}x.gif', save_all=True, append_images=pictures[1:],
                         duration=durations, loop=0, transparency=0, disposal=2, optimize=False)
    board = Image.new('RGBA', (56*4*4, 48*4), (38, 41, 50, 255))
    for i, n in enumerate((0, 146, 147, 148)):
        picture = images[n].convert('RGBA').resize((224, 192), Image.Resampling.NEAREST)
        board.alpha_composite(picture, (i*224, 0))
    board.save(out/'breathing_4x.png')
    report = {'selected_png': str(source), 'selected_sha256': sha256(source.read_bytes()),
              'source_sha256': profile['source_sha256'], 'generated_source': str(generated),
              'generated_sha256': sha256(generated.read_bytes()), 'generated_size': image.size,
              'normalized_size': size, 'alpha_threshold': 128, 'generated_alignment_xy': [-1, -2],
              'generated_region_output_xyxy': [0, 33, 55, 39],
              'fixed_lower_boot_rows': [39, 48], 'upper_body_translation_xy': [0, 1],
              'transition_preserved_upper_rows': [0, 30], 'blink_source': str(blink.resolve()),
              'blink_sha256': sha256(blink.read_bytes()), 'blink_roi_xyxy': [17, 11, 20, 14],
              'sequence': sequence, 'original_duration_ticks': ticks,
              'preview_assumed_ticks_per_second': 60, 'preview_is_runtime_evidence': False,
              'frame147_exact_selected': frames[147][0] == pixels,
              'foot_pixels_preserved_all_frames': True,
              'changed_pixels_vs_selected': {n: int(np.sum(a != original)) for n, a in arrays.items()},
              'frame_hashes': {n: sha256((out/f'idle_{n:03d}.png').read_bytes()) for n in arrays},
              'checks': checks, 'style_review_pending': True, 'game_applied': False,
              'art_interpretation': '1px upper-body breath; generated joint/cape strip, immutable v2 face and feet',
              'limitation': '0/1/2 share the eye tile; blink remains on 148. GIF timing assumes 60 ticks/s.'}
    write_json(out/'report.json', report)
    print(json.dumps({'output': str(out), 'compression': checks['compression'],
                      'changed_pixels': report['changed_pixels_vs_selected']}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--generated', type=Path, required=True)
    parser.add_argument('--blink', type=Path, required=True)
    parser.add_argument('--extract', type=Path, required=True)
    args = parser.parse_args()
    prepare(args.generated, args.blink, args.extract)
