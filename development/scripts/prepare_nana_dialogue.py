"""나나 대화8슬롯을 고정 길이로 제작한다. 아머 의상은 기본형 얼굴로 유보한다."""
import argparse,json,struct,sys
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.inventory_nana_dialogue import ART,PARENT,PARENT_SHA,read_sources,locate
from scripts.prepare_rin_dialogue import overlay
from scripts.prepare_riko_ui import entry
from scripts.prepare_riko_illustrations import regrid_ui_parts,repack_one_bank
from scripts.prepare_nana_selection_portrait import RGB
from scripts.project import digest
from scripts.discover_inputs import sha256
from scripts.extract_zero import save_image
from src.psx_ui_atlas import aliased_composition,local_composition
from src.psx_static_effect import compose_static
from src.psx_ui_render import render_static_rgba
WORDS=[0]+[0x8000|(r>>3)|((g>>3)<<5)|((b>>3)<<10)for r,g,b in RGB]
PAL=struct.pack('<16H',*WORDS)
MOUTH=(71,54,78,60)
SOURCES=('closed_generated.png','open_generated.png','prompt.txt','open_prompt.txt')
def native_frames():
    closed=Image.open(ART/SOURCES[0]).convert('RGBA');opened=Image.open(ART/SOURCES[1]).convert('RGBA')
    if closed.size!=opened.size:raise ValueError('Source registration differs')
    alpha=np.array(closed)[:,:,3];full=np.where((alpha>=192).all(axis=1))[0]
    if not len(full):raise ValueError('Missing full-width lower edge')
    bottom=int(full[-1])+1;scale=max(112/closed.width,94/bottom);box=(0,0,closed.width,bottom)
    colors=np.array([[(w>>s&31)*255//31 for s in(0,5,10)]for w in WORDS[1:]],np.int32);variants=[]
    for im in(closed,opened):
        im=im.crop(box).convert('RGBa').resize((round(closed.width*scale),round(bottom*scale)),Image.Resampling.LANCZOS).convert('RGBA')
        dx=(im.width-112)//2;dy=im.height-94;a=np.array(im.crop((dx,dy,dx+112,dy+94)))
        dist=((a[:,:,:3].astype(np.int32)[:,:,None,:]-colors)**2).sum(3);out=np.zeros((96,112),np.uint8);out[:94]=np.where(a[:,:,3]>=192,dist.argmin(2)+1,0);variants.append(out)
    c,o=variants;opened=c.copy();x0,y0,x1,y1=MOUTH;opened[y0:y1,x0:x1]=o[y0:y1,x0:x1]
    return {n:(opened if n&4 else c).copy()for n in range(8)},{'crop':box,'uniform_scale':scale,'mouth_rect':MOUTH,'full_width_row':93,'armor_slots':'basic portrait fallback; no armor costume design'}
def verify(original,new,inv,targets,palette):
    if set(new)!=set(original)or len(new)!=26:raise ValueError('Unexpected file scope')
    if(len(inv['graphics']),len(inv['compositions']),sum(len(q['rows'])for q in inv['palettes']))!=(9,9,17):raise ValueError('Unexpected copy counts')
    if set(targets)!=set(range(8))or palette!=PAL:raise ValueError('Unexpected frames/palette')
    oldp=entry(original['ST00_00.ARC'],10);p=entry(new['ST00_00.ARC'],10);g=entry(new['ST00_00.ARC'],0x10102)[204800:217088]
    start,end=struct.unpack_from('<I',oldp,44)[0],struct.unpack_from('<I',oldp,52)[0]
    if new!=overlay(original,inv,g,p[start:end],palette):raise ValueError('Bytes outside dialogue scope changed')
    allowed=set();counts=[]
    for n,a in targets.items():
        if a.shape!=(96,112)or a.dtype!=np.uint8 or a.max()>15:raise ValueError('Invalid native image')
        if not a[93].all()or a[94:].any():raise ValueError('Bottom gap/spill')
        before=aliased_composition(oldp,11,n);after=aliased_composition(p,11,n)
        if before['bank_frame_count']!=8 or after['bank_frame_count']!=8 or len(before['parts'])!=len(after['parts']):raise ValueError('Count changed')
        counts.append(len(after['parts']))
        for b,c in zip(before['parts'],after['parts']):
            if any(b[k]!=c[k]for k in('flip_x','flip_y','unknown_flags','record_offset'))or c['clut']!=0:raise ValueError('Flags/CLUT changed')
            allowed.update(range(b['record_offset'],b['record_offset']+4))
        px,size,bounds,_=compose_static(g,local_composition(after))
        if(px,size,bounds)!=(a.tobytes(),(112,96),(-56,-48,56,48)):raise ValueError('Indexed portrait mismatch')
        im,rb=render_static_rgba(g,after,{0:WORDS});expected=np.zeros((96,112,4),np.uint8)
        for i,w in enumerate(WORDS[1:],1):expected[a==i]=[*(int(w>>s&31)*255//31 for s in(0,5,10)),255]
        if rb!=bounds or not np.array_equal(np.array(im),expected):raise ValueError('CLUT render mismatch')
        if compose_static(g,local_composition(aliased_composition(p,12,n)))[:3]!=(px,size,bounds):raise ValueError('Bank12 alias differs')
    if len(oldp)!=len(p)or any(a!=b and i not in allowed for i,(a,b)in enumerate(zip(oldp,p))):raise ValueError('Other headers/records changed')
    for q in inv['compositions']:
        op=entry(original[q['file']],10);np_=entry(new[q['file']],10);offsets=struct.unpack_from('<'+'I'*(struct.unpack_from('<I',op)[0]//4),op)
        if sum(x==q['offset']for x in offsets)not in(1,2):raise ValueError('Unexpected bank alias scope')
        if op[:q['offset']]!=np_[:q['offset']]or op[q['offset']+q['size']:]!=np_[q['offset']+q['size']:]:raise ValueError('Other composition affected')
    mask=np.zeros((96,112),bool);x0,y0,x1,y1=MOUTH;mask[y0:y1,x0:x1]=True
    if not 1<=np.count_nonzero(targets[0]!=targets[4])<=42:raise ValueError('Mouth difference missing/too large')
    for n,a in targets.items():
        if not np.array_equal(a,targets[4 if n&4 else 0])or not np.array_equal(a[~mask],targets[0][~mask])or not np.array_equal(a>0,targets[0]>0):raise ValueError('Portrait moves outside mouth')
    return {'texture_copies':9,'composition_copies':9,'palette_rows':17,'arc_files':26,'frames':8,'native_size':[112,96],'part_counts':counts,'other_bytes_exact':True,'alias_banks':[11,12],'all_parts_clut_zero':True,'actual_clut_render_equal':True,'mouth_changed_pixels':int(np.count_nonzero(targets[0]!=targets[4])),'face_body_fixed':True,'bottom_filled_width':112,'rows94_95_transparent':True,'armor_outfits_pending':True,'runtime_verified':False}
def prepare(out):
    records,raw=read_sources();inv=locate(records,raw);names=sorted({q['file']for k in('graphics','compositions','palettes')for q in inv[k]});original={n:raw[n]for n in names}
    targets,conversion=native_frames();g=entry(raw['ST00_00.ARC'],0x10102)[204800:217088];p=entry(raw['ST00_00.ARC'],10);start,end=struct.unpack_from('<I',p,44)[0],struct.unpack_from('<I',p,52)[0]
    tt={n:(a.tobytes(),(112,96))for n,a in targets.items()};p=regrid_ui_parts(p,11,tt);ng,np_,packing=repack_one_bank(g,p,11,tt,{n:0 for n in tt});new=overlay(original,inv,ng,np_[start:end],PAL);v=verify(original,new,inv,targets,PAL)
    out.mkdir(parents=True,exist_ok=False)
    for n,data in new.items():(out/n).write_bytes(data)
    board=Image.new('RGB',(896,420),(40,40,50));d=ImageDraw.Draw(board)
    for n,a in targets.items():
        im=save_image(a.tobytes(),(112,96),WORDS,out/f'frame_{n}.png')
        if n in(0,4):
            big=im.convert('RGBA').resize((448,384),Image.Resampling.NEAREST);board.paste(big,(n//4*448,28),big);d.text((n//4*448+5,5),'closed'if n==0 else'speaking',fill='white')
    board.save(out/'review.png');(out/'palette.bin').write_bytes(PAL)
    recipe={'kind':'nana_dialogue','parent_sha256':PARENT_SHA,'parent_manifest_sha256':digest(PARENT/'manifest.json'),'tool':'built-in image_gen','sources':[{'path':(ART/n).relative_to(ROOT).as_posix(),'sha256':digest(ART/n)}for n in SOURCES],'conversion':conversion,'packing':packing,'verification':v,'inventory':inv,'files':[{'file':n,'source':records[n],'sha256':sha256(new[n])}for n in names]}
    (out/'recipe.json').write_text(json.dumps(recipe,indent=2)+'\n','utf8');print(json.dumps({'output':str(out),'packing':packing,'verification':v}))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);prepare(p.parse_args().output)
