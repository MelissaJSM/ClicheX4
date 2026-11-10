"""프로스트 타워·라이징 파이어 의상을 같은 얼굴/권총 기준으로 등록한다."""
import argparse,json,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import numpy as np
from PIL import Image,ImageDraw
from scipy.ndimage import label,distance_transform_edt,binary_erosion
from scripts.prepare_nana_ultimate_elemental_reference import D,PARENT,PARENT_SHA,ARC_SHA,FRAMES,ORDER
from scripts.prepare_nana_fourth_pilot import entry,render,require,write
from scripts.prepare_nana_ultimate_shot_arm import full
from scripts.prepare_nana_fourth_elemental_art import shift
from scripts.prepare_nana_pilot import normalize
from scripts.project import digest
from scripts.discover_inputs import sha256
from scripts.extract_zero import save_image
from scripts.prepare_shibuki_ultimate_production import pack_shared,repack_parts
from scripts.prepare_nana_ultimate_run import verify
from scripts.prepare_riko_ui import replace_entry
from src.psx_player import graphics_bank,composition_frame,decode_stream
from src.psx_compress import encode_stream
from src.psx_bank_repack import repack_graphics_bank
SOURCE_SHA='e388e3f9e1889d295ba3862b59762a4c13fd556ea35869d016674eff729979fd'
FROST_SHA='4a95d1d239a467eb10b96967207bca8a09fae15d4b09a9c122dae950299817fd'
GUNS={95:[62,73,70,81],100:[68,60,73,69],101:[69,42,75,54],102:[70,48,77,60],103:[68,56,74,66],104:[69,44,76,56],231:[69,52,76,63]}

def face_mask(face,gun,master):
    x,y,x2,y2=face;gx,gy,gx2,gy2=gun;mask=master>0;fy,fx=np.indices(mask.shape)
    return mask&~((fx+x>=gx)&(fx+x<gx2)&(fy+y>=gy)&(fy+y<gy2))

