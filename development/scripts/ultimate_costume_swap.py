"""기존 수영복/재킷 픽셀로 Ultimate 표시 교환의 특수 동작 자원을 준비한다."""
import argparse
import json
from pathlib import Path
import struct
import sys

import numpy as np
from PIL import Image
from scipy.ndimage import binary_dilation, binary_fill_holes, label

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.c01_audio_build import read_disc, require
from scripts.project import digest
from scripts.prepare_riko_ui import entry, replace_entry
from scripts.overhaul_sprites_audit import render, rgba, board, sha
from scripts.overhaul_sprites_costume_pack import resize_tile_storage, repack_variable
from scripts.prepare_shibuki_ultimate_production import pack_shared, repack_parts, records
from src.psx_player import graphics_bank, composition_frame, decode_stream, bank_offsets
from src.psx_sprite_batch import canvas_from_parts
from src.psx_ui_atlas import local_composition
from src.psx_compress import encode_stream

WORK = ROOT/'work/ultimate_costume_swap_20261105/core'
SOURCES = {
    'ver_buki_riko': ('black_monochrome_riko_20261105_v1','shibuki_riko',
        '852813890c3c9f8e0394026f8c243f6c323f1a9c0f4e1941eaa920b85bdecc4e'),
    'ver_rin_nana': ('black_red_rin_20261105_v1','rin_nana',
        'aca6d7839ad1956ea837b07d1105a7609817cd30fd0e6ceffe13e6dd611ad6fe'),
}
FRAMES = tuple(range(217,231))
AIR = {221:39,223:37,225:45,227:47,229:41}
CUT = {221:85,223:86,225:85,227:87,229:85}
SIZE = (256,160)

def save_json(path, value):
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n','utf8')

def layer(arc, bank, frame):
    a,_ = render(arc,0,bank,frame)
    return a[80:240,80:336].copy()

def image(arc, base, overlay):
    words = struct.unpack_from('<48H',entry(arc,9))
    result = rgba(base,words)
    result.alpha_composite(rgba(overlay,words[16:32]))
    return result

def shifted(a, dx, dy):
    out = np.zeros_like(a)
    h,w = a.shape
    out[max(0,dy):min(h,h+dy),max(0,dx):min(w,w+dx)] = a[max(0,-dy):min(h,h-dy),max(0,-dx):min(w,w-dx)]
    require(np.count_nonzero(out) == np.count_nonzero(a), 'Shift clips approved pixels')
    return out

def source_body(arc, n):
    a = layer(arc,0,n)
    labs,_ = label(a>0,np.ones((3,3),bool))
    counts = np.bincount(labs.ravel());counts[0] = 0
    mask = labs == int(counts.argmax())
    result = np.where(mask,a,0).astype(np.uint8)
    return result, {'source_frame':n,'retained_pixels':int(mask.sum()),
                    'separate_native_dust_pixels_excluded':int(np.count_nonzero(a)-mask.sum())}

