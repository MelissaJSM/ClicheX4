"""리코 벽 머리만 준비한다. 실제 BIN·EXE·세이브·팔레트·파츠는 쓰지 않는다."""
import argparse
from collections import defaultdict
import json
from pathlib import Path
import struct
import sys

import numpy as np
from PIL import Image, ImageDraw

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts.export_zero_consistency import SOURCES, sha, need, write
from scripts.c01_audio_build import read_disc
from scripts.prepare_riko_ui import entry, replace_entry
from scripts.overhaul_sprites_audit import render, rgba
from src.psx_player import graphics_bank, composition_frame, decode_stream, compose_indices
from src.psx_frame_edit import frame_coverage, edit_frame_set, read_indexed_png
from src.psx_compress import encode_stream
from src.psx_bank_repack import repack_graphics_bank
from src.psx_disc import file_hash

WORK=ROOT/'work/sprite_consistency_20261105/zero/riko/wall_fix'
TARGETS={0:tuple(range(38,44)),1:(50,51,53,54,56,57,59,61,63,65)}
TEMPLATE=ROOT/'work/ver_buki_riko/art_pilot/wall_v1/rear_head_indexed.png'
TEMPLATE_SHA='ee2b61b3d420177339b427b671a8ab71e221b28c8fb695846e139ce5aadfde70'
# Hand-authored semantic boundary on the authenticated old 23x19 template.
# Top-right raised glove/forearm and bottom shoulder/left arm are excluded.
HEAD_SPANS={0:(13,15),1:(8,16),2:(6,19),3:(4,20),4:(3,21),5:(2,21),6:(2,22),7:(1,22),
            8:(2,23),9:(2,23),10:(2,23),11:(3,23),12:(3,23),13:(4,23),14:(5,11),15:(6,8)}


def inputs():
    mode,stem,expected=SOURCES['riko']
    source=ROOT/'out'/mode/'ultimate_costumes_swapped_20261105_v1'/f'{stem}.bin'
    need(file_hash(source)==expected,'Latest Riko source changed')
    arc=read_disc(source,('PL01_U.ARC',))[0]['PL01_U.ARC']
    need(file_hash(TEMPLATE)==TEMPLATE_SHA,'Old binding template changed')
    head=np.array(Image.open(TEMPLATE),np.uint8)
    need(head.shape==(19,23),'Old template geometry changed')
    mask=np.zeros_like(head,bool)
    for y,(x0,x1) in HEAD_SPANS.items():
        mask[y,x0:x1]=head[y,x0:x1]>0
    return source,expected,arc,head,mask


