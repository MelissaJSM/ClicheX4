"""생성된 앞쪽 종아리/부츠를 기존 전신에 등록하고 이동 반복 경계를 검증한다."""
import argparse
import json
from pathlib import Path
import shutil
import struct
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts.project import new_run,write_json
from scripts.discover_inputs import sha256
from scripts.repack_zero import read_inputs
from scripts.extract_zero import save_image
from scripts.build_riko_idle import patch_frames,validate_motion_scope
from src.psx_player import graphics_bank,composition_frame,decode_stream
from src.psx_frame_edit import frame_coverage,read_indexed_png

# destination, existing whole-body anchor, generated sheet cell, sheet, sampling phase, registration x.
EDITS=((12,11,0,'midswing_v1.png',.5,1),(13,14,0,'precontact_v1.png',0.,1),
       (19,18,1,'midswing_v1.png',.5,1),(20,7,1,'precontact_v1.png',.5,2))
TICKS=(2,3,2,2,2,3,2)*2


def prepare(extracted,previous,art_dir):
    import numpy as np
    from PIL import Image,ImageDraw,ImageFont
    previous=previous.resolve();art_dir=art_dir.resolve()
    for path in (previous,art_dir):
        if not path.is_relative_to((ROOT/'work/ver_buki_riko').resolve()):
            raise ValueError('Unexpected first-project input')
    profile,_,arc,gfx_meta,gfx,parts,_=read_inputs(extracted)
    selection=json.loads((ROOT/'projects/ver_buki_riko/art_selection.json').read_text(encoding='utf-8'))
    reference=ROOT/selection['indexed_png']
    if sha256(reference.read_bytes())!=selection['indexed_png_sha256']:raise ValueError('Approved idle changed')
    palette=reference.with_name('candidate_palette.bin').read_bytes();words=struct.unpack('<16H',palette)
    colors=np.array([[(w&31)*255//31,((w>>5)&31)*255//31,((w>>10)&31)*255//31] for w in words[1:]],dtype=np.int32)
    prior=json.loads(previous.read_text(encoding='utf-8'));validate_motion_scope(prior)
    if prior['scope']!='jump_and_run_v1' or prior['source_sha256']!=profile['source_sha256'] or prior['palette_sha256']!=sha256(palette):
        raise ValueError('Previous source, palette or scope mismatch')
    frames={};paths={}
    for key,record in prior['frames'].items():
        path=(previous.parent/record['file']).resolve()
        if not path.is_relative_to(previous.parent) or sha256(path.read_bytes())!=record['sha256']:
            raise ValueError('Previous frame changed or escaped input directory')
        frames[int(key)]=read_indexed_png(path,words);paths[int(key)]=path
    bank=graphics_bank(gfx,0);geometry={};before={}
    for n in range(7,21):
        f=bank['frames'][n];comp=composition_frame(parts,0,n)
        raw=decode_stream(gfx,f['offset'],f['limit'],f['tile_count']*128).data
        coverage,size,bounds=frame_coverage(raw,f['tile_count'],comp)
        if any(len(c)>1 for c in coverage) or any(p['flags'] for p in comp['parts']):
            raise ValueError('Unmodeled composition')
        safe=np.array([bool(c) for c in coverage]).reshape(size[1],size[0])
        for p in comp['parts']:
            if p['tile']%16==0:safe[p['y']-bounds[1]:p['y']-bounds[1]+16,p['x']-bounds[0]]=False
        geometry[n]=(size,bounds,safe)
        world=np.zeros((72,96),dtype=np.uint8)
        world[40+bounds[1]:40+bounds[3],48+bounds[0]:48+bounds[2]]=np.frombuffer(frames[n][0],dtype=np.uint8).reshape(size[1],size[0])
        before[n]=world
    after={n:a.copy() for n,a in before.items()};sources={};edits={}
    edit_region=np.zeros((72,96),dtype=bool);edit_region[48:64,32:48]=True
    for n,anchor,cell,name,phase_x,offset_x in EDITS:
        source=art_dir/name
        sources[name]={'sha256':sha256(source.read_bytes()),'path':str(source)}
        image=Image.open(source).convert('RGBA')
        # Full reference canvas sampling retains placement/scale. No per-pose bbox scaling.
        pixels=np.array(image)
        xs=((np.arange(128)+phase_x)*image.width/128).astype(int)
        ys=((np.arange(72)+.5)*image.height/72).astype(int)
        sampled=pixels[ys[:,None],xs[None,:]][:,cell*64:(cell+1)*64]
        visible=sampled[:,:,3]>=128;indices=np.zeros((72,64),dtype=np.uint8)
        indices[visible]=np.argmin(((sampled[:,:,:3][visible].astype(np.int32)[:,None]-colors[None])**2).sum(2),axis=1)+1
        # Image generation supplied the replacement lower leg. Keep the anchor's head, waist,
        # pelvis and rear leg exact; register only the selected foreground leg tile region.
        world=before[anchor].copy()
        world[48:64,32:48]=indices[48:64,16-offset_x:32-offset_x]
        if np.any(world[~edit_region]!=before[anchor][~edit_region]):raise AssertionError('Unselected body region changed')
        size,bounds,safe=geometry[n]
        canvas=world[40+bounds[1]:40+bounds[3],48+bounds[0]:48+bounds[2]]
        if np.any((canvas!=0)&~safe):raise ValueError(f'Frame {n}: outside part or reflected U=0 edge')
        restored=np.zeros_like(world);restored[40+bounds[1]:40+bounds[3],48+bounds[0]:48+bounds[2]]=canvas
        if np.any(restored!=world):raise ValueError('World silhouette escapes native canvas')
        frames[n]=(canvas.tobytes(),size);after[n]=world
        edits[n]={'anchor_frame':anchor,'source':name,'cell':cell,'logical_sheet_size':[128,72],
                  'nearest_sample_phase':[phase_x,.5],'lower_leg_registration_dx':offset_x,
                  'world_edit_rectangle':[-16,8,0,24],'outside_selected_region_changed_pixels':0,
                  'outside_parts':0,'reflected_u0_pixels':0,'silhouette_clipping':0}

    def transitions(worlds):
        rows=[]
        for n in range(7,21):
            nxt=n+1 if n<20 else 7;a,b=worlds[n],worlds[nxt]
            front_a=np.nonzero(a[48:64,32:48]);front_b=np.nonzero(b[48:64,32:48])
            rows.append({'from':n,'to':nxt,'changed_pixels':int(np.sum(a!=b)),
                         'upper_changed_pixels':int(np.sum(a[:48]!=b[:48])),
                         'outside_front_leg_changed_pixels':int(np.sum(a[~edit_region]!=b[~edit_region])),
                         'silhouette_xor':int(np.sum((a!=0)^(b!=0))),
                         'front_bottom_delta':int(front_b[0].max()-front_a[0].max()),
                         'front_toe_x_delta':int(front_b[1].min()-front_a[1].min())})
        return rows
    metrics={'before':transitions(before),'after':transitions(after)}
    for n in (13,20):
        row=next(r for r in metrics['after'] if r['from']==n)
        if row['outside_front_leg_changed_pixels'] or not 0<row['changed_pixels']<=128 or abs(row['front_bottom_delta'])>2 or abs(row['front_toe_x_delta'])>5:
            raise ValueError(f'Contact boundary discontinuity: {row}')
    for sequence in ((12,13,14),(19,20,7)):
        heights=[int(np.nonzero(after[n][48:64,32:48])[0].max())+8 for n in sequence]
        if heights!=[17,21,23]:raise ValueError(f'Unexpected foot descent: {sequence}, {heights}')
    _,checks=patch_frames(arc,gfx_meta,gfx,parts,frames,palette)
    out=new_run(ROOT,'ver_buki_riko','run_loop_frames');records={}
    for n,frame in sorted(frames.items()):
        filename=f'frame_{n:03d}.png'
        if n not in edits:shutil.copyfile(paths[n],out/filename)
        else:save_image(*frame,words,out/filename)
        records[str(n)]={'file':filename,'sha256':sha256((out/filename).read_bytes())}
    font=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',16)
    def picture(indices,zoom=4):
        crop=indices[:,16:80];visible=crop!=0;rgba=np.zeros((*crop.shape,4),dtype=np.uint8)
        rgba[visible,:3]=colors[crop[visible]-1];rgba[visible,3]=255
        im=Image.new('RGBA',(64,72),(42,45,54,255));im.alpha_composite(Image.fromarray(rgba))
        return im.resize((64*zoom,72*zoom),Image.Resampling.NEAREST)
    boundary=Image.new('RGBA',(6*256,4*320),(42,45,54,255));draw=ImageDraw.Draw(boundary)
    for row,(data,seq,label) in enumerate(((before,[11,12,13,14,15,16],'이전'),(after,[11,12,13,14,15,16],'수정'),
                                          (before,[18,19,20,7,8,9],'이전'),(after,[18,19,20,7,8,9],'수정'))):
        for j,n in enumerate(seq):
            boundary.alpha_composite(picture(data[n]),(j*256,row*320+32));draw.text((j*256+4,row*320+4),f'{label} {n}',font=font,fill='white')
    boundary.save(out/'loop_boundaries_4x.png')
    for zoom in (1,4):
        for slow in (False,True):
            elapsed=0;seq=[];durations=[]
            for n,tick in zip(range(7,21),TICKS):
                seq.append(picture(after[n],zoom).convert('RGB'))
                prior_ms=round(elapsed*100/60)*10;elapsed+=tick
                duration=round(elapsed*100/60)*10-prior_ms;durations.append(duration*(3 if slow else 1))
            seq[0].save(out/f'loop_{zoom}x{"_slow" if slow else ""}.gif',save_all=True,append_images=seq[1:],duration=durations,loop=0,disposal=2)
    comparison=[];elapsed=0;durations=[]
    for n,tick in zip(range(7,21),TICKS):
        board=Image.new('RGBA',(512,320),(42,45,54,255));draw=ImageDraw.Draw(board)
        for j,(label,data) in enumerate((('수정 전',before),('수정 후',after))):
            board.alpha_composite(picture(data[n]),(j*256,32));draw.text((j*256+4,5),label,font=font,fill='white')
        comparison.append(board.convert('RGB'));prior_ms=round(elapsed*100/60)*10;elapsed+=tick;durations.append(round(elapsed*100/60)*10-prior_ms)
    comparison[0].save(out/'loop_before_after.gif',save_all=True,append_images=comparison[1:],duration=durations,loop=0,disposal=2)
    write_json(out/'loop_metrics.json',metrics)
    write_json(out/'motion_set.json',{'source_sha256':profile['source_sha256'],'palette_sha256':sha256(palette),
        'scope':'jump_and_run_v1','frames':records,'previous_manifest':str(previous),
        'previous_manifest_sha256':sha256(previous.read_bytes()),'sources':sources,'edits':edits,'checks':checks,
        'run_ticks':list(TICKS),'changed_frames':[12,13,19,20],'unchanged_motion_png_count':28,
        'boundary_pairs':[[13,14],[20,7]],'runtime_verified':False,'art_review_pending':True,
        'game_logic_changed':False,'preview_timing':'GIF centiseconds approximate cumulative 60Hz timing; game ticks untouched'})
    print(json.dumps({'output':str(out),'boundaries':[r for r in metrics['after'] if r['from'] in (13,20)],
                      'compression':[c for c in checks['compression'] if any(n in edits for n in c['frames'])]}))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--extract',type=Path,required=True)
    p.add_argument('--previous-motion',type=Path,required=True);p.add_argument('--art-dir',type=Path,required=True)
    args=p.parse_args();prepare(args.extract,args.previous_motion,args.art_dir)
