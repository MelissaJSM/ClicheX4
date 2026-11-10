"""기존 완성 PNG의 대기 프레임 배정을 고쳐 허리에서 갈라지는 중간 자세를 제거."""
import argparse
import json
from pathlib import Path
import shutil
import struct
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.project import new_run, write_json, checked_path, digest
from scripts.repack_zero import read_inputs
from scripts.build_riko_idle import patch_idle
from src.psx_frame_edit import read_indexed_png


def phase_metrics(pixels, reference, size):
    # 목 아래~허리/골반 상단. 눈 깜빡임과 무릎/망토 형태는 이 검사와 구분한다.
    width, height = size
    if size != (56, 48):
        raise ValueError('Expected native idle canvas')
    differences = {}
    for dy in (0, 1):
        differences[dy] = sum(pixels[(y+dy)*width+x] != reference[y*width+x]
                              for y in range(18, 32) for x in range(12, 37))
    return {'differences_by_vertical_shift': differences,
            'coherent_shifts': [dy for dy, count in differences.items() if count == 0]}


def prepare(previous, blink_dir, extracted):
    from PIL import Image, ImageDraw, ImageFont
    previous = previous.resolve(); blink_dir = blink_dir.resolve()
    allowed = (ROOT/'work/ver_buki_riko').resolve()
    if not previous.is_relative_to(allowed) or not blink_dir.is_relative_to(allowed):
        raise ValueError('Expected local version-specific frame inputs')
    old_report = json.loads((previous/'report.json').read_text(encoding='utf-8'))
    selection = json.loads((ROOT/'projects/ver_buki_riko/art_selection.json').read_text(encoding='utf-8'))
    source = checked_path(ROOT, selection['indexed_png'], ROOT/'out/ver_buki_riko')
    if digest(source) != selection['indexed_png_sha256']:
        raise ValueError('Selected v2 changed')
    palette = (source.parent/'candidate_palette.bin').read_bytes()
    words = struct.unpack('<16H', palette)
    reference, size = read_indexed_png(source, words)
    # 모든 출력은 이미 보존된 세 PNG 중 하나의 바이트 동일 사본이다. 새 픽셀 편집 없음.
    low = previous/'idle_000.png'; blink = blink_dir/'idle_148.png'
    if digest(low) != old_report['frame_hashes']['0']:
        raise ValueError('Lowered pose changed')
    blink_pixels, blink_size = read_indexed_png(blink, words)
    if blink_size != size:
        raise ValueError('Blink canvas mismatch')
    changed_eye = [i for i, (a, b) in enumerate(zip(reference, blink_pixels)) if a != b]
    if len(changed_eye) != 8 or any(not (17 <= i%56 < 20 and 11 <= i//56 < 14) for i in changed_eye):
        raise ValueError('Expected the preserved eight-pixel blink only')
    sources = {0: low, 1: low, 2: low, 146: low, 147: source, 148: blink}
    frames = {n: read_indexed_png(path, words) for n, path in sources.items()}
    phases = {}; old_phases = {}
    for n, (pixels, frame_size) in frames.items():
        if frame_size != size:
            raise ValueError('Idle canvas mismatch')
        metrics = phase_metrics(pixels, reference, size)
        if len(metrics['coherent_shifts']) != 1:
            raise ValueError('Torso and pelvis are not a single translated pose')
        if pixels[39*56:] != reference[39*56:]:
            raise ValueError('Boot/foot anchor changed')
        phases[n] = metrics
        prior = previous/f'idle_{n:03d}.png'
        if digest(prior) != old_report['frame_hashes'][str(n)]:
            raise ValueError('Previous animation changed')
        old_phases[n] = phase_metrics(read_indexed_png(prior, words)[0], reference, size)
    profile, _, arc, gfx_meta, gfx, parts, _ = read_inputs(extracted)
    if old_report['source_sha256'] != profile['source_sha256']:
        raise ValueError('Game revision changed')
    _, checks = patch_idle(arc, gfx_meta, gfx, parts, frames, palette)
    out = new_run(ROOT, 'ver_buki_riko', 'coherent_idle_frames')
    for n, path in sources.items():
        shutil.copyfile(path, out/f'idle_{n:03d}.png')
        if digest(path) != digest(out/f'idle_{n:03d}.png'):
            raise ValueError('Output differs from preserved source PNG')
    sequence = old_report['sequence']; ticks = old_report['original_duration_ticks']
    if sequence != [0,146,147,148,0,146,147,148,0,1,2,1] or ticks != [21,12,42,12,54,12,42,12,24,3,3,3]:
        raise ValueError('Original idle timeline changed')
    duration = [round(t*1000/60/10)*10 for t in ticks]
    for scale in (1, 4):
        pictures = [Image.open(out/f'idle_{n:03d}.png').resize((56*scale,48*scale),Image.Resampling.NEAREST) for n in sequence]
        pictures[0].save(out/f'idle_preview_{scale}x.gif',save_all=True,append_images=pictures[1:],
                         duration=duration,loop=0,transparency=0,disposal=2,optimize=False)
    font = ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',16)
    pictures = []
    for n in sequence:
        board = Image.new('RGB',(480,228),(38,41,50)); draw = ImageDraw.Draw(board)
        draw.text((12,4),'이전 — 허리 분리',font=font,fill='white')
        draw.text((252,4),'수정 — 몸통 연결',font=font,fill='white')
        for x, folder in ((8,previous),(248,out)):
            image = Image.open(folder/f'idle_{n:03d}.png').convert('RGBA').resize((224,192),Image.Resampling.NEAREST)
            board.paste(image,(x,28),image); draw.line((x,220,x+224,220),fill=(94,101,119))
        pictures.append(board)
    pictures[0].save(out/'waist_before_after_4x.gif',save_all=True,append_images=pictures[1:],
                     duration=duration,loop=0,optimize=False)
    board = Image.new('RGB',(224*4,192),(38,41,50))
    for col, n in enumerate((0,146,147,148)):
        image = Image.open(out/f'idle_{n:03d}.png').convert('RGBA').resize((224,192),Image.Resampling.NEAREST)
        board.paste(image,(224*col,0),image)
    board.save(out/'coherent_4x.png')
    report = {'source_sha256':profile['source_sha256'],'selected_sha256':selection['indexed_png_sha256'],
              'previous_frames':str(previous),'preserved_blink_frames':str(blink_dir),
              'method':'Reassign byte-identical existing pose PNGs; no new image generation or pixel drawing',
              'source_pngs':{n:{'path':str(path),'sha256':digest(path)} for n,path in sources.items()},
              'frame_hashes':{n:digest(out/f'idle_{n:03d}.png') for n in sources},
              'body_phase_metrics':phases,'rejected_previous_phase_metrics':old_phases,
              'torso_roi_xyxy':[12,18,37,32],'frame147_preserved':True,'boots_and_feet_preserved':True,
              'changed_idle_references':[n for n in sources if digest(out/f'idle_{n:03d}.png') != digest(previous/f'idle_{n:03d}.png')],
              'sequence':sequence,'original_duration_ticks':ticks,'preview_assumed_ticks_per_second':60,
              'preview_is_runtime_evidence':False,'checks':checks,'game_applied':False,
              'user_review_pending':True,'previous_split_pose_rejected_by_user':True}
    write_json(out/'report.json',report)
    print(json.dumps({'output':str(out),'changed_idle_references':report['changed_idle_references'],
                      'phases':{n:m['coherent_shifts'] for n,m in phases.items()},'compression':checks['compression']}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--previous',type=Path,required=True)
    parser.add_argument('--blink-dir',type=Path,required=True)
    parser.add_argument('--extract',type=Path,required=True)
    args = parser.parse_args(); prepare(args.previous,args.blink_dir,args.extract)