def artwork(out):
    src=D/'elemental_v1/generated.png';require(digest(src)==SOURCE_SHA,'Source changed');source=Image.open(src).convert('RGBA');arc=(PARENT/'PL02_U.ARC').read_bytes();words=struct.unpack_from('<16H',entry(arc,9),32);rgb=np.array([[(w>>s&31)*255//31 for s in(0,5,10)]for w in words],np.int32)
    frost=D/'frost_pose_v2/generated.png';require(digest(frost)==FROST_SHA,'Frost source changed');frost_source=Image.open(frost).convert('RGBA')
    master=full(arc,0);targets={};meta={};yy,xx=np.indices((160,160));registration_errors=[]
    for i,n in enumerate(ORDER):
        base=render(arc,n)[1];by,bx=np.nonzero(base);bottom=int(by.max());gy,gx=np.nonzero((base==14)&(yy<85));ex,ey=round(float(np.median(gx))),round(float(np.median(gy)))
        cell=frost_source if n==95 else source.crop((i%4*source.width//4,i//4*source.height//2,(i%4+1)*source.width//4,(i//4+1)*source.height//2));a=np.array(cell);labs,_=label(a[:,:,3]>=192,np.ones((3,3)));sizes=np.bincount(labs.flat);sizes[0]=0;keep=labs==sizes.argmax();sy,sx=np.nonzero(keep);a[~keep,3]=0;crop=Image.fromarray(a).crop((sx.min(),sy.min(),sx.max()+1,sy.max()+1));ca=np.array(crop).astype(np.int32);cyy,_=np.indices(ca.shape[:2]);green=(ca[:,:,1]>ca[:,:,0]+8)&(ca[:,:,1]>ca[:,:,2]+8)&(ca[:,:,3]>=192)&(cyy<crop.height*.65);gy,gx=np.nonzero(green);require(len(gx)>0,'Source eye missing');choices=[]
        for h in range(32,85):
            w=round(h*crop.width/crop.height);cx=round((float(np.median(gx))+.5)*w/crop.width-.5);cy=round((float(np.median(gy))+.5)*h/crop.height-.5);choices.append((abs(h-1-cy-(bottom-ey)),h,w,cx,cy))
        _,h,w,cx,cy=min(choices);v=normalize(crop,h,rgb,width=w);dx,dy=ex-cx,ey-cy;target=np.zeros_like(base);target[dy:dy+h,dx:dx+w]=v
        face=[ex-3,ey-3,ex+7,ey+6];x,y,x2,y2=face;face_pixels=master[65:74,73:83];fm=face_mask(face,GUNS[n],face_pixels);target[y:y2,x:x2][fm]=face_pixels[fm]
        gx,gy,gx2,gy2=GUNS[n]
        # The weapon and the hand retain their native firing location. Clear
        # only generated arm/weapon pixels outside the native contact envelope.
        arm_gate=(xx<ex-3)&(yy<ey+2)
        if n==95:arm_gate=(xx<ex-7)&(yy>=ey+10)&(yy<ey+24)
        arm_gate&=~((xx>=ex-7)&(xx<ex+10)&(yy>=ey-17)&(yy<ey-4))
        target[arm_gate&(base==0)]=0;target[gy:gy2,gx:gx2]=base[gy:gy2,gx:gx2]
        dist,near=distance_transform_edt(target==0,return_indices=True);missing=(base>0)&(target==0)
        print(json.dumps(dict(frame=n,size=[w,h],eye=[ex,ey],sole=bottom,placement=[dx,dy],max_distance=float(dist[missing].max(initial=0)),far=np.argwhere(missing&(dist>6)).tolist())),flush=True)
        if dist[missing].max(initial=0)>6:registration_errors.append([n,float(dist[missing].max())])
        target[missing]=target[near[0][missing],near[1][missing]];target[bottom+1:]=0
        edge=(target>0)&~binary_erosion(target>0,np.ones((3,3),bool));rim=edge&(target==5)
        for x,y,x2,y2 in(face,GUNS[n]):rim[y:y2,x:x2]=False
        target[rim]=1;labs,count=label(target>0,np.ones((3,3)));removed=[]
        for k in range(1,count+1):
            mask=labs==k
            if np.count_nonzero(mask)<=2 and not np.any(base[mask]):removed.extend([[int(x),int(y)]for y,x in np.argwhere(mask)]);target[mask]=0
        x,y,x2,y2=face;target[y:y2,x:x2][fm]=face_pixels[fm];target[gy:gy2,gx:gx2]=base[gy:gy2,gx:gx2]
        require(not np.any((base>0)&(target==0)),'Base escapes costume');require(int(np.nonzero(target)[0].max())==bottom,'Sole moved');targets[n]=target
        meta[n]=dict(frames=[n,n],source_cell=i,source_sha256=FROST_SHA if n==95 else SOURCE_SHA,source_size=[w,h],source_crop_size=list(crop.size),placement=[dx,dy],eye=[ex,ey],face_box=face,sole=bottom,pistol_present=True,pistol_mask_bbox=GUNS[n],registration_max_distance=float(dist[missing].max(initial=0)),removed_detached_pixels=removed,neutral_outline_pixels=int(rim.sum()))
    require(np.array_equal(render(arc,96)[1],shift(render(arc,95)[1],1)),'Frost translation differs');targets[96]=shift(targets[95],1)
    require(np.array_equal(render(arc,232)[1],render(arc,231)[1]),'Ground fire pair differs');targets[232]=targets[231].copy()
    for n,src,delta in((96,95,1),(232,231,0)):
        x,y,x2,y2=GUNS[src];meta[n]=dict(frames=[n,n],shared_body_frame=src,translation=[delta,0],pistol_present=True,pistol_mask_bbox=[x+delta,y,x2+delta,y2])
    board=Image.new('RGB',(1280,1080),'#46545c');draw=ImageDraw.Draw(board)
    for i,n in enumerate([0]+FRAMES):
        v=targets[n]if n else master
        if n:save_image(v.tobytes(),(160,160),words,out/f'ultimate_{n:03}.png')
        rgba=np.concatenate((rgb[v].astype(np.uint8),((v>0)*255).astype(np.uint8)[...,None]),2);im=Image.fromarray(rgba).crop((40,24,120,104)).resize((320,320),Image.Resampling.NEAREST);x,y=i%4*320,i//4*360;board.paste(im,(x,y+28),im);draw.text((x+4,y+8),str(n)if n else'ACCEPTED IDLE',fill='white')
    board.save(out/'elemental_review_4x.png');require(not registration_errors,'Registration gaps: '+str(registration_errors));return targets,[meta[n]for n in FRAMES]

def pack(arc,targets):
    g,c=entry(arc,2),entry(arc,3);bank=graphics_bank(g,0,allow_bank_aliases=True);changes={};replacements={};reports=[];seen=set()
    for n in FRAMES:
        f=bank['frames'][n]
        if f['offset']in seen:continue
        seen.add(f['offset']);ns=[q['index']for q in bank['frames']if q['offset']==f['offset']];require(set(ns)<=set(FRAMES),'Unselected alias');require(ns==[95,96]or ns==[n],'Unexpected translation group')
        raw=decode_stream(g,f['offset'],f['limit'],f['tile_count']*128).data;keep={q['tile']for v in ns for cb in(0,6,7,8)for q in composition_frame(c,cb,v)['parts']};pool={t for t in range(f['tile_count'])if t not in keep and t%16!=0};base=render(arc,n)[1];overlay=np.where((targets[n]==base)&(targets[n]!=15),0,targets[n]).astype(np.uint8)
        new,rr=pack_shared(raw,f['tile_count'],[overlay],pool,[len(pool)])
        for v in ns:
            delta=1 if v==96 else 0;rows=[(t,x+delta,y,fl)for t,x,y,fl in rr[0]];changes[v]=b''.join(struct.pack('<BBbb',fl,t,x-80,y-80)for t,x,y,fl in rows);replacements[v]=encode_stream(new)
        reports.append(dict(frames=ns,source_frame=n,free_tiles=len(pool),parts=len(rr[0])));print(json.dumps(reports[-1]),flush=True)
    nc,slack=repack_parts(c,5,changes);ng,rep=repack_graphics_bank(g,0,replacements);result=replace_entry(replace_entry(arc,2,ng),3,nc);check=verify(arc,result,targets,{})
    return result,dict(packing=reports,graphics_repack=rep,parts_bank5_remaining=slack,verification=check)

def prepare(out,art_only=False):
    out=out.resolve();require(out.is_relative_to(D)and not out.exists(),'Fresh isolated output required');require(digest(PARENT/'rin_nana.bin')==PARENT_SHA and digest(PARENT/'PL02_U.ARC')==ARC_SHA,'Parent changed');out.mkdir();targets,proof=artwork(out);write(out/'registration.json',proof)
    if art_only:return
    result,packed=pack((PARENT/'PL02_U.ARC').read_bytes(),targets);(out/'PL02_U.ARC').write_bytes(result);write(out/'recipe.json',dict(task='ultimate_armor_nana',kind='ultimate_elemental',parent_sha256=PARENT_SHA,parent_arc_sha256=ARC_SHA,generated_sha256=SOURCE_SHA,frost_source_sha256=FROST_SHA,frames=FRAMES,registration=proof,**packed,files={'PL02_U.ARC':sha256(result)},full_ultimate_complete=False));print(json.dumps(dict(output=str(out),sha256=sha256(result),verification=packed['verification'])))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--art-only',action='store_true');a=p.parse_args();prepare(a.output,a.art_only)