def targets(project, arc):
    base, over, proof = {}, {}, []
    for n, reused in AIR.items():
        cut = CUT[n]
        for f,s in ((n,reused),(n+1,reused+1)):
            original_base, original_over = layer(arc,0,f),layer(arc,5,f)
            a = layer(arc,0,s); a[cut:] = 0
            b = original_over.copy(); b[:cut] = 0
            # Existing foot/shoe pixels retain their original armor CLUT.
            # Any exposed lower base pixel also stays in its original CLUT.
            lower = original_base.copy();lower[:cut] = 0
            exposed = (lower>0)&(b==0);a[exposed] = lower[exposed]
            require(np.array_equal(a[:cut],layer(arc,0,s)[:cut]),'Accepted swimsuit upper changed')
            require(image(arc,a,b).tobytes()[cut*SIZE[0]*4:] ==
                    image(arc,original_base,original_over).tobytes()[cut*SIZE[0]*4:],
                    'Accepted propulsion feet/colors changed')
            base[f],over[f] = a,b
            proof.append({'frame':f,'kind':'hover','swimsuit_upper_source':s,'cut_y_local':cut,
                          'lower_source':f,'lower_RGBA_exact':True,'same_world_origin':[80,80],
                          'upper_pixels_reused':int(np.count_nonzero(a[:cut])),
                          'pistol_source':'accepted swimsuit paired air shooting pose' if f%2==0 else None})
    dash,dashproof = source_body(arc,73)
    # Anchor to the existing one-pixel character eye; no scaling or rotation.
    eye, old_eye = ((63,87),(60,80)) if project=='ver_buki_riko' else ((62,86),(65,80))
    dx,dy = old_eye[0]-eye[0],old_eye[1]-eye[1]
    body = shifted(dash,dx,dy)
    oldbody = layer(arc,5,217)
    base[217],over[217] = body,np.zeros_like(body)
    proof.append({'frame':217,'kind':'nova_body','reuse':dashproof,'translation':[dx,dy],
                  'eye_before':eye,'eye_after':old_eye,'no_rescale_or_rotation':True})
    for n in (218,220):
        old = layer(arc,5,n)
        candidates=[]
        for y in range(-8,9):
            for x in range(-16,17):
                try:moved=shifted(oldbody,x,y)
                except ValueError:continue
                score=int(np.count_nonzero((moved>0)&(moved==old)))
                candidates.append((score,-abs(x)-abs(y),x,y))
        _,_,x,y=max(candidates)
        remove=binary_dilation(shifted(oldbody>0,x,y),iterations=1)
        effect=old.copy();effect[remove]=0
        newbody=shifted(body,x,y)
        envelope=binary_fill_holes(old>0)
        values,counts=np.unique(effect[effect>0],return_counts=True)
        if len(values) and np.count_nonzero(effect)>100:
            fill=int(values[int(counts.argmax())]);holes=remove&envelope&(effect==0)&(newbody==0)
            effect[holes]=fill
        else:
            fill=None;holes=np.zeros_like(remove)
        # Base must appear above the energy; the overlay is cut at its exact alpha.
        effect[newbody>0]=0
        preserved=~remove&(newbody==0)
        require(np.array_equal(effect[preserved],old[preserved]),'External native Nova effect changed')
        base[n],over[n]=newbody,effect
        proof.append({'frame':n,'kind':'nova_with_effect','body_source':217,'translation':[x,y],
                      'native_effect_outside_old_and_new_body_preserved':True,'body_erase_pixels':int(remove.sum()),
                      'envelope_fill_pixels':int(holes.sum()),'fill_existing_index':fill})
    oldflash=layer(arc,5,219)
    vals,cnt=np.unique(oldflash[oldflash>0],return_counts=True)
    colors=vals[np.argsort(-cnt)].tolist();require(len(colors)>=2,'Unexpected Nova flash colors')
    flash=np.zeros_like(body);flash[binary_dilation(body>0,iterations=2)]=colors[1];flash[body>0]=colors[0]
    base[219],over[219]=np.zeros_like(body),flash
    proof.append({'frame':219,'kind':'nova_flash','silhouette_source':217,'existing_color_indices':colors,
                  'same_effect_palette':True})
    require(set(base)==set(over)==set(FRAMES),'Incomplete special scope')
    for n in FRAMES:
        for b in (6,7,8):
            require(not np.any(layer(arc,b,n)),'Unaccounted nonempty special armor layer')
    return base,over,sorted(proof,key=lambda q:q['frame'])

