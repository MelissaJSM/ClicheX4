"""기존 생성 시트의 이동 16포즈를 원래 타일의 양방향 공통 범위에 배치한다."""
import argparse
import json
from pathlib import Path
import shutil
import struct
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.project import new_run, write_json
from scripts.discover_inputs import sha256
from scripts.repack_zero import read_inputs
from scripts.extract_zero import save_image
from scripts.prepare_riko_jump import components
from scripts.build_riko_idle import patch_frames
from src.psx_player import graphics_bank, composition_frame, decode_stream
from src.psx_frame_edit import frame_coverage, read_indexed_png

RUN_FRAMES = (3, 4, *range(7, 21))


def prepare(extracted, sheet, previous, scale, compact=None, contact=None):
    import numpy as np
    from PIL import Image, ImageDraw
    sheet = sheet.resolve(); previous = previous.resolve()
    for path in (sheet, previous, *([compact.resolve()] if compact else []), *([contact.resolve()] if contact else [])):
        if not path.is_relative_to((ROOT/'work/ver_buki_riko').resolve()):
            raise ValueError('Expected first-project working inputs')
    if not .14 <= scale <= .17:
        raise ValueError('Unexpected scale for reviewed run sheet')
    profile, _, arc, gfx_meta, gfx, parts, _ = read_inputs(extracted)
    selected = json.loads((ROOT/'projects/ver_buki_riko/art_selection.json').read_text(encoding='utf-8'))
    reference = ROOT/selected['indexed_png']
    if sha256(reference.read_bytes()) != selected['indexed_png_sha256']:
        raise ValueError('Approved reference changed')
    palette = (reference.parent/'candidate_palette.bin').read_bytes()
    words = struct.unpack('<16H', palette)
    colors = np.array([[(w&31)*255//31, ((w>>5)&31)*255//31, ((w>>10)&31)*255//31]
                       for w in words[1:]], dtype=np.int32)
    prior = json.loads(previous.read_text(encoding='utf-8'))
    if prior['source_sha256'] != profile['source_sha256'] or prior['palette_sha256'] != sha256(palette):
        raise ValueError('Prior source or palette mismatch')
    if set(prior['frames']) != {str(n) for n in (5, 6, *range(21, 35))}:
        raise ValueError('Expected complete verified jump inputs')
    frames = {}; records = {}; copied = {}
    for key, record in prior['frames'].items():
        path = (previous.parent/record['file']).resolve()
        if not path.is_relative_to(previous.parent) or sha256(path.read_bytes()) != record['sha256']:
            raise ValueError('Prior frame changed or escaped directory')
        frames[int(key)] = read_indexed_png(path, words); copied[int(key)] = path
    rgba = Image.open(sheet).convert('RGBA'); crops = components(rgba, 16)
    crops.sort(key=lambda pair: (int((pair[0][1]+pair[0][3])/2*4/rgba.height), pair[0][0]))
    if [int((box[1]+box[3])/2*4/rgba.height) for box, _ in crops] != [r for r in range(4) for _ in range(4)]:
        raise ValueError('Expected four rows of four separate connected sprites')
    overrides = dict(zip((9,13,16,17,19,20), components(Image.open(compact).convert('RGBA'),6))) if compact else {}
    contacts = dict(zip((9,16), components(Image.open(contact).convert('RGBA'),2))) if contact else {}
    bank = graphics_bank(gfx, 0); audit = {}; pictures = {}; failures = []
    for n, (box, crop) in zip(RUN_FRAMES, crops):
        current_scale = .105 if n in overrides else scale
        if n in overrides: box, crop = overrides[n]
        if n in contacts: box, crop = contacts[n]; current_scale = .062
        w, h = round(crop.width*current_scale*.90), round(crop.height*current_scale)
        source_pixels = np.array(crop)
        # 최근접 표본의 원점을 기록한다. 작은 눈 색이 표본 격자 사이로 사라지면
        # 한 픽셀보다 작은 공통 원점 이동으로 보존하며 새 픽셀을 그리지 않는다.
        for phase_x, phase_y in ((.5,.5),(.25,.5),(.75,.5),(.5,.25),(.5,.75),(.25,.25),(.75,.75),(.25,.75),(.75,.25)):
            xs = ((np.arange(w)+phase_x)*crop.width/w).astype(int)
            ys = ((np.arange(h)+phase_y)*crop.height/h).astype(int)
            sampled = source_pixels[ys[:,None],xs[None,:]]; visible = sampled[:,:,3] >= 128
            small = np.zeros((h,w), dtype=np.uint8)
            small[visible] = np.argmin(np.sum((sampled[:,:,:3][visible].astype(np.int32)[:,None]-colors[None])**2, axis=2), axis=1)+1
            rgb = sampled[:,:,:3].astype(int)
            purple = (rgb[:,:,0] > rgb[:,:,1]+20) & (rgb[:,:,2] > rgb[:,:,0]+10)
            eyes_y, eyes_x = np.nonzero((small == 5) & purple & (np.indices(small.shape)[0] < h*.45))
            if len(eyes_x): break
        else: raise ValueError(f'Purple eye lost in frame {n}')
        f = bank['frames'][n]; comp = composition_frame(parts, 0, n)
        raw = decode_stream(gfx, f['offset'], f['limit'], f['tile_count']*128).data
        coverage, size, bounds = frame_coverage(raw, f['tile_count'], comp)
        if any(len(c)>1 for c in coverage) or any(p['flags'] for p in comp['parts']):
            raise ValueError('Unmodeled overlap or part flags')
        safe = np.array([bool(c) for c in coverage]).reshape(size[1], size[0])
        # 원작 반전 quad가 U=0의 첫 열을 표시하지 않으므로 양방향 공통 범위를 쓴다.
        for p in comp['parts']:
            if p['tile'] % 16 == 0:
                x, y = p['x']-bounds[0], p['y']-bounds[1]
                safe[y:y+16,x] = False
        eye_target = -1 if n in (3,4) else -8
        ideal_x = eye_target-bounds[0]-float(np.mean(eyes_x))
        ideal_y = -24-bounds[1]
        choices = []
        for y in range(size[1]-h+1):
            for x in range(size[0]-w+1):
                if not np.any(visible & ~safe[y:y+h,x:x+w]):
                    choices.append((abs(x-ideal_x)+4*abs(y-ideal_y), x, y))
        if not choices:
            best=min((int(np.sum(visible & ~safe[yy:yy+h,xx:xx+w])),xx,yy)
                     for yy in range(size[1]-h+1) for xx in range(size[0]-w+1))
            count,xx,yy=best
            bad=np.argwhere(visible & ~safe[yy:yy+h,xx:xx+w])
            print(json.dumps({'failed_frame':n,'size':[w,h],'best_xy':[xx,yy],'uncovered':count,'bad_xy':[[int(a+xx),int(b+yy)] for b,a in bad]}))
            failures.append(n)
            continue
        _, x, y = min(choices)
        if n not in (3,4) and abs(x+bounds[0]+float(np.mean(eyes_x))+8)>2.5:
            raise ValueError(f'Frame {n}: coverage fit would introduce head jitter')
        canvas = np.zeros((size[1],size[0]), dtype=np.uint8); canvas[y:y+h,x:x+w] = small
        frames[n] = (canvas.tobytes(), size)
        audit[n] = {'sheet_bbox': box, 'source_sheet': str(contact if n in contacts else compact if n in overrides else sheet),
                    'sheet_scale_y': current_scale, 'common_aspect_x': .90, 'sample_size': [w,h], 'placement_xy': [x,y],
                    'nearest_sample_phase_xy': [phase_x,phase_y],
                    'bounds': bounds, 'world_top': y+bounds[1], 'world_bottom': y+bounds[1]+h-1,
                    'eye_world_mean': [x+bounds[0]+float(np.mean(eyes_x)),y+bounds[1]+float(np.mean(eyes_y))],
                    'opaque_pixels': int(visible.sum()), 'purple_eye_pixels': len(eyes_x),
                    'outside_parts': 0, 'reflected_u0_pixels': 0, 'pixels_clipped': 0,
                    'separate_body_slicing': False}
    if failures: raise ValueError(f'Frames {failures}: full silhouettes cannot fit both orientations at scale {scale}')
    _, checks = patch_frames(arc, gfx_meta, gfx, parts, frames, palette)
    out = new_run(ROOT, 'ver_buki_riko', 'run_frames')
    for n, frame in sorted(frames.items()):
        name = f'frame_{n:03d}.png'
        if n in copied: shutil.copyfile(copied[n], out/name)
        else: save_image(*frame, words, out/name)
        records[str(n)] = {'file': name, 'sha256': sha256((out/name).read_bytes())}
        pictures[n] = Image.open(out/name).convert('RGBA')
    board = Image.new('RGBA',(64*4*4,72*4*4),(42,45,54,255)); draw = ImageDraw.Draw(board)
    aligned = {}
    for j,n in enumerate(RUN_FRAMES):
        tile = Image.new('RGBA',(64,72),(42,45,54,255)); b=audit[n]['bounds']
        tile.alpha_composite(pictures[n],(32+b[0],40+b[1])); aligned[n]=tile
        x,y=j%4*256,j//4*288
        board.alpha_composite(tile.resize((256,288),Image.Resampling.NEAREST),(x,y))
        draw.text((x+4,y+4),str(n),fill='white');draw.line((x,y+256,x+255,y+256),fill=(90,95,110))
    board.save(out/'run_sheet_4x.png')
    ticks=[2,3,2,2,2,3,2,2,3,2,2,2,3,2]
    # GIF milliseconds cannot represent exact 60Hz ticks; round cumulative timestamps, record limitation.
    elapsed=0; durations=[]
    for tick in ticks:
        before=round(elapsed*100/60)*10;elapsed+=tick;durations.append(round(elapsed*100/60)*10-before)
    for zoom in (1,4):
        seq=[aligned[n].resize((64*zoom,72*zoom),Image.Resampling.NEAREST).convert('RGB') for n in range(7,21)]
        seq[0].save(out/f'run_preview_{zoom}x.gif',save_all=True,append_images=seq[1:],duration=durations,loop=0,disposal=2)
    write_json(out/'motion_set.json',{'source_sha256':profile['source_sha256'],'palette_sha256':sha256(palette),
        'scope':'jump_and_run_v1','frames':records,'previous_manifest':str(previous),'previous_manifest_sha256':sha256(previous.read_bytes()),
        'generated_sheet':str(sheet),'generated_sheet_sha256':sha256(sheet.read_bytes()),'run_audit':audit,'checks':checks,
        'compact_sheet':str(compact) if compact else None,'compact_sheet_sha256':sha256(compact.read_bytes()) if compact else None,
        'contact_sheet':str(contact) if contact else None,'contact_sheet_sha256':sha256(contact.read_bytes()) if contact else None,
        'runtime_verified':False,'art_review_pending':True,'game_logic_changed':False,
        'run_ticks':ticks,'preview_timing':'GIF rounded cumulative 60Hz ticks to centiseconds; game sequence untouched'})
    print(json.dumps({'output':str(out),'compression':checks['compression'],'audit':audit}))


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--extract',type=Path,required=True);parser.add_argument('--sheet',type=Path,required=True)
    parser.add_argument('--previous-motion',type=Path,required=True);parser.add_argument('--scale',type=float,default=.157)
    parser.add_argument('--compact',type=Path)
    parser.add_argument('--contact',type=Path)
    args=parser.parse_args();prepare(args.extract,args.sheet,args.previous_motion,args.scale,args.compact,args.contact)




