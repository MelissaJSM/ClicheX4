"""피격·저체력15참조를 같은 의상으로 등록하고 공통 효과를 보존한다."""
import argparse,json,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import numpy as np
from PIL import Image,ImageDraw
from scipy.ndimage import label,distance_transform_edt
from scripts.prepare_nana_fourth_pilot import entry,render,require,write
from scripts.prepare_nana_fourth_reaction_art import face_anchor
from scripts.prepare_nana_ultimate_shot_arm import D,full,pack_resources
from scripts.prepare_nana_ultimate_run_detail import register_shaded_legs
from scripts.prepare_nana_ultimate_run import verify
from scripts.prepare_shibuki_ultimate_production import pack_shared,repack_parts,records
from scripts.prepare_shibuki_capsule_nova import raster
from scripts.prepare_riko_ui import replace_entry
from scripts.prepare_nana_pilot import normalize
from scripts.project import digest
from scripts.discover_inputs import sha256
from scripts.extract_zero import save_image
from src.psx_player import graphics_bank,composition_frame,decode_stream
from src.psx_sprite_batch import canvas_from_parts
from src.psx_ui_atlas import local_composition
from src.psx_bank_repack import repack_graphics_bank
from src.psx_compress import encode_stream
PARENT=ROOT/'out/ver_rin_nana/nana_ultimate_air_transition_20261104T094101726771Z'
PARENT_SHA='ba510c559b8589b22a014fc5303dcca846d8b9c6659107c825b8cc11199dcdb0'
ARC_SHA='abb514ccf0ca70c9eb4fa2ff1aec6e1ca7f55337e7a495cacdb5c56fb6114f14'
SOURCE_SHA='8b14f5f3d4818c75ada996d8ebfc028acf17debd45ec08f5eff90ceb0fc29009'
FRAMES=[106,107,108,110,111,*range(120,126),*range(233,237)]
ORDER=[106,110,122,233,234]

def source_face(crop,base,ex,ey):
    a=np.array(crop).astype(np.int32);yy,xx=np.indices(a.shape[:2]);r,g,b=a[:,:,:3].transpose(2,0,1);upper=(a[:,:,3]>=192)&(yy<crop.height*.47);green=upper&(g>r+8)&(g>b+8)
    gy,gx=np.nonzero(green);ny,nx=np.nonzero((base==14)&(np.indices(base.shape)[0]<80))
    if len(gx)and len(nx):return float(np.median(gx)),float(np.median(gy)),ex-float(np.median(nx)),ey-float(np.median(ny))
    skin=upper&(r>g+10)&(g>b+10)&(g>90);labs,count=label(skin,np.ones((3,3)));sizes=np.bincount(labs.flat);sizes[0]=0;require(count and sizes.max()>10,'Source face missing');y,x=np.nonzero(labs==sizes.argmax());return float(x.mean()),float(y.mean()),0,0

def effects(arc,n):
    if n not in(107,108):return np.zeros((160,160),np.uint8),[]
    g,c=entry(arc,2),entry(arc,3);core={p['tile']for p in composition_frame(c,5,106)['parts']};comp=composition_frame(c,5,n);ps=[p for p in comp['parts']if p['tile']not in core];f=graphics_bank(g,0,allow_bank_aliases=True)['frames'][n];raw=decode_stream(g,f['offset'],f['limit'],f['tile_count']*128).data
    return canvas_from_parts(raw,f['tile_count'],local_composition({**comp,'parts':ps})),ps

