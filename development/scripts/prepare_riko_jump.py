"""생성 시트의 알파 연결 성분을 분리하고 원래 조립 구조에 점프 연결 프레임을 준비한다."""
import argparse
from collections import deque
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
from src.psx_player import graphics_bank, composition_frame, decode_stream
from src.psx_frame_edit import frame_coverage, edit_frame_set, read_indexed_png
from src.psx_compress import encode_stream


def components(rgba, expected_count=6):
    """배경 RGB를 추측하지 않고 alpha >= 128의 연결 성분만 분리한다."""
    import numpy as np
    from PIL import Image
    data = np.array(rgba); mask = data[:, :, 3] >= 128; groups = []
    while mask.any():
        y, x = np.argwhere(mask)[0]; queue = deque([(int(y), int(x))]); mask[y, x] = False; points = []
        while queue:
            y, x = queue.popleft(); points.append((x, y))
            for yy, xx in ((y-1,x),(y+1,x),(y,x-1),(y,x+1)):
                if 0 <= yy < mask.shape[0] and 0 <= xx < mask.shape[1] and mask[yy,xx]:
                    mask[yy,xx] = False; queue.append((yy,xx))
        if len(points) < 100:
            raise ValueError('Unexpected disconnected artwork; review instead of discarding pixels')
        xs, ys = zip(*points); box = [min(xs), min(ys), max(xs)+1, max(ys)+1]
        crop = data[box[1]:box[3], box[0]:box[2]].copy(); crop[:,:,3] = 0
        for x, y in points:
            crop[y-box[1],x-box[0],3] = 255
        groups.append((box, Image.fromarray(crop)))
    if len(groups) != expected_count:
        raise ValueError(f'Expected exactly {expected_count} separated sheet poses')
    groups.sort(key=lambda pair: (pair[0][1] > rgba.height//2 if expected_count == 6 else False, pair[0][0]))
    return groups


def prepare(extracted, sheet, rise, scale, compact=None):
    import numpy as np
    from PIL import Image, ImageDraw, ImageFont
    for path in (sheet, rise, *([compact] if compact else [])):
        if not path.resolve().is_relative_to((ROOT/'work/ver_buki_riko').resolve()):
            raise ValueError('Expected first-project working art')
    if not 0.08 <= scale <= 0.12:
        raise ValueError('Unexpected native art scale')
    profile, _, _, _, gfx, parts, _ = read_inputs(extracted)
    selected = json.loads((ROOT/'projects/ver_buki_riko/art_selection.json').read_text(encoding='utf-8'))
    reference = ROOT/selected['indexed_png']
    if sha256(reference.read_bytes()) != selected['indexed_png_sha256']:
        raise ValueError('Approved art changed')
    palette_bytes = (reference.parent/'candidate_palette.bin').read_bytes(); words = struct.unpack('<16H', palette_bytes)
    colors = np.array([[(w & 31)*255//31, ((w >> 5) & 31)*255//31, ((w >> 10) & 31)*255//31] for w in words[1:]], dtype=np.int32)
    crops = components(Image.open(sheet).convert('RGBA')); normalized = []
    compact_crops = components(Image.open(compact).convert('RGBA'),2) if compact else []
    if compact:
        crops[3] = compact_crops[0]; crops[4] = compact_crops[1]
    out = new_run(ROOT, 'ver_buki_riko', 'jump_frames')
    for i, (box, crop) in enumerate(crops):
        crop.save(out/f'source_pose_{i}.png')
        current_scale = 0.055 if compact and i in (3,4) else scale
        size = (round(crop.width*current_scale), round(crop.height*current_scale))
        rgba = np.array(crop.resize(size, Image.Resampling.NEAREST)); visible = rgba[:,:,3] >= 128
        indices = np.zeros((size[1], size[0]), dtype=np.uint8)
        distances = np.sum((rgba[:,:,:3][visible].astype(np.int32)[:,None]-colors[None])**2, axis=2)
        indices[visible] = np.argmin(distances, axis=1)+1
        normalized.append(indices)
    bank = graphics_bank(gfx, 0)
    # 고유 키 포즈의 원래 시간표 내 재사용. 14장 모두 다른 그림이라고 보고하지 않는다.
    mapping = {21:0, 24:1, 25:2, 26:2, 27:3, 28:3, 29:3, 30:3, 31:3, 32:3, 33:4, 34:5}
    frame_numbers = [5,6,*range(21,35)]
    images = {}; records = {}; groups = {}
    for n in frame_numbers:
        descriptor = bank['frames'][n]
        decoded = decode_stream(gfx, descriptor['offset'], descriptor['limit'], descriptor['tile_count']*128)
        comp = composition_frame(parts,0,n); coverage, size, bounds = frame_coverage(decoded.data, descriptor['tile_count'], comp)
        if n in (5,6):
            indices, actual_size = read_indexed_png(reference, words)
            if actual_size != size: raise ValueError('Settle reference canvas changed')
            placement = None; source = 'approved_idle_reference'
        elif n in (22,23):
            indices, actual_size = read_indexed_png(rise, words)
            if actual_size != size: raise ValueError('Rise sample canvas changed')
            placement = None; source = 'existing_rise_sample'
        else:
            small = normalized[mapping[n]]; h,w = small.shape; visible = small != 0
            cover = np.array([len(c) == 1 for c in coverage]).reshape(size[1],size[0])
            ideal_x = -bounds[0]-round(w*0.4)
            ideal_y = 24-bounds[1]-h
            choices = []
            for y in range(size[1]-h+1):
                for x in range(size[0]-w+1):
                    if not np.any(visible & ~cover[y:y+h,x:x+w]):
                        choices.append((4*abs(y-ideal_y)+abs(x-ideal_x),x,y))
            if not choices: raise ValueError(f'Frame {n}: generated pose does not fit; no clipping performed')
            _,x,y = min(choices)
            canvas = np.zeros((size[1],size[0]),dtype=np.uint8); canvas[y:y+h,x:x+w] = small
            indices = canvas.tobytes(); placement = [x,y]; source = mapping[n]
        images[n] = (indices,size)
        save_image(indices,size,words,out/f'frame_{n:03d}.png')
        records[str(n)] = {'file':f'frame_{n:03d}.png','sha256':sha256((out/f'frame_{n:03d}.png').read_bytes()),
                           'source_pose':source,'placement_xy':placement,'canvas_size':size,'bounds':bounds,
                           'opaque_pixels':sum(bool(p) for p in indices),'violet_pixels':indices.count(5),'outside_pixels':0}
        groups.setdefault(descriptor['offset'],[]).append(n)
    checks = []
    for offset, numbers in groups.items():
        descriptor = bank['frames'][numbers[0]]
        decoded = decode_stream(gfx,offset,descriptor['limit'],descriptor['tile_count']*128)
        edits = [(composition_frame(parts,0,n),*images[n]) for n in numbers]
        packed = edit_frame_set(decoded.data,descriptor['tile_count'],edits)
        encoded = encode_stream(packed)
        checks.append({'frames':numbers,'encoded_bytes':len(encoded),'budget':decoded.end-offset,'fits':len(encoded)<=decoded.end-offset})
    font = ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',16)
    board = Image.new('RGB',(8*192,2*310+40),(30,33,40)); draw = ImageDraw.Draw(board)
    draw.text((8,6),'Riko 점프·낙하·착지 / 3배 확대 / 정적 조립 검토',font=font,fill='white')
    for i,n in enumerate([*range(21,35),5,6]):
        pic = Image.open(out/f'frame_{n:03d}.png').convert('RGBA'); x=i%8*192;y=i//8*310+40
        draw.text((x+6,y+4),f'frame {n}',font=font,fill='white')
        pic=pic.resize((pic.width*3,pic.height*3),Image.Resampling.NEAREST)
        board.paste(pic,(x+3,y+25),pic)
    board.save(out/'review_3x.png')
    report={'source_sha256':profile['source_sha256'],'palette_sha256':sha256(palette_bytes),'frames':records,
            'sheet':str(sheet.resolve()),'sheet_sha256':sha256(sheet.read_bytes()),'rise_sample':str(rise.resolve()),
            'rise_sample_sha256':sha256(rise.read_bytes()),'scale':scale,'alpha_threshold':128,
            'compact_source':str(compact.resolve()) if compact else None,
            'compact_sha256':sha256(compact.read_bytes()) if compact else None,'compact_scale':0.055 if compact else None,
            'sheet_pose_boxes':[box for box,_ in crops],'compression':checks,'all_fit':all(c['fits'] for c in checks),
            'shared_frame_edits_consistent':True,'pixels_clipped':0,'game_applied':False,
            'unique_native_poses':len(set(p for p,s in images.values())),
            'limitations':['Repeated pose keys retain original sequence/timing; fine cloth motion is unfinished.',
                           'Frame 22 and 23 use identical rise art to respect shared tiles.']}
    write_json(out/'motion_set.json',report)
    print(json.dumps({'output':str(out),'compression':checks,'all_fit':report['all_fit']}))


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--extract',type=Path,required=True);parser.add_argument('--sheet',type=Path,required=True)
    parser.add_argument('--rise',type=Path,required=True);parser.add_argument('--scale',type=float,default=0.1)
    parser.add_argument('--compact',type=Path)
    args=parser.parse_args();prepare(args.extract,args.sheet,args.rise,args.scale,args.compact)