def indexed(path,array,palette):
    image=Image.fromarray(array,'P')
    colors=[int(v) for word in palette for v in ((word&31)*255//31,(word>>5&31)*255//31,(word>>10&31)*255//31)]
    image.putpalette(colors+[0]*(768-len(colors)));image.save(path,transparency=0)


def bindings(arc,head,mask):
    g,c=entry(arc,2),entry(arc,3);rows=[]
    for b,numbers in TARGETS.items():
        bank=graphics_bank(g,b);sharing=defaultdict(list)
        for f in bank['frames']:
            sharing[f['offset']].append(f['index'])
        for n in numbers:
            world,_=render(arc,b,0 if b==0 else 5,n)
            region=world[100:175,105:210]
            windows=np.lib.stride_tricks.sliding_window_view(region,head.shape)
            matches=np.argwhere(np.all(windows[:,:,head>0]==head[head>0],axis=-1))
            need(len(matches)==1,f'Old full template is not unique: {b}/{n}')
            y,x=matches[0];x=int(x+105-160);y=int(y+100-160)
            f=bank['frames'][n];raw=decode_stream(g,f['offset'],f['limit'],f['tile_count']*128).data
            cp=composition_frame(c,0 if b==0 else 5,n);cov,size,bb=frame_coverage(raw,f['tile_count'],cp)
            coverage=np.zeros((384,384),bool)
            coverage[bb[1]+160:bb[3]+160,bb[0]+160:bb[2]+160]=np.array([bool(v)for v in cov]).reshape(size[1],size[0])
            ownership=np.zeros_like(coverage);ownership[y+160:y+179,x+160:x+183]=mask
            reserved=(world>0)&~ownership
            extension=coverage[y+156:y+179,x+160:x+183]
            rows.append({'id':f'b{b}_{n:03}','bank':b,'parts_bank':0 if b==0 else 5,'frame':n,
                         'old_template_anchor':[x,y],'old_semantic_mask_pixels':int(mask.sum()),
                         'head_hair_bbox_world':[x+1,y+2,x+23,y+16],
                         'stream_offset':f['offset'],'shared_refs':sharing[f['offset']],
                         'tile_count':f['tile_count'],'part_count':len(cp['parts']),
                         'composition_bounds':bb,'four_rows_extended_rectangle_uncovered':
                         [[int(xx+x),int(yy+y-4)]for yy,xx in np.argwhere(~extension)],
                         'world':world,'owned_mask':ownership,'protected_mask':reserved,'coverage':coverage})
    return rows


def analyze():
    source,expected,arc,head,mask=inputs();rows=bindings(arc,head,mask)
    out=WORK/'binding';need(not out.exists(),'Binding already exists');out.mkdir(parents=True)
    pal=struct.unpack_from('<16H',entry(arc,9))
    pure=np.where(mask,head,0).astype(np.uint8);indexed(out/'old_head_only.png',pure,pal)
    Image.fromarray(mask.astype(np.uint8)*255,'L').save(out/'old_head_mask.png')
    original=rgba(head,pal);owned=rgba(pure,pal);protected=rgba(np.where(mask,0,head).astype(np.uint8),pal)
    board=Image.new('RGB',(23*12*3,19*12+28),'#263442');draw=ImageDraw.Draw(board)
    for k,(name,im) in enumerate([('old template = head + limbs',original),('editable head only',owned),('protected glove / shoulder',protected)]):
        im=im.resize((23*12,19*12),Image.Resampling.NEAREST);board.paste(im,(k*23*12,28),im);draw.text((k*23*12+3,4),name,fill='white')
    board.save(out/'semantic_mask_review.png')
    report=[]
    for r in rows:
        prefix=r['id'];world=r.pop('world');ownership=r.pop('owned_mask');protected=r.pop('protected_mask');coverage=r.pop('coverage')
        for label,a in [('head_mask',ownership),('protected_mask',protected),('coverage',coverage)]:
            Image.fromarray(a.astype(np.uint8)*255,'L').save(out/f'{prefix}_{label}.png')
        indexed(out/f'{prefix}_before.png',world,pal)
        r['masks']={label:f'{prefix}_{label}.png'for label in ('head_mask','protected_mask','coverage')};report.append(r)
    record={'source_bin':source.relative_to(ROOT).as_posix(),'source_sha256':expected,'source_arc_sha256':sha(arc),
            'old_template':TEMPLATE.relative_to(ROOT).as_posix(),'old_template_sha256':TEMPLATE_SHA,
            'old_template_size':[23,19],'semantic_head_mask_pixels':int(mask.sum()),
            'semantic_head_rows':[''.join(format(int(v),'x')for v in row)for row in pure],
            'semantic_mask_is_manual':True,'head_excludes_glove_forearm_shoulder':True,
            'new_head_input':{'format':'PNG P indexed, original 16-color order, transparency0',
                              'suggested_size':[23,22],'offset_from_old_template':[0,-3],
                              'anchor_contract':'No rescale. Caller supplies dx/dy explicitly; fixed non-head opaque pixels win occlusion.',
                              'four_pixel_extension_limit':'b0_38 y=-33 lacks existing coverage; keep this row transparent or use top=-32.'},
            'frames':report,'game_modified':False,'runtime_verified':False}
    write(out/'binding.json',record)
    print(json.dumps({'binding':str(out/'binding.json'),'mask_pixels':int(mask.sum()),'frames':len(rows)}))


def prepare(head_path,head_sha,dx,dy,output):
    source,expected,arc,head,mask=inputs();rows=bindings(arc,head,mask)
    output=output.resolve();head_path=head_path.resolve()
    need(output.is_relative_to(WORK.resolve()) and not output.exists(),'Fresh wall_fix output required')
    need(head_path.is_relative_to(WORK.resolve()) and head_path.is_file(),'Head input outside wall_fix')
    need(file_hash(head_path)==head_sha,'Head SHA mismatch')
    pal=struct.unpack_from('<16H',entry(arc,9));pixels,size=read_indexed_png(head_path,pal)
    need(1<=size[0]<=32 and 1<=size[1]<=28,'Unexpected head geometry')
    newhead=np.frombuffer(pixels,np.uint8).reshape(size[1],size[0]);targets={};proof=[]
    for r in rows:
        before=r['world'];oldmask=r['owned_mask'];protected=r['protected_mask'];coverage=r['coverage']
        x,y=r['old_template_anchor'];x+=dx;y+=dy
        new=np.zeros_like(before);new[160+y:160+y+size[1],160+x:160+x+size[0]]=newhead
        occluded=(new>0)&protected
        visible=(new>0)&~protected
        need(not np.any(visible&~coverage),f'New head escapes original parts: {r["id"]}')
        target=before.copy();target[oldmask]=0;target[visible]=new[visible]
        need(np.array_equal(target[protected],before[protected]),'Protected body pixels changed')
        need(not np.any((target!=before)&~(oldmask|visible)),'Mutation escaped head masks')
        targets[r['bank'],r['frame']]=target
        proof.append({'id':r['id'],'old_template_anchor':r['old_template_anchor'],'new_head_anchor':[x,y],
                      'changed_pixels':int(np.count_nonzero(target!=before)),
                      'new_head_pixels_occluded_by_original_limbs':int(occluded.sum()),
                      'occluded_world_pixels':[[int(xx-160),int(yy-160)]for yy,xx in np.argwhere(occluded)],
                      'protected_body_pixels_exact':True,'outside_coverage':0})
    g,c=entry(arc,2),entry(arc,3);ng=g;packing=[]
    for b,numbers in TARGETS.items():
        bank=graphics_bank(g,b);groups=defaultdict(list)
        for f in bank['frames']:
            groups[f['offset']].append(f['index'])
        encoded={};group_report=[]
        for start,refs in groups.items():
            selected=[n for n in refs if (b,n)in targets]
            if not selected:
                continue
            f=bank['frames'][refs[0]];raw=decode_stream(g,start,f['limit'],f['tile_count']*128).data
            edits=[];preserved=[]
            for n in refs:
                cp=composition_frame(c,0 if b==0 else 5,n)
                if (b,n)not in targets:
                    preserved.append(cp);continue
                _,sz,bb,_=compose_indices(raw,f['tile_count'],cp)
                target=targets[b,n][160+bb[1]:160+bb[3],160+bb[0]:160+bb[2]]
                edits.append((cp,target.tobytes(),sz))
            rebuilt=edit_frame_set(raw,f['tile_count'],edits,preserved_compositions=preserved)
            if rebuilt==raw:
                continue
            code=encode_stream(rebuilt)
            for n in refs:
                encoded[n]=code
            group_report.append({'refs':refs,'edited_body_refs':selected,'preserved_effect_refs':[n for n in refs if n not in selected],
                                 'tile_count':f['tile_count'],'encoded_bytes':len(code)})
        if encoded:
            ng,packed=repack_graphics_bank(ng,b,encoded)
            packing.append({'bank':b,'groups':group_report,'repack':packed})
    changed=replace_entry(arc,2,ng)
    checked=[]
    for b in (0,1):
        oldbank=graphics_bank(g,b);newbank=graphics_bank(ng,b)
        for old,new in zip(oldbank['frames'],newbank['frames']):
            n=old['index'];need(new['tile_count']==old['tile_count']<=32,'Tile count/buffer changed')
            oldraw=decode_stream(g,old['offset'],old['limit'],old['tile_count']*128).data
            newraw=decode_stream(ng,new['offset'],new['limit'],new['tile_count']*128).data
            if b==1 and 42<=n<=49:
                need(oldraw==newraw,'Partial VRAM stream changed');continue
            before,_=render(arc,b,0 if b==0 else 5,n);after,_=render(changed,b,0 if b==0 else 5,n)
            want=targets.get((b,n),before)
            need(np.array_equal(after,want),f'Final displayed pixels differ: {b}/{n}')
            checked.append({'bank':b,'frame':n,'target':(b,n)in targets,'unchanged':np.array_equal(before,after)})
    need(replace_entry(changed,2,g)==arc,'Non-graphics entry changed')
    output.mkdir(parents=True)
    (output/'PL01_U.ARC').write_bytes(changed)
    board=Image.new('RGB',(4*320,4*280+26),'#263442');draw=ImageDraw.Draw(board)
    for i,r in enumerate(rows):
        ident=r['id'];before=r['world'];after=targets[r['bank'],r['frame']]
        indexed(output/f'{ident}.png',after,pal)
        for col,array in enumerate((before,after)):
            im=rgba(array,pal).crop((120,120,184,184)).resize((160,160),Image.Resampling.NEAREST)
            board.paste(im,(i%4*320+col*160,i//4*280+40),im)
        draw.text((i%4*320+5,i//4*280+8),ident+' before / proposed',fill='white')
    board.save(output/'comparison.png')
    report={'source_bin':source.relative_to(ROOT).as_posix(),'source_sha256':expected,'source_arc_sha256':sha(arc),
            'resource':(output/'PL01_U.ARC').relative_to(ROOT).as_posix(),'after_sha256':sha(changed),
            'head_file':head_path.relative_to(ROOT).as_posix(),'head_sha256':head_sha,
            'head_size':size,'head_offset':[dx,dy],'frames':proof,'packing':packing,
            'validation':{'all_444_references_checked':True,'full_display_checks':len(checked),
                          'partial8_bytes_preserved':True,'parts_palette_timing_sound_static_byte_identical':True,
                          'other_displayed_frames_identical':True,'max_tiles':32},
            'game_bin_written':False,'runtime_verified':False,'visual_acceptance_required':True}
    write(output/'proposal.json',report)
    need(file_hash(source)==expected,'Source BIN changed')
    print(json.dumps({'output':str(output),'arc_sha256':sha(changed),'changed_frame_pixels':
                      sum(x['changed_pixels']for x in proof),'banks_repacked':len(packing)}))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=('analyze','prepare'))
    p.add_argument('--head',type=Path);p.add_argument('--head-sha256');p.add_argument('--dx',type=int,default=0)
    p.add_argument('--dy',type=int,default=-3);p.add_argument('--output',type=Path);a=p.parse_args()
    if a.action=='analyze':
        analyze()
    else:
        need(a.head and a.head_sha256 and a.output,'Head, explicit SHA and fresh output required')
        prepare(a.head,a.head_sha256,a.dx,a.dy,a.output)