def artwork(out):
    src=D/'reaction_v1/generated.png';require(digest(src)==SOURCE_SHA,'Source changed');source=Image.open(src).convert('RGBA');require(source.getchannel('A').getextrema()==(0,255),'Transparent source required');arc=(PARENT/'PL02_U.ARC').read_bytes();fourth=(PARENT/'modified.arc').read_bytes();words=struct.unpack_from('<16H',entry(arc,9),32);rgb=np.array([[(w>>s&31)*255//31 for s in(0,5,10)]for w in words],np.int32);yy,xx=np.indices((160,160));masters={};meta={};targets={};proof=[]
    for i,n in enumerate(ORDER):
        base=render(arc,n)[1];ex,ey,face=face_anchor(base);ys,xs=np.nonzero(base);top,bottom=int(ys.min()),int(ys.max());width=int(xs.max()-xs.min()+3);cell=source.crop((i*source.width//5,0,(i+1)*source.width//5,source.height));a=np.array(cell);labs,_=label(a[:,:,3]>=192,np.ones((3,3)));sizes=np.bincount(labs.flat);sizes[0]=0;keep=labs==sizes.argmax();sy,sx=np.nonzero(keep);a[~keep,3]=0;crop=Image.fromarray(a).crop((sx.min(),sy.min(),sx.max()+1,sy.max()+1));choices=[]
        sx,sy,ox,oy=source_face(crop,base,ex,ey)
        for h in range(36,62):
            v=normalize(crop,h,rgb,width=width);cx=round((sx+.5)*width/crop.width-.5+ox);cy=round((sy+.5)*h/crop.height-.5+oy);choices.append((abs(h-1-cy-(bottom-ey)),abs(cy-18),v,cx,cy))
        _,_,v,cx,cy=min(choices,key=lambda q:q[:2]);dx,dy=ex-cx,ey-cy;target=np.zeros_like(base);require(min(dx,dy)>=0 and dx+v.shape[1]<=160 and dy+v.shape[0]<=160,'Outside canvas');target[dy:dy+v.shape[0],dx:dx+v.shape[1]]=v
        # The facial anchor is two rows below the eye; keep ear-to-eye scale.
        upper=target[:ey+4].copy();target[:ey+4]=0
        for y in range(ey-18,ey+4):
            sy=round(ey+(y-ey)*(cy/18 if y<=ey else 1));target[y]=upper[max(0,min(upper.shape[0]-1,sy))]
        x,y,x2,y2=face;target[y:y2,x:x2]=base[y:y2,x:x2]
        low=ey+{106:18,110:15,122:19,233:19,234:18}[n];register_shaded_legs(target,base,ex,ey,np.isin(full(fourth,n),(10,11,12,13)),yy>=low)
        gun=[70,80,77,88]if n==122 else None
        if gun:
            x,y,x2,y2=gun;target[y:y2,x:x2]=base[y:y2,x:x2]
        dist,near=distance_transform_edt(target==0,return_indices=True);missing=(base>0)&(target==0)
        save_image(target.tobytes(),(160,160),words,out/f'registered_{n:03}.png')
        print(json.dumps(dict(frame=n,face=[ex,ey],source_face=[cx,cy],source_size=list(v.shape[::-1]),max_distance=float(dist[missing].max(initial=0)),far_pixels=[[int(x),int(y)]for y,x in np.argwhere(missing&(dist>7))])),flush=True)
        require(dist[missing].max(initial=0)<=7,f'Pose {n} needs redraw');target[missing]=target[near[0][missing],near[1][missing]];x,y,x2,y2=face;target[y:y2,x:x2]=base[y:y2,x:x2]
        if gun:
            x,y,x2,y2=gun;target[y:y2,x:x2]=base[y:y2,x:x2]
        lab,count=label(target>0,np.ones((3,3)))
        for k in range(1,count+1):
            m=lab==k
            if np.count_nonzero(m)<=2 and not np.any(base[m]):target[m]=0
        require(not np.any((base>0)&(target==0)),'Base escapes');require(int(np.nonzero(target)[0].max())==bottom,'Sole moved');masters[n]=target;save_image(target.tobytes(),(160,160),words,out/f'body_{n:03}.png');meta[n]=dict(body_frame=n,face_anchor=[ex,ey],face_box=face,sole=bottom,lower_silhouette_from_y=low,head_face_to_ear=18,source_size=list(v.shape[::-1]),source_face=[cx,cy],pistol_mask_bbox=gun,pistol_present=bool(gun),registration_max_distance=float(dist[missing].max(initial=0)))
    for n in FRAMES:
        core=106 if n in(106,107,108) else 110 if n in(110,111) else 122 if 120<=n<=125 else 233 if n==233 else 234;body=masters[core].copy();q=meta[core].copy();delta={120:1,121:1,124:-1,125:-1}.get(n,0);base=raster(entry(arc,2),entry(arc,3),0,0,n)
        if core==122:
            origin=body.copy()
            for y in range(160):
                shift=delta if y<90 else round(delta*max(0,98-y)/8);sy=y-shift;body[y]=origin[sy]if 0<=sy<160 else 0
            x,y,x2,y2=q['face_box'];y+=delta;y2+=delta;body[y:y2,x:x2]=base[y:y2,x:x2];q['face_box']=[x,y,x2,y2];x,y,x2,y2=q['pistol_mask_bbox'];y+=delta;y2+=delta;body[y:y2,x:x2]=base[y:y2,x:x2];q['pistol_mask_bbox']=[x,y,x2,y2];dist,near=distance_transform_edt(body==0,return_indices=True);missing=(base>0)&(body==0);require(dist[missing].max(initial=0)<=2,'Breathing loses native coverage');body[missing]=body[near[0][missing],near[1][missing]]
        target=np.where(body,body,base).astype(np.uint8);fx,parts=effects(arc,n);target=np.where(fx,fx,target).astype(np.uint8);targets[n]=target;q.update(frames=[n,n],breathing_delta=delta,effect_parts_preserved=len(parts));proof.append(q);save_image(target.tobytes(),(160,160),words,out/f'ultimate_{n:03}.png')
    board=Image.new('RGB',(1280,3*300),'#252c3c');draw=ImageDraw.Draw(board)
    for i,n in enumerate([0,106,110,122,233,234,107,108,111,120,124,235,236]):
        v=targets[n]if n else full(arc,0);rgba=np.concatenate((rgb[v].astype(np.uint8),((v>0)*255).astype(np.uint8)[...,None]),axis=2);im=Image.fromarray(rgba,'RGBA').crop((40,36,120,112)).resize((256,244),Image.Resampling.NEAREST);x,y=i%5*256,i//5*300;board.paste(im,(x,y+24),im);draw.text((x+4,y+4),str(n)if n else'ACCEPTED IDLE',fill='white')
    board.save(out/'reaction_review.png');return targets,proof

def pack(arc,targets):
    # 106/107/108 share one body and independent effect tiles17/18.
    # Preserve those tiles/records instead of baking three entire FX frames.
    g,c=entry(arc,2),entry(arc,3);bank=graphics_bank(g,0,allow_bank_aliases=True);replacements={};changes={};reports=[]
    for ns in([106,107,108],[110,111]):
        f=bank['frames'][ns[0]];require([q['index']for q in bank['frames']if q['offset']==f['offset']]==ns,'Aliases changed');raw=decode_stream(g,f['offset'],f['limit'],f['tile_count']*128).data;fxrows={n:effects(arc,n)[1]for n in ns};keep={p['tile']for n in ns for cb in(0,6,7,8)for p in composition_frame(c,cb,n)['parts']}|{p['tile']for ps in fxrows.values()for p in ps};pool=set(range(f['tile_count']))-keep;new,rr=pack_shared(raw,f['tile_count'],[targets[ns[0]]],pool,[len(pool)]);body=b''.join(struct.pack('<BBbb',fl,t,x-80,y-80)for t,x,y,fl in rr[0])
        for n in ns:
            fx=b''.join(c[p['record_offset']:p['record_offset']+4]for p in fxrows[n]);changes[n]=body+fx;replacements[n]=encode_stream(new)
        reports.append(dict(frames=ns,body_parts=len(rr[0]),effect_parts={str(n):len(fxrows[n])for n in ns},preserved_effect_tiles=sorted({p['tile']for ps in fxrows.values()for p in ps})))
    nc,slack=repack_parts(c,5,changes);ng,rep=repack_graphics_bank(g,0,replacements);intermediate=replace_entry(replace_entry(arc,2,ng),3,nc);remaining=[n for n in FRAMES if n not in changes];final,rest=pack_resources(intermediate,{n:targets[n]for n in remaining},remaining);check=verify(arc,final,targets,{})
    return final,dict(packing=reports+rest['packing'],graphics_repack=[rep,rest['graphics_repack']],parts_bank5_remaining=rest['parts_bank5_remaining'],verification=check)

def prepare(out,art_only=False):
    out=out.resolve();require(out.is_relative_to(D)and not out.exists(),'Fresh isolated output required');require(digest(PARENT/'rin_nana.bin')==PARENT_SHA and digest(PARENT/'PL02_U.ARC')==ARC_SHA,'Parent changed');out.mkdir();targets,proof=artwork(out);write(out/'registration.json',proof)
    if art_only:return
    result,packed=pack((PARENT/'PL02_U.ARC').read_bytes(),targets);(out/'PL02_U.ARC').write_bytes(result);write(out/'recipe.json',dict(task='ultimate_armor_nana',kind='ultimate_reaction',parent_sha256=PARENT_SHA,parent_arc_sha256=ARC_SHA,generated_sha256=SOURCE_SHA,frames=FRAMES,registration=proof,**packed,files={'PL02_U.ARC':sha256(result)},full_ultimate_complete=False));print(json.dumps(dict(output=str(out),sha256=sha256(result),verification=packed['verification'])))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--art-only',action='store_true');a=p.parse_args();prepare(a.output,a.art_only)
