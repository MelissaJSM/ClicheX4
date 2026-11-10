"""린 대화 얼굴3상태를 고정 크기/15색으로 변환하고 모든 원본 복사본을 교체한다."""
import argparse,json,struct,sys
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.inventory_rin_dialogue import ART,PARENT,PARENT_SHA,locate,read_sources
from scripts.prepare_riko_ui import entry,replace_entry
from scripts.prepare_riko_illustrations import repack_one_bank
from scripts.prepare_rin_selection_portrait import RGB
from scripts.project import digest
from scripts.discover_inputs import sha256
from scripts.extract_zero import save_image
from src.psx_ui_atlas import aliased_composition,local_composition
from src.psx_static_effect import compose_static
from src.psx_ui_render import render_static_rgba

WORDS=[0]+[0x8000|(r>>3)|((g>>3)<<5)|((b>>3)<<10) for r,g,b in RGB]
PALETTE=struct.pack('<16H',*WORDS)
MOUTH=(69,59,78,65)

def native_frames():
    closed=Image.open(ART/'closed_generated.png').convert('RGBA')
    opened=Image.open(ART/'open_generated.png').convert('RGBA')
    if closed.size!=opened.size:raise ValueError('Mouth source registration differs')
    alpha=np.array(closed)[:,:,3]
    bottom=int(np.where((alpha>=128).all(axis=1))[0][-1])+1
    box=(0,0,closed.width,bottom);scale=max(112/closed.width,94/bottom)
    colors=np.array([[(w>>s&31)*255//31 for s in (0,5,10)] for w in WORDS[1:]],np.int32)
    variants=[]
    for im in (closed,opened):
        im=im.crop(box).convert('RGBa').resize((round(closed.width*scale),round(bottom*scale)),Image.Resampling.LANCZOS).convert('RGBA')
        dx=(im.width-112)//2;dy=im.height-94
        a=np.array(im.crop((dx,dy,dx+112,dy+94)))
        distance=((a[:,:,:3].astype(np.int32)[:,:,None,:]-colors)**2).sum(3)
        out=np.zeros((96,112),np.uint8);out[:94]=np.where(a[:,:,3]>=128,distance.argmin(2)+1,0)
        variants.append(out)
    closed,opened=variants
    x0,y0,x1,y1=MOUTH
    wide=closed.copy();wide[y0:y1,x0:x1]=opened[y0:y1,x0:x1]
    small=closed.copy();small[60:62,x0:x1]=opened[60:62,x0:x1]
    return {0:wide,1:closed,2:small},{'shared_crop':box,'uniform_scale':scale,'mouth_rect':MOUTH,'small_open_rows':[60,62]}

def overlay(original,inv,g,p,palette):
    new=dict(original)
    for key,payload in (('graphics',g),('compositions',p)):
        for q in inv[key]:
            if len(payload)!=q['size']:raise ValueError('Dialogue resource length changed')
            data=entry(new[q['file']],q['type']);at=q['offset']
            new[q['file']]=replace_entry(new[q['file']],q['type'],data[:at]+payload+data[at+q['size']:])
    for q in inv['palettes']:
        data=bytearray(entry(new[q['file']],5))
        for row in q['rows']:data[row*32:(row+1)*32]=palette
        new[q['file']]=replace_entry(new[q['file']],5,bytes(data))
    return new

def verify(original,new,inv,targets,palette):
    if set(new)!=set(original) or len(original)!=20:raise ValueError('Unexpected dialogue file set')
    base='ST00_00.ARC';g=entry(new[base],0x10102)[217088:223232]
    oldp=entry(original[base],10);newp=entry(new[base],10)
    start=struct.unpack_from('<I',oldp,13*4)[0];body=newp[start:]
    if palette!=PALETTE:raise ValueError('Unexpected Rin palette')
    if new!=overlay(original,inv,g,body,palette):raise ValueError('Bytes outside dialogue windows changed')
    allowed=set();other_banks=0
    for n,a in targets.items():
        if a.shape!=(96,112) or a.dtype!=np.uint8 or a.max()>15:raise ValueError('Invalid native portrait')
        if not a[93].all() or a[94:].any():raise ValueError('Dialogue lower edge has a gap or spill')
        before=aliased_composition(oldp,13,n);after=aliased_composition(newp,13,n)
        if before['bank_frame_count']!=3 or after['bank_frame_count']!=3 or len(before['parts'])!=len(after['parts']):raise ValueError('Dialogue state count changed')
        for u,v in zip(before['parts'],after['parts']):
            if any(u[k]!=v[k] for k in ('x','y','flip_x','flip_y','clut','unknown_flags','record_offset')):raise ValueError('Dialogue geometry/palette changed')
            if u['clut']!=0:raise ValueError('Unexpected original CLUT')
            allowed.update((u['record_offset'],u['record_offset']+1))
        pixels,size,bounds,_=compose_static(g,local_composition(after))
        if (pixels,size,bounds)!=(a.tobytes(),(112,96),(-56,-48,56,48)):raise ValueError('Dialogue indexed readback differs')
        actual,rb=render_static_rgba(g,after,{0:WORDS})
        expected=np.zeros((96,112,4),np.uint8)
        for i,w in enumerate(WORDS[1:],1):expected[a==i]=[*(int(w>>s&31)*255//31 for s in (0,5,10)),255]
        if rb!=bounds or not np.array_equal(np.array(actual),expected):raise ValueError('Actual CLUT rendering differs')
    if len(oldp)!=len(newp) or any(a!=b and i not in allowed for i,(a,b) in enumerate(zip(oldp,newp))):raise ValueError('Other part/header bytes changed')
    for q in inv['compositions']:
        op=entry(original[q['file']],10);np_=entry(new[q['file']],10)
        offsets=struct.unpack_from('<'+'I'*(struct.unpack_from('<I',op)[0]//4),op)
        if sum(x==q['offset'] for x in offsets)!=1:raise ValueError('Target bank is aliased by another resource')
        if op[:q['offset']]!=np_[:q['offset']] or op[q['offset']+q['size']:]!=np_[q['offset']+q['size']:]:raise ValueError('Unrelated composition changed')
        other_banks+=len(offsets)-1
    mask=np.zeros((96,112),bool);x0,y0,x1,y1=MOUTH;mask[y0:y1,x0:x1]=True
    if len({a.tobytes() for a in targets.values()})!=3:raise ValueError('Mouth states are not distinct')
    if any(not np.array_equal(a[~mask],targets[1][~mask]) or not np.array_equal(a>0,targets[1]>0) for a in targets.values()):raise ValueError('Face/body drift outside mouth')
    return {'texture_copies':6,'composition_copies':6,'palette_rows':14,'arc_files':20,
        'original_part_coordinates_order_flags_preserved':True,'frame_count_and_timing_preserved':True,
        'other_bank_parts_unchanged':other_banks,'native_size':[112,96],'bounds':[-56,-48,56,48],
        'three_distinct_mouth_states':True,'face_body_exact_outside_mouth':True,
        'row93_opaque_width':112,'rows94_95_transparent':True,'actual_clut_render_equal':True,
        'other_arc_bytes_exact':True,'runtime_verified':False}

def prepare(out):
    records,raw=read_sources();inv=locate(records,raw)
    names=sorted({q['file'] for k in ('graphics','compositions','palettes') for q in inv[k]})
    original={n:raw[n] for n in names};targets,conversion=native_frames()
    g=entry(raw['ST00_00.ARC'],0x10102)[217088:223232];p=entry(raw['ST00_00.ARC'],10)
    ng,np_,packing=repack_one_bank(g,p,13,{n:(a.tobytes(),(112,96)) for n,a in targets.items()})
    start=struct.unpack_from('<I',p,13*4)[0];new=overlay(original,inv,ng,np_[start:],PALETTE)
    v=verify(original,new,inv,targets,PALETTE)
    out.mkdir(parents=True,exist_ok=False)
    for n,data in new.items():(out/n).write_bytes(data)
    sheet=Image.new('RGB',(1344,420),(40,40,50));draw=ImageDraw.Draw(sheet)
    for n,a in targets.items():
        im=save_image(a.tobytes(),(112,96),WORDS,out/f'frame_{n}.png');big=im.convert('RGBA').resize((448,384),Image.Resampling.NEAREST)
        sheet.paste(big,(n*448,28),big);draw.text((n*448+5,5),['speaking / 0','closed / 1','small open / 2'][n],fill='white')
    sheet.save(out/'review.png');(out/'palette.bin').write_bytes(PALETTE)
    recipe={'kind':'rin_dialogue','parent_sha256':PARENT_SHA,'tool':'built-in image_gen',
        'sources':[{'path':(ART/n).relative_to(ROOT).as_posix(),'sha256':digest(ART/n)} for n in ('closed_generated.png','open_generated.png','prompt.txt','open_prompt.txt')],
        'conversion':conversion,'packing':packing,'verification':v,'inventory':inv,
        'files':[{'file':n,'source':records[n],'sha256':sha256(new[n])} for n in names]}
    (out/'recipe.json').write_text(json.dumps(recipe,indent=2)+'\n','utf8');print(json.dumps({'output':str(out),'packing':packing,'verification':v}))

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,required=True);prepare(parser.parse_args().output)
