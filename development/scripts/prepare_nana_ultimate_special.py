"""얼티밋 차지 연계·더블 사이클론7참조를 같은 체형과 권총 접점으로 등록한다."""
import argparse,json,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import numpy as np
from PIL import Image,ImageDraw
from scipy.ndimage import label,distance_transform_edt,binary_erosion
from scripts.prepare_nana_ultimate_special_reference import D,PARENT,PARENT_SHA,ARC_SHA,FRAMES,ORDER
from scripts.prepare_nana_fourth_pilot import entry,render,require,write
from scripts.prepare_nana_ultimate_shot_arm import full,pack_resources
from scripts.prepare_nana_fourth_special_art import shift
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
SOURCE_SHA='59520dc164222c83f035baf1362fa3a5d12d703add4f63229327072d9503fd5f'
GUNS={89:[62,50,70,59],90:[60,60,68,67],91:[56,66,64,73],97:[68,69,74,76],98:[55,70,63,77]}
CONTACTS={89:[],90:[],91:[],97:[],98:[[96,70,101,77]]}

def artwork(out):
    src=D/'special_v1/generated.png';require(digest(src)==SOURCE_SHA,'Source changed');source=Image.open(src).convert('RGBA')
    arc=(PARENT/'PL02_U.ARC').read_bytes();words=struct.unpack_from('<16H',entry(arc,9),32);rgb=np.array([[(w>>s&31)*255//31 for s in(0,5,10)]for w in words],np.int32)
    master=full(arc,0);targets={};meta={};yy,xx=np.indices((160,160))
    for i,n in enumerate(ORDER):
        base=render(arc,n)[1];by,bx=np.nonzero(base);bottom=int(by.max());gy,gx=np.nonzero((base==14)&(yy<80));ex,ey=round(float(np.median(gx))),round(float(np.median(gy)))
        cell=source.crop((i%3*source.width//3,i//3*source.height//2,(i%3+1)*source.width//3,(i//3+1)*source.height//2));a=np.array(cell);labs,_=label(a[:,:,3]>=192,np.ones((3,3)));sizes=np.bincount(labs.flat);sizes[0]=0;keep=labs==sizes.argmax();sy,sx=np.nonzero(keep);a[~keep,3]=0;crop=Image.fromarray(a).crop((sx.min(),sy.min(),sx.max()+1,sy.max()+1))
        ca=np.array(crop).astype(np.int32);cyy,_=np.indices(ca.shape[:2]);green=(ca[:,:,1]>ca[:,:,0]+8)&(ca[:,:,1]>ca[:,:,2]+8)&(ca[:,:,3]>=192)&(cyy<crop.height*.55);gy,gx=np.nonzero(green);require(len(gx)>0,'Source eye missing');choices=[]
        for h in range(32,75):
            w=round(h*crop.width/crop.height);cx=round((float(np.median(gx))+.5)*w/crop.width-.5);cy=round((float(np.median(gy))+.5)*h/crop.height-.5);choices.append((abs(h-1-cy-(bottom-ey)),abs(cy-16),h,w,cx,cy))
        _,_,h,w,cx,cy=min(choices);v=normalize(crop,h,rgb,width=w);dx,dy=ex-cx,ey-cy;target=np.zeros_like(base);target[dy:dy+h,dx:dx+w]=v
        face=[ex-3,ey-3,ex+7,ey+6];x,y,x2,y2=face;face_pixels=master[65:74,73:83];fm=face_pixels>0
        # The gathered weapon lies in front of the left fringe of the face.
        gx,gy,gx2,gy2=GUNS[n];fy,fx=np.indices(fm.shape);fm&=~((fx+x>=gx)&(fx+x<gx2)&(fy+y>=gy)&(fy+y<gy2))
        target[y:y2,x:x2][fm]=face_pixels[fm]
        # Register the authored shooting arm to the native wrist, rather than
        # leaving a second generated pistol above/beside the native gun.
        x,y,x2,y2=GUNS[n];arm_gate=(xx<ex-5)&(yy<ey+7)
        if n==97:arm_gate=(xx<ex-2)&(yy>=ey-4)&(yy<ey+10)
        target[arm_gate&(base==0)]=0
        for box in [GUNS[n]]+CONTACTS[n]:
            x,y,x2,y2=box;target[y:y2,x:x2]=base[y:y2,x:x2]
        dist,near=distance_transform_edt(target==0,return_indices=True);missing=(base>0)&(target==0)
        print(json.dumps(dict(frame=n,size=[w,h],eye=[ex,ey],placement=[dx,dy],max_distance=float(dist[missing].max(initial=0)),far=np.argwhere(missing&(dist>6)).tolist())),flush=True)
        require(dist[missing].max(initial=0)<=6,'Registration too far from native pose')
        target[missing]=target[near[0][missing],near[1][missing]];target[bottom+1:]=0
        # Confine the red shadow at the extreme contour to the accepted dark
        # outline. Preserve face, gun, palms and all inner pink material.
        edge=(target>0)&~binary_erosion(target>0,np.ones((3,3),bool));rim=edge&(target==5)
        for x,y,x2,y2 in [face,GUNS[n]]+CONTACTS[n]:rim[y:y2,x:x2]=False
        target[rim]=1
        labs,count=label(target>0,np.ones((3,3)));removed=[]
        for k in range(1,count+1):
            mask=labs==k
            if np.count_nonzero(mask)<=2 and not np.any(base[mask]):removed.extend([[int(x),int(y)]for y,x in np.argwhere(mask)]);target[mask]=0
        x,y,x2,y2=face;target[y:y2,x:x2][fm]=face_pixels[fm]
        require(not np.any((base>0)&(target==0)),'Base escapes costume');require(int(np.nonzero(target)[0].max())==bottom,'Sole moved');targets[n]=target
        meta[n]=dict(frames=[n,n],source_cell=i,source_size=[w,h],source_crop_size=list(crop.size),placement=[dx,dy],eye=[ex,ey],face_box=face,sole=bottom,pistol_present=True,pistol_mask_bbox=GUNS[n],contacts=CONTACTS[n],registration_max_distance=float(dist[missing].max(initial=0)),removed_detached_pixels=removed,neutral_outline_pixels=int(rim.sum()))
    # Shared streams:88 retains its native charge trail,99 is exact X+1.
    native88=render(arc,88)[1];body88=shift(render(arc,89)[1],-1);effect=np.where(native88!=body88,native88,0).astype(np.uint8)
    require(set(np.unique(effect))=={0,12},'Unexpected charge trail')
    overlay89=np.where((targets[89]==render(arc,89)[1])&(targets[89]!=15),0,targets[89]).astype(np.uint8)
    overlay88=shift(overlay89,-1);targets[88]=np.where(overlay88,overlay88,native88).astype(np.uint8)
    save_image(effect.tobytes(),(160,160),words,out/'charge_effect_088.png')
    require(np.array_equal(render(arc,99)[1],shift(render(arc,98)[1],1)),'Cyclone native shift differs');targets[99]=shift(targets[98],1)
    for n,src,delta in((88,89,-1),(99,98,1)):
        x,y,x2,y2=GUNS[src];meta[n]=dict(frames=[n,n],shared_body_frame=src,translation=[delta,0],pistol_present=True,pistol_mask_bbox=[x+delta,y,x2+delta,y2],native_effect_pixels=int(np.count_nonzero(effect))if n==88 else 0)
    board=Image.new('RGB',(1280,720),'#46545c');draw=ImageDraw.Draw(board)
    for i,n in enumerate([0]+FRAMES):
        v=targets[n]if n else master
        if n:save_image(v.tobytes(),(160,160),words,out/f'ultimate_{n:03}.png')
        rgba=np.concatenate((rgb[v].astype(np.uint8),((v>0)*255).astype(np.uint8)[...,None]),2);im=Image.fromarray(rgba).crop((40,32,120,112)).resize((320,320),Image.Resampling.NEAREST);x,y=i%4*320,i//4*360;board.paste(im,(x,y+28),im);draw.text((x+4,y+8),str(n)if n else'ACCEPTED IDLE',fill='white')
    board.save(out/'special_review_4x.png');return targets,[meta[n]for n in FRAMES]

def pack(arc,targets):
    g,c=entry(arc,2),entry(arc,3);bank=graphics_bank(g,0,allow_bank_aliases=True);changes={};replacements={};reports=[]
    for n in ORDER:
        f=bank['frames'][n];ns=[q['index']for q in bank['frames']if q['offset']==f['offset']];require(set(ns)<=set(FRAMES),'Unselected alias')
        raw=decode_stream(g,f['offset'],f['limit'],f['tile_count']*128).data;keep={q['tile']for v in ns for cb in(0,6,7,8)for q in composition_frame(c,cb,v)['parts']}
        pool={t for t in range(f['tile_count'])if t not in keep and t%16!=0};base=render(arc,n)[1]
        overlay=np.where((targets[n]==base)&(targets[n]!=15),0,targets[n]).astype(np.uint8)
        new,rr=pack_shared(raw,f['tile_count'],[overlay],pool,[len(pool)])
        for v in ns:
            delta=-1 if v==88 else 1 if v==99 else 0
            rows=[(t,x+delta,y,fl)for t,x,y,fl in rr[0]]
            changes[v]=b''.join(struct.pack('<BBbb',fl,t,x-80,y-80)for t,x,y,fl in rows);replacements[v]=encode_stream(new)
        reports.append(dict(frames=ns,source_frame=n,free_tiles=len(pool),parts=len(rr[0]),translated_shared_tiles=True));print(json.dumps(reports[-1]),flush=True)
    nc,slack=repack_parts(c,5,changes);ng,rep=repack_graphics_bank(g,0,replacements);result=replace_entry(replace_entry(arc,2,ng),3,nc);check=verify(arc,result,targets,{})
    return result,dict(packing=reports,graphics_repack=rep,parts_bank5_remaining=slack,verification=check)

def prepare(out,art_only=False):
    out=out.resolve();require(out.is_relative_to(D)and not out.exists(),'Fresh isolated output required');require(digest(PARENT/'rin_nana.bin')==PARENT_SHA and digest(PARENT/'PL02_U.ARC')==ARC_SHA,'Parent changed');out.mkdir();targets,proof=artwork(out);write(out/'registration.json',proof)
    if art_only:return
    result,packed=pack((PARENT/'PL02_U.ARC').read_bytes(),targets);(out/'PL02_U.ARC').write_bytes(result);write(out/'recipe.json',dict(task='ultimate_armor_nana',kind='ultimate_special',parent_sha256=PARENT_SHA,parent_arc_sha256=ARC_SHA,generated_sha256=SOURCE_SHA,frames=FRAMES,registration=proof,**packed,files={'PL02_U.ARC':sha256(result)},full_ultimate_complete=False));print(json.dumps(dict(output=str(out),sha256=sha256(result),verification=packed['verification'])))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--art-only',action='store_true');a=p.parse_args();prepare(a.output,a.art_only)
