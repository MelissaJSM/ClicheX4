"""호버 상체는 수용 공중 자세를 보존하고 새 다리를 추진 위치에 등록한다."""
import argparse,json,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import numpy as np
from PIL import Image,ImageDraw
from scipy.ndimage import label,binary_erosion
from scripts.prepare_nana_ultimate_hover_reference import PARENT,PARENT_SHA,ARC_SHA,FRAMES,ORDER,REUSE,CUTS
from scripts.prepare_nana_fourth_pilot import entry,render,require,write
from scripts.prepare_nana_ultimate_shot_arm import D,full,pack_resources
from scripts.prepare_nana_ultimate_run_detail import register_shaded_legs
from scripts.prepare_nana_pilot import normalize
from scripts.prepare_shibuki_ultimate_production import pack_shared,repack_parts,records
from scripts.prepare_riko_ui import replace_entry
from scripts.extract_zero import save_image
from scripts.project import digest
from scripts.discover_inputs import sha256
from src.psx_player import graphics_bank,composition_frame,decode_stream,bank_offsets
from src.psx_compress import encode_stream
from src.psx_bank_repack import repack_graphics_bank

def base_images():
    fourth=(PARENT/'modified.arc').read_bytes()
    return {n:render(fourth,n)[1]for n in FRAMES}

def correct_base(arc):
    require(sha256(arc)==ARC_SHA,'Unsupported hover parent');images=base_images();g,c=entry(arc,2),entry(arc,3);bank=graphics_bank(g,0,allow_bank_aliases=True);changes={};replacements={};proof=[]
    for n in ORDER:
        f=bank['frames'][n];ns=[q['index']for q in bank['frames']if q['offset']==f['offset']];require(ns==[n,n+1],'Hover aliases changed');raw=decode_stream(g,f['offset'],f['limit'],f['tile_count']*128).data
        protected={q['tile']for v in ns for b in(5,6,7,8)for q in composition_frame(c,b,v)['parts']};pool={q['tile']for v in ns for q in composition_frame(c,0,v)['parts']}-protected
        pool={t for t in pool if t%16!=0};new,rr=pack_shared(raw,f['tile_count'],[images[v]for v in ns],pool,[len(pool)]*2)
        for v,parts in zip(ns,rr):changes[v]=b''.join(struct.pack('<BBbb',fl,t,x-80,y-80)for t,x,y,fl in parts);replacements[v]=encode_stream(new)
        proof.append(dict(frames=ns,pool=sorted(pool),parts=[len(q)for q in rr]))
    nc,slack=repack_parts(c,0,changes);ng,rep=repack_graphics_bank(g,0,replacements);newarc=replace_entry(replace_entry(arc,2,ng),3,nc)
    protected_graphics=0
    for bi in range(len(bank_offsets(g,allow_aliases=True))):
        oldbank=graphics_bank(g,bi,allow_bank_aliases=True);newbank=graphics_bank(ng,bi,allow_bank_aliases=True)
        for a,b in zip(oldbank['frames'],newbank['frames']):
            old=decode_stream(g,a['offset'],a['limit'],a['tile_count']*128).data;new=decode_stream(ng,b['offset'],b['limit'],b['tile_count']*128).data
            if bi==0 and a['index']in FRAMES:continue
            require(old==new,'Unselected base graphics changed');protected_graphics+=1
    for cb in range(len(bank_offsets(c))):
        for n in range(composition_frame(c,cb,0)['bank_frame_count']):
            if cb==0 and n in FRAMES:continue
            require(records(c,cb,n)==records(nc,cb,n),'Other base composition changed')
    from scripts.prepare_shibuki_capsule_nova import raster
    for n in FRAMES:
        require(np.array_equal(render(newarc,n)[1],images[n]),'Nana hover base differs')
        for cb in(5,6,7,8):require(np.array_equal(raster(g,c,0,cb,n),raster(ng,nc,0,cb,n)),'Other layer pixels changed')
    return newarc,dict(frames=FRAMES,source='accepted Fourth Nana base layer only; legs remain Ultimate overlay',packing=proof,protected_graphics=protected_graphics,parts_slack=slack,graphics_repack=rep)

