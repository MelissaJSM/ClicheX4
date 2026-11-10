"""생성한 감은 눈의 승인 기준안 정렬 결과에서 눈 영역만 취하는 기술 후처리."""
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
from src.psx_frame_edit import read_indexed_png


def prepare(blink_png):
    from PIL import Image
    selection = json.loads((ROOT/'projects/ver_buki_riko/art_selection.json').read_text(encoding='utf-8'))
    source = checked_path(ROOT, selection['indexed_png'], ROOT/'out/ver_buki_riko')
    if sha256(source.read_bytes()) != selection['indexed_png_sha256']:
        raise ValueError('Selected art hash changed')
    blink_png = blink_png.resolve()
    if not blink_png.is_relative_to((ROOT/'out/ver_buki_riko').resolve()):
        raise ValueError('Expected a normalized local generated variant')
    palette = struct.unpack('<16H', (source.parent/'candidate_palette.bin').read_bytes())
    original, size = read_indexed_png(source, palette)
    blink, blink_size = read_indexed_png(blink_png, palette)
    if size != (56, 48) or blink_size != size:
        raise ValueError('Expected aligned 56 by 48 idle frames')
    # 생성 결과의 눈만 취한다. 새 그림을 코드로 그리지 않고 ROI 밖의 생성 변형을 버린다.
    rectangle = (17, 11, 20, 14)
    edited = bytearray(original)
    for y in range(rectangle[1], rectangle[3]):
        for x in range(rectangle[0], rectangle[2]):
            i = y*size[0]+x
            if not original[i] or not blink[i]:
                raise ValueError('Eye crop unexpectedly includes transparency')
            edited[i] = blink[i]
    changed = [[i % size[0], i // size[0], a, b]
               for i, (a, b) in enumerate(zip(original, edited)) if a != b]
    if not changed:
        raise ValueError('Generated eye crop did not change any pixels')
    out = new_run(ROOT, 'ver_buki_riko', 'riko_idle_frames')
    frames = {}
    for n in (0, 1, 2, 146, 147, 148):
        # 0/1/2의 왼쪽 머리 타일이 공유되므로 독립 타일을 가진 148에서만 눈을 바꾼다.
        pixels = bytes(edited) if n == 148 else original
        frames[n] = save_image(pixels, size, palette, out/f'idle_{n:03d}.png')
    sequence = [0, 146, 147, 148, 0, 146, 147, 148, 0, 1, 2, 1]
    ticks = [21, 12, 42, 12, 54, 12, 42, 12, 24, 3, 3, 3]
    durations = [round(t*1000/60/10)*10 for t in ticks]
    # GIF는 60 tick/s 가정의 검수용 미리보기. 실제 게임 실행 증거는 별도로 기록한다.
    for scale in (1, 3):
        images = [frames[n].resize((size[0]*scale, size[1]*scale), Image.Resampling.NEAREST) for n in sequence]
        images[0].save(out/f'idle_preview_{scale}x.gif', save_all=True, append_images=images[1:],
                       duration=durations, loop=0, transparency=0, disposal=2, optimize=False)
    report = {'selected_png': str(source), 'selected_sha256': sha256(source.read_bytes()),
              'generated_normalized_png': str(blink_png), 'generated_normalized_sha256': sha256(blink_png.read_bytes()),
              'eye_crop_xyxy': rectangle, 'changed_pixels_in_frame148': changed,
              'all_other_frames_exact_selected_art': True, 'frame147_preserved': True,
              'sequence': sequence, 'original_duration_ticks': ticks, 'preview_assumed_ticks_per_second': 60,
              'preview_is_runtime_evidence': False, 'style_review_pending': True,
              'limitation': 'Blink uses frame 148; original blink frames 1/2 share the Riko eye tile with frame 0.'}
    write_json(out/'report.json', report)
    print(json.dumps({'output': str(out), 'changed_pixels': len(changed)}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--blink-png', type=Path, required=True)
    prepare(parser.parse_args().blink_png)