def pack(arc, base, over):
    g,c = entry(arc,2),entry(arc,3)
    bank = graphics_bank(g,0,allow_bank_aliases=True)
    groups={}
    for f in bank['frames']:groups.setdefault(f['offset'],[]).append(f['index'])
    replacements,counts,changes = {},{},{0:{},5:{}}
    reports=[]
    for off,refs in groups.items():
        if not set(refs)&set(FRAMES):continue
        require(set(refs)<=set(FRAMES),'Special stream aliases a preserved frame')
        f=bank['frames'][refs[0]];raw=decode_stream(g,off,f['limit'],f['tile_count']*128).data
        protected={p['tile'] for n in refs for b in(6,7,8) for p in composition_frame(c,b,n)['parts']}
        count=32;expanded=resize_tile_storage(raw,f['tile_count'],count)
        images=[v[n] for v in(base,over) for n in refs]
        # A fresh layout may use the same pixels with a different tile partition.
        limits=[24]*len(images)
        result,assigned=pack_shared(expanded,count,images,set(range(count))-protected,limits)
        for index,b in enumerate((0,5)):
            for n,rr in zip(refs,assigned[index*len(refs):(index+1)*len(refs)]):
                if not rr:
                    blank=composition_frame(c,6,n)['parts'][0]['tile']
                    rr=[(blank,72,72,0)]
                require(rr and all(-128<=x-80<=127 and -128<=y-80<=127 for _,x,y,_ in rr),'Part outside signed origin range')
                changes[b][n]=b''.join(struct.pack('<BBbb',flag,t,x-80,y-80)for t,x,y,flag in rr)
        for n in refs:replacements[n]=result;counts[n]=count
        reports.append({'frames':refs,'protected_blank_tiles':sorted(protected),'parts':[len(q)for q in assigned],
                        'tiles':count,'encoded_bytes':len(encode_stream(result))})
    nc=c;slack={}
    for b,rr in changes.items():nc,slack[b]=repack_parts(nc,b,rr)
    ng,graphics=repack_variable(g,replacements,counts)
    result=replace_entry(replace_entry(arc,2,ng),3,nc)
    for n in FRAMES:
        require(np.array_equal(layer(result,0,n),base[n]) and np.array_equal(layer(result,5,n),over[n]),
                'Special pixels differ after packing')
    checked=0
    for bi in range(len(bank_offsets(g,allow_aliases=True))):
        before=graphics_bank(g,bi,allow_bank_aliases=True);after=graphics_bank(ng,bi,allow_bank_aliases=True)
        require((before['base'],before['end'],len(before['frames']))==(after['base'],after['end'],len(after['frames'])),'Graphics bank dimensions changed')
        for a,b in zip(before['frames'],after['frames']):
            if bi==0 and a['index']in FRAMES:continue
            require(decode_stream(g,a['offset'],a['limit'],a['tile_count']*128).data==decode_stream(ng,b['offset'],b['limit'],b['tile_count']*128).data,'Unrelated graphics changed');checked+=1
    for bi in range(len(bank_offsets(c))):
        for n in range(composition_frame(c,bi,0)['bank_frame_count']):
            if bi in (0,5) and n in FRAMES:continue
            require(records(c,bi,n)==records(nc,bi,n),'Unrelated composition changed')
    from scripts.discover_inputs import psx_arc
    for e in psx_arc(arc):
        if int(e['type'],16)not in(2,3):require(entry(arc,int(e['type'],16))==entry(result,int(e['type'],16)),'Palette/timing/sound/static data changed')
    require(len(arc)==len(result),'ARC length changed')
    return result,{'parts_remaining':slack,'graphics':graphics,'groups':reports,
                   'all_unselected_graphics_checked':checked,'nonselected_parts_and_nongraphics_entries_exact':True}

def prepare(project, output, preview_only=False):
    output=output.resolve();require(output.is_relative_to(WORK.resolve())and not output.exists(),'Fresh isolated core output required')
    folder,stem,expected=SOURCES[project];path=ROOT/'out'/project/folder/(stem+'.bin')
    require(digest(path)==expected,'Unsupported source BIN')
    assets,records_=read_disc(path,('PL02_U.ARC',));arc=assets['PL02_U.ARC']
    b,o,proof=targets(project,arc)
    result,packing=(None,None)if preview_only else pack(arc,b,o)
    output.mkdir(parents=True)
    reviews=[]
    for n in FRAMES:
        old=image(arc,layer(arc,0,n),layer(arc,5,n));new=image(arc,b[n],o[n])
        old.save(output/f'before_{n:03}.png');new.save(output/f'after_{n:03}.png')
        Image.fromarray(b[n]).save(output/f'base_{n:03}.png');Image.fromarray(o[n]).save(output/f'overlay_{n:03}.png')
        # board expects its original 384 canvas with origin at160.
        for text,im in((f'{n} BEFORE',old),(f'{n} AFTER',new)):
            canvas=Image.new('RGBA',(384,384));canvas.alpha_composite(im,(80,80));reviews.append((text,canvas))
    board(reviews,output/'special_review.png',cols=4)
    proposal={'project':project,'baseline':path.relative_to(ROOT).as_posix(),'baseline_sha256':expected,
              'source_arc_sha256':sha(arc),'record':records_['PL02_U.ARC'],'frames':list(FRAMES),
              'registration':proof,'packing':packing,'new_generated_art':False,'runtime_verified':False,
              'required_render_rule':'Ultimate ordinary frames: engine armor0 => visual15, owned => visual0; frames217..230 retain visual15',
              'partial_armor_rule':'gameplay armor flags are unchanged; native Ultimate capsule grants15',
              'capsule_graphics10_13_and_parts18_21_preserved':True}
    if result is not None:
        (output/'PL02_U.ARC').write_bytes(result);proposal['after_sha256']=sha(result)
        proposal['resource']=(output/'PL02_U.ARC').relative_to(ROOT).as_posix()
    save_json(output/'proposal.json',proposal)
    require(digest(path)==expected,'Source changed')
    print(json.dumps({'project':project,'output':str(output),'sha256':sha(result)if result else None,'packing':packing},ensure_ascii=False))

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--project',choices=SOURCES,required=True)
    p.add_argument('--output',type=Path,required=True);p.add_argument('--preview-only',action='store_true')
    a=p.parse_args();prepare(a.project,a.output,a.preview_only)
