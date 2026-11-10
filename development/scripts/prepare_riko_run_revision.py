"""Riko 이동 수정: 공통 기준점과 좌우 다리의 같은 위상 길이를 검증한다."""
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
from scripts.build_riko_idle import patch_frames, JUMP_FRAMES
from src.psx_player import graphics_bank, composition_frame, decode_stream
from src.psx_frame_edit import frame_coverage, read_indexed_png

KEY_SLOTS = ((7,), (8, 9), (10,), (11, 12), (13,),
             (14,), (15, 16), (17,), (18, 19), (20,))
TICKS = (2, 3, 2, 2, 2, 3, 2) * 2
HEIGHTS = (47, 46, 47, 48, 41) * 2
PHASES = ((.5,.5),(.25,.5),(.75,.5),(.5,.25),(.5,.75),
          (.25,.25),(.75,.75),(.25,.75),(.75,.25))


def prepare(extracted, art_dir, previous):
    import numpy as np
    from PIL import Image, ImageDraw
    art_dir = art_dir.resolve(); previous = previous.resolve()
    for path in (art_dir, previous):
        if not path.is_relative_to((ROOT/'work/ver_buki_riko').resolve()):
            raise ValueError('Expected first-project working inputs')
    profile, _, arc, gfx_meta, gfx, parts, _ = read_inputs(extracted)
    selected = json.loads((ROOT/'projects/ver_buki_riko/art_selection.json').read_text(encoding='utf-8'))
    reference = ROOT/selected['indexed_png']
    if sha256(reference.read_bytes()) != selected['indexed_png_sha256']:
        raise ValueError('Approved reference changed')
    palette = reference.with_name('candidate_palette.bin').read_bytes()
    words = struct.unpack('<16H', palette)
    colors = np.array([[(w&31)*255//31, ((w>>5)&31)*255//31, ((w>>10)&31)*255//31]
                       for w in words[1:]], dtype=np.int32)
    prior = json.loads(previous.read_text(encoding='utf-8'))
    if prior['source_sha256'] != profile['source_sha256'] or prior['palette_sha256'] != sha256(palette):
        raise ValueError('Prior source or palette mismatch')
    if set(prior['frames']) != {str(n) for n in JUMP_FRAMES}:
        raise ValueError('Expected verified jump inputs')
    frames = {}; copied = {}
    for key, record in prior['frames'].items():
        path = (previous.parent/record['file']).resolve()
        if not path.is_relative_to(previous.parent) or sha256(path.read_bytes()) != record['sha256']:
            raise ValueError('Prior frame changed or escaped directory')
        frames[int(key)] = read_indexed_png(path, words); copied[int(key)] = path

    sources = {}
    def load_crops(name, count):
        path = art_dir/name
        sources[name] = {'path':str(path), 'sha256':sha256(path.read_bytes())}
        im = Image.open(path).convert('RGBA'); found = components(im,count)
        if count == 8:
            found.sort(key=lambda q:(q[0][1] > im.height//2,q[0][0]))
            if [q[0][1] > im.height//2 for q in found] != [False]*4+[True]*4:
                raise ValueError('Expected 4 by 2 sprite sheet')
        return [(name, box, crop) for box,crop in found]

    keys = load_crops('paired8_clean.png',8)
    keys[1] = load_crops('paired8_down.png',8)[1]
    keys[3] = load_crops('paired8_legorder.png',8)[3]
    keys[5] = load_crops('down_far.png',1)[0]
    flights = load_crops('flight2_compact.png',2)
    keys = keys[:4]+[flights[0]]+keys[4:]+[flights[1]]
    start = load_crops('start2.png',2)[0]
    bank = graphics_bank(gfx,0); geometry = {}; audit = {}; key_audit = {}
    for n in (3,4,*range(7,21)):
        descriptor = bank['frames'][n]; comp = composition_frame(parts,0,n)
        raw = decode_stream(gfx,descriptor['offset'],descriptor['limit'],descriptor['tile_count']*128).data
        coverage,size,bounds = frame_coverage(raw,descriptor['tile_count'],comp)
        if any(len(c)>1 for c in coverage) or any(p['flags'] for p in comp['parts']):
            raise ValueError('Unmodeled overlaps or part flags')
        safe = np.array([bool(c) for c in coverage]).reshape(size[1],size[0])
        for p in comp['parts']:
            if p['tile']%16 == 0:
                safe[p['y']-bounds[1]:p['y']-bounds[1]+16,p['x']-bounds[0]] = False
        world = np.zeros((96,96),dtype=bool)
        world[48+bounds[1]:48+bounds[3],48+bounds[0]:48+bounds[2]] = safe
        geometry[n] = (size,bounds,world)

    normalized = {}
    def sample_and_fit(key, source, ns, height, target_eye, world_top=None):
        name,box,crop = source
        width = round(crop.width*height/crop.height*.85)
        common = np.logical_and.reduce([geometry[n][2] for n in ns])
        world_y = 24-height if world_top is None else world_top
        source_pixels = np.array(crop)
        options = []; rejected = []
        for priority,(px,py) in enumerate(PHASES):
            xs = ((np.arange(width)+px)*crop.width/width).astype(int)
            ys = ((np.arange(height)+py)*crop.height/height).astype(int)
            rgba = source_pixels[ys[:,None],xs[None,:]]; visible = rgba[:,:,3]>=128
            rgb = rgba[:,:,:3].astype(np.int32)
            indexed = np.zeros((height,width),dtype=np.uint8)
            indexed[visible] = np.argmin(((rgb[visible,None]-colors[None])**2).sum(axis=2),axis=1)+1
            purple = (rgb[:,:,0]>rgb[:,:,1]+20)&(rgb[:,:,2]>rgb[:,:,0]+10)
            eyes_y,eyes_x = np.nonzero((indexed==5)&purple&(np.indices(indexed.shape)[0]<height*.45))
            if not len(eyes_x): continue
            eye_x = float(np.mean(eyes_x)); eye_y = float(np.mean(eyes_y))
            for x in range(-32,min(16,49-width)):
                error = abs(x+eye_x-target_eye)
                if error > .51: continue
                bad = np.argwhere(visible&~common[48+world_y:48+world_y+height,48+x:48+x+width])
                if len(bad):
                    rejected.append({'phase':[px,py],'x':x,'bad_pixels':bad.tolist()});continue
                options.append((priority+error, x, indexed, (px,py), eye_x, eye_y))
        if not options: raise ValueError(f'Key {key} cannot fit: {rejected}')
        _,x,indexed,phase,eye_x,eye_y = min(options,key=lambda q:q[0])
        normalized[key] = (indexed,x,world_y)
        key_audit[key] = {'source':name,'sheet_bbox':box,'sample_size':[width,height],
                          'aspect_x':.85,'nearest_sample_phase':phase,'world_origin':[x,world_y],
                          'eye_world':[x+eye_x,world_y+eye_y], 'frames':list(ns)}
        for n in ns:
            size,bounds,_ = geometry[n]
            canvas = np.zeros((size[1],size[0]),dtype=np.uint8)
            cx,cy = x-bounds[0],world_y-bounds[1]
            if min(cx,cy)<0 or cx+width>size[0] or cy+height>size[1]:
                raise ValueError('Whole sampled canvas outside composition bounds')
            canvas[cy:cy+height,cx:cx+width] = indexed
            frames[n] = (canvas.tobytes(),size)
            audit[n] = {'key':key,'bounds':bounds,'placement_xy':[cx,cy],
                        'world_bottom':world_y+height-1,'opaque_pixels':int(np.count_nonzero(indexed)),
                        'dark_pixels':int(np.sum(indexed==1)), 'dark_ratio':float(np.sum(indexed==1)/np.count_nonzero(indexed)),
                        'outside_parts':0,'reflected_u0_pixels':0,'pixels_clipped':0,'separate_body_slicing':False}

    for k,(source,ns,height) in enumerate(zip(keys,KEY_SLOTS,HEIGHTS)):
        sample_and_fit(str(k),source,ns,height,-6,-24 if k in (4,9) else None)
    sample_and_fit('start',start,(3,),47,-2)
    sample_and_fit('entry_contact',keys[0],(4,),47,-2)
    # 양다리 위상별 표시 시간도 같아야 한다. 그림을 옮겨 타일 제약을 숨기지 않는다.
    phase_ticks = [sum(TICKS[n-7] for n in ns) for ns in KEY_SLOTS]
    if phase_ticks[:5] != phase_ticks[5:] or sum(phase_ticks[:5]) != 16:
        raise ValueError('Unequal half-cycle timing')
    _,checks = patch_frames(arc,gfx_meta,gfx,parts,frames,palette)
    out = new_run(ROOT,'ver_buki_riko','run_revision_frames'); records = {}; pictures = {}
    for n,frame in sorted(frames.items()):
        filename=f'frame_{n:03d}.png'
        if n in copied: shutil.copyfile(copied[n],out/filename)
        else: save_image(*frame,words,out/filename)
        records[str(n)]={'file':filename,'sha256':sha256((out/filename).read_bytes())}
        pictures[n]=Image.open(out/filename).convert('RGBA')
    aligned={}
    for n in (3,4,*range(7,21)):
        tile=Image.new('RGBA',(64,72),(42,45,54,255));b=audit[n]['bounds']
        tile.alpha_composite(pictures[n],(32+b[0],40+b[1]));aligned[n]=tile
    board=Image.new('RGBA',(256*4,288*4),(42,45,54,255));draw=ImageDraw.Draw(board)
    for j,n in enumerate((3,4,*range(7,21))):
        x,y=j%4*256,j//4*288
        board.alpha_composite(aligned[n].resize((256,288),Image.Resampling.NEAREST),(x,y))
        draw.text((x+4,y+4),str(n),fill='white');draw.line((x,y+256,x+255,y+256),fill=(90,95,110))
    board.save(out/'run_sheet_4x.png')
    elapsed=0;durations=[]
    for tick in TICKS:
        before=round(elapsed*100/60)*10;elapsed+=tick;durations.append(round(elapsed*100/60)*10-before)
    for zoom in (1,4):
        seq=[aligned[n].resize((64*zoom,72*zoom),Image.Resampling.NEAREST).convert('RGB') for n in range(7,21)]
        seq[0].save(out/f'run_preview_{zoom}x.gif',save_all=True,append_images=seq[1:],duration=durations,loop=0,disposal=2)
    manifest={'source_sha256':profile['source_sha256'],'palette_sha256':sha256(palette),
              'scope':'jump_and_run_v1','frames':records,'previous_manifest':str(previous),
              'previous_manifest_sha256':sha256(previous.read_bytes()),'sources':sources,
              'keys':key_audit,'run_audit':audit,'checks':checks,'run_ticks':list(TICKS),
              'phase_ticks_per_half':phase_ticks[:5],'unique_cycle_keys':10,
              'uniform_world_eye_target_x':-6,'ground_foot_baseline':23,'flight_bottom':16,
              'runtime_verified':False,'art_review_pending':True,'game_logic_changed':False,
              'preview_timing':'Cumulative 60Hz ticks rounded to GIF centiseconds; game timing untouched'}
    write_json(out/'motion_set.json',manifest)
    print(json.dumps({'output':str(out),'keys':key_audit,'phase_ticks':phase_ticks,
                      'compression':checks['compression']}))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--extract',type=Path,required=True)
    parser.add_argument('--art-dir',type=Path,required=True)
    parser.add_argument('--previous-motion',type=Path,required=True)
    args=parser.parse_args();prepare(args.extract,args.art_dir,args.previous_motion)