def artwork(out):
    src=D/'hover_v1/generated.png';provenance=json.loads((src.parent/'provenance.json').read_text('utf8'));require(digest(src)==provenance['sha256'],'Source changed');source=Image.open(src).convert('RGBA');arc=(PARENT/'PL02_U.ARC').read_bytes();fourth=(PARENT/'modified.arc').read_bytes();bases=base_images();master=full(arc,0);yy,xx=np.indices(master.shape);words=struct.unpack_from('<16H',entry(arc,9),32);rgb=np.array([[(w>>s&31)*255//31 for s in(0,5,10)]for w in words],np.int32);targets={};meta=[]
    air_meta=json.loads((PARENT/'ultimate_air/registration.json').read_text('utf8'))
    for i,n in enumerate(ORDER):
        reuse=REUSE[n];upper=full(arc,reuse);shot=full(arc,reuse+1);cut=CUTS[n];eye=np.nonzero((render(arc,reuse)[1]==14)&(yy<85));ex,ey=round(float(np.median(eye[1]))),round(float(np.median(eye[0])))
        cell=source.crop((i*source.width//5,0,(i+1)*source.width//5,source.height));a=np.array(cell);labs,_=label(a[:,:,3]>=192,np.ones((3,3)));sizes=np.bincount(labs.flat);sizes[0]=0;keep=labs==sizes.argmax();sy,sx=np.nonzero(keep);a[~keep,3]=0;crop=Image.fromarray(a).crop((sx.min(),sy.min(),sx.max()+1,sy.max()+1));ca=np.array(crop).astype(np.int32);cyy,_=np.indices(ca.shape[:2]);gy,gx=np.nonzero((ca[:,:,1]>ca[:,:,0]+6)&(ca[:,:,1]>ca[:,:,2]+6)&(ca[:,:,3]>=192)&(cyy<crop.height*.6));require(len(gx)>0,'Hover eye missing')
        silhouette=full(fourth,n);bottom=int(np.nonzero(silhouette)[0].max());choices=[]
        for h in range(40,75):
            w=round(h*crop.width/crop.height);cx=round((float(np.median(gx))+.5)*w/crop.width-.5);cy=round((float(np.median(gy))+.5)*h/crop.height-.5);choices.append((abs(h-1-cy-(bottom-ey)),h,w,cx,cy))
        _,h,w,cx,cy=min(choices);v=normalize(crop,h,rgb,width=w);generated=np.zeros_like(upper);dx,dy=ex-cx,ey-cy;generated[dy:dy+h,dx:dx+w]=v
        # Register whole authored rows between hip and propulsion foot without
        # stretching their widths or inheriting the Fourth dress hem.
        lower=generated.copy();lower[:cut]=0;lower[bottom+1:]=0
        source_foot=np.flatnonzero(lower[bottom]);dest_foot=np.flatnonzero(silhouette[bottom]);require(len(source_foot)>0,'Generated foot row missing')
        foot_shift=round(float(dest_foot.mean()-source_foot.mean()));oldrow=np.flatnonzero(upper[cut-1]>0);oldrow=oldrow[oldrow<90];newrow=np.flatnonzero(lower[cut]>0);newrow=newrow[newrow<90];require(len(oldrow)>0 and len(newrow)>0,'Hip seam missing');hip_shift=round(float(oldrow.mean()-newrow.mean()))
        for y in range(cut,bottom+1):
            t=(y-cut)/max(1,bottom-cut);shift=round(hip_shift*(1-t)+foot_shift*t);row=lower[y].copy();lower[y]=0
            if shift>=0:lower[y,shift:]=row[:160-shift]
            else:lower[y,:shift]=row[-shift:]
        for f,up in((n,upper),(n+1,shot)):
            target=up.copy();target[cut:]=lower[cut:];rim=(target>0)&~binary_erosion(target>0,np.ones((3,3),bool))&(target==5)&(yy>=cut);target[rim]=1;require(not np.any((bases[f]>0)&(target==0)),'Base escapes hover');require(np.array_equal(target[:cut],up[:cut]),'Accepted upper changed');require(int(np.nonzero(target)[0].max())==bottom,'Hover foot moved');targets[f]=target;save_image(target.tobytes(),(160,160),words,out/f'ultimate_{f:03}.png')
        q=next(q for q in air_meta if q['frames'][0]==reuse);box=q['pistol_mask_bbox'];x,y,x2,y2=box;require(np.array_equal(targets[n+1][y:y2,x:x2],bases[n+1][y:y2,x:x2]),'Hover pistol differs')
        meta.append(dict(frames=[n,n+1],reuse_sources=[reuse,reuse+1],upper_preserved_before_y=cut,sole=bottom,eye=[ex,ey],source_size=[w,h],source_crop_size=list(crop.size),pistol_present=True,pistol_mask_bbox=box,propulsion_foot_center=float(dest_foot.mean()),foot_shift=foot_shift,hip_shift=hip_shift,leg_skin_counts={str(k):int(np.count_nonzero((targets[n]==k)&(yy>=cut)))for k in(10,11,12,13)}))
    board=Image.new('RGB',(1600,720),'#46545c');draw=ImageDraw.Draw(board)
    for i,n in enumerate(FRAMES):
        v=targets[n];im=Image.fromarray(np.concatenate((rgb[v].astype(np.uint8),((v>0)*255).astype(np.uint8)[...,None]),2));pic=im.crop((40,36,120,116)).resize((320,320),Image.Resampling.NEAREST);x=i//2*320;y=i%2*360;board.paste(pic,(x,y+28),pic);draw.text((x+4,y+8),str(n),fill='white')
    board.save(out/'hover_review_4x.png');return targets,meta

def prepare(out,art_only=False):
    out=out.resolve();require(out.is_relative_to(D)and not out.exists(),'Fresh output required');require(digest(PARENT/'rin_nana.bin')==PARENT_SHA and digest(PARENT/'PL02_U.ARC')==ARC_SHA,'Parent changed');out.mkdir();targets,meta=artwork(out);write(out/'registration.json',meta)
    if art_only:return
    base,proof=correct_base((PARENT/'PL02_U.ARC').read_bytes());result,packed=pack_resources(base,targets,FRAMES);(out/'PL02_U.ARC').write_bytes(result);write(out/'recipe.json',dict(task='ultimate_armor_nana',kind='ultimate_hover',parent_sha256=PARENT_SHA,parent_arc_sha256=ARC_SHA,generated_sha256=digest(D/'hover_v1/generated.png'),frames=FRAMES,registration=meta,base_correction=proof,**packed,files={'PL02_U.ARC':sha256(result)},full_ultimate_complete=False));print(json.dumps(dict(output=str(out),sha256=sha256(result),verification=packed['verification'])))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--art-only',action='store_true');a=p.parse_args();prepare(a.output,a.art_only)
