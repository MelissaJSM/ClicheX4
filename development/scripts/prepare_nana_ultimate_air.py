"""수용 얼티밋 크기·명암으로 공중22참조를 제작하고 고정 은행 안에 넣는다."""
import argparse,json,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import numpy as np
from PIL import Image,ImageDraw
from scipy.ndimage import label,distance_transform_edt
from scripts.prepare_nana_fourth_pilot import entry,require,render,write
from scripts.prepare_nana_pilot import normalize
from scripts.prepare_nana_ultimate_run_detail import register_shaded_legs
from scripts.prepare_nana_ultimate_run import verify
from scripts.prepare_shibuki_ultimate_production import pack_shared,repack_parts
from scripts.prepare_shibuki_capsule_nova import raster
from scripts.prepare_riko_ui import replace_entry
from scripts.extract_zero import save_image
from scripts.project import digest
from scripts.discover_inputs import sha256
from src.psx_player import graphics_bank,composition_frame,decode_stream
from src.psx_bank_repack import repack_graphics_bank
from src.psx_compress import encode_stream

D=ROOT/'work/ver_rin_nana/nana_ultimate_armor'
PARENT=ROOT/'out/ver_rin_nana/nana_ultimate_run_20261031T004636981571Z'
PARENT_SHA='c10ab446d3bf60cbc66d658516bf28173a46368133edc81110214c516b05c5af'
ARC_SHA='5efe5ac3f64776e1612d3aa0a616c2c3f7ae4a5299f040cabc083c6b1a0f3d90'
SOURCE_SHA='ca9d8efaa0181d6c29cd69857f8a41bd3fff191a0e955440070aefe91bd8827b'
FRAMES=list(range(33,55));ORDER=FRAMES[::2]

def artwork(out):
    path=D/'air_v1/generated_transparent.png';require(digest(path)==SOURCE_SHA,'Source changed')
    source=Image.open(path).convert('RGBA');require(source.getchannel('A').getextrema()==(0,255),'Transparent source required')
    arc=(PARENT/'PL02_U.ARC').read_bytes();words=struct.unpack_from('<16H',entry(arc,9),32);rgb=np.array([[(w>>s&31)*255//31 for s in (0,5,10)] for w in words],np.int32)
    master=np.array(Image.open(D/'start_v2/ultimate_000.png'));yy,xx=np.indices(master.shape);targets={};proof=[]
    fourth=(PARENT/'modified.arc').read_bytes();fg,fc=entry(fourth,2),entry(fourth,3)
    for i,n in enumerate(ORDER):
        base=render(arc,n)[1];shot=render(arc,n+1)[1];ey,ex=np.nonzero((base==14)&(yy<80));require(len(ex)>0,'Native eye missing');eye_x=int(round(float(np.median(ex))));eye_y=int(round(float(np.median(ey))));bottom=int(np.nonzero(base)[0].max())
        cell=source.crop((i%4*source.width//4,i//4*source.height//3,(i%4+1)*source.width//4,(i//4+1)*source.height//3));a=np.array(cell);ls,count=label(a[:,:,3]>=192,np.ones((3,3)));sizes=np.bincount(ls.flat);sizes[0]=0;keep=ls==sizes.argmax();sy,sx=np.nonzero(keep);a[~keep,3]=0;crop=Image.fromarray(a).crop((sx.min(),sy.min(),sx.max()+1,sy.max()+1))
        choices=[]
        for h in range(32,64):
            v=normalize(crop,h,rgb);vy,vx=np.nonzero((v==14)&(np.indices(v.shape)[0]<h//2))
            if not len(vx):continue
            cy,cx=float(np.median(vy)),float(np.median(vx));choices.append((abs(h-1-cy-(bottom-eye_y)),abs(cy-16),v,cx,cy))
        require(bool(choices),'Generated eye missing');_,_,v,cx,cy=min(choices,key=lambda q:q[:2]);dx=eye_x-round(cx);dy=eye_y-round(cy);require(min(dx,dy)>=0 and dx+v.shape[1]<=160 and dy+v.shape[0]<=160,'Art outside canvas');target=np.zeros_like(base);target[dy:dy+v.shape[0],dx:dx+v.shape[1]]=v
        # Head scale is independent of the raised hand and bent knees.
        head_left=eye_x-5;head_right=eye_x+11;target[:eye_y+5,head_left:head_right]=0
        ratio=min(1.,16/max(cy,1))
        for y in range(eye_y-16,eye_y+5):
            sy=round(cy+(y-eye_y)*(cy/16 if y<=eye_y else 1));sy=max(0,min(v.shape[0]-1,sy));row=v[sy];width=max(1,round(len(row)*ratio));r=np.array(Image.fromarray(row[None,:]).resize((width,1),Image.Resampling.NEAREST))[0];x=eye_x-round(cx*ratio)
            lo=max(x,head_left);hi=min(x+width,head_right)
            if hi>lo:target[y,lo:hi]=r[lo-x:hi-x]
        tail_y=eye_y+15;tail_x=eye_x+11;old_right=int(np.nonzero(target[:tail_y])[1].max())+1;new_right=int(np.nonzero(base[:tail_y])[1].max())+1
        if old_right>new_right and new_right>tail_x:
            patch=target[:tail_y,tail_x:old_right].copy();target[:tail_y,tail_x:]=0;target[:tail_y,tail_x:new_right]=np.array(Image.fromarray(patch).resize((new_right-tail_x,tail_y),Image.Resampling.NEAREST))
        fx,fy=eye_x-76,eye_y-68;target[65+fy:74+fy,73+fx:83+fx]=master[65:74,73:83]
        accepted=raster(fg,fc,0,0,n)
        for cb in (8,5,7,6):
            layer=raster(fg,fc,0,cb,n);accepted=np.where(layer,layer,accepted)
        legmask=register_shaded_legs(target,base,eye_x,eye_y,np.isin(accepted,(10,11,12,13)),yy>=eye_y+17)
        dist,nearest=distance_transform_edt(target==0,return_indices=True);missing=(base>0)&(target==0);require(dist[missing].max(initial=0)<=7,f'Pose {n} needs registration redraw')
        target[missing]=target[nearest[0][missing],nearest[1][missing]]
        # Copy the accepted pistol/hand at its exact original muzzle anchor;
        # only the costume sleeve is pink, with an explicit shoulder join.
        gy,gx=np.nonzero(base!=shot);gun_end=int(gx.min())+6;gun=(xx>=gx.min())&(xx<eye_x+1)&(yy>=eye_y+2)&(yy<eye_y+10);firing=target.copy();firing[gun]=shot[gun];lowered=(xx<eye_x+1)&(yy>=eye_y+10)&(yy<eye_y+18);firing[lowered]=shot[lowered]
        sleeve=gun&(xx>=gun_end)&(xx<eye_x)&np.isin(firing,(2,3,4));firing[sleeve]=np.choose(firing[sleeve]-2,[7,8,9]);stray=(shot>0)&(firing==0);firing[stray]=shot[stray];bridges=[]
        for y in range(eye_y+3,eye_y+8):
            row=firing[y];left=np.flatnonzero(row[eye_x-10:eye_x-2])+eye_x-10;right=np.flatnonzero(row[eye_x:eye_x+6])+eye_x
            if len(left) and len(right) and 0<int(right.min()-left.max()-1)<=5:
                for x in range(int(left.max()+1),int(right.min())):
                    if not row[x]:row[x]=7;bridges.append([x,y])
        box=[int(gx.min()),int(gy.min()),gun_end,int(gy.max()+1)];x,y,x2,y2=box;require(np.array_equal(firing[y:y2,x:x2],shot[y:y2,x:x2]),'Pistol moved')
        for f,b,t in ((n,base,target),(n+1,shot,firing)):
            require(not np.any((b>0)&(t==0)),'Base escapes overlay');require(int(np.nonzero(t)[0].max())==bottom,'Sole shifted');targets[f]=t;save_image(t.tobytes(),(160,160),words,out/f'ultimate_{f:03}.png')
        proof.append({'frames':[n,n+1],'eye':[eye_x,eye_y],'sole':bottom,'generated_size':list(v.shape[::-1]),'head_registration_eye_to_ear':16,'face_source':'accepted Ultimate idle','leg_shading':'generated shaded pixels retargeted to accepted knee/foot silhouette','skin_counts':{str(k):int(np.count_nonzero((target==k)&legmask)) for k in (10,11,12,13)},'registration_extension_pixels':int(missing.sum()),'registration_max_distance':float(dist[missing].max(initial=0)),'pistol_mask_bbox':box,'pistol_exact':True,'shoulder_bridge_pixels':bridges})
    for firing,name in ((False,'air_review_4x.png'),(True,'air_shoot_review_4x.png')):
        board=Image.new('RGB',(1280,1024),'#252c3c');draw=ImageDraw.Draw(board)
        for i,n in enumerate([*ORDER,0]):
            f=n+int(firing) if n else 0;path=out/f'ultimate_{f:03}.png' if n else D/'start_v2/ultimate_000.png';pic=Image.open(path).convert('RGBA').crop((40,36,120,116)).resize((320,320),Image.Resampling.NEAREST);x=i%4*320;y=i//4*340;board.paste(pic,(x,y+20),pic);draw.text((x+6,y+3),str(f) if n else 'ACCEPTED IDLE',fill='white')
        board.save(out/name)
    return targets,proof

def prepare(out,art_only=False):
    out=out.resolve();require(out.is_relative_to(D) and not out.exists(),'Fresh isolated output required');require(digest(PARENT/'rin_nana.bin')==PARENT_SHA and digest(PARENT/'PL02_U.ARC')==ARC_SHA,'Parent changed')
    approval=json.loads((ROOT/'projects/ver_rin_nana/nana_ultimate_candidate.json').read_text('utf8'));require(approval['full_animation_production_approved'] and approval['run_art_user_accepted'],'Accepted style required');out.mkdir();targets,registration=artwork(out);write(out/'registration.json',registration)
    if art_only:return
    arc=(PARENT/'PL02_U.ARC').read_bytes();g,c=entry(arc,2),entry(arc,3);bank=graphics_bank(g,0,allow_bank_aliases=True);replacements={};changes={};reports=[]
    for n in ORDER:
        f=bank['frames'][n];ns=[q['index'] for q in bank['frames'] if q['offset']==f['offset']];require(ns==[n,n+1],'Unexpected aliases');old=decode_stream(g,f['offset'],f['limit'],f['tile_count']*128).data;keep={q['tile'] for v in ns for cb in (0,6,7,8) for q in composition_frame(c,cb,v)['parts']};pool=set(range(f['tile_count']))-keep;limits=[min(len(pool),len(composition_frame(c,5,v)['parts'])+3) for v in ns];overlays=[]
        for v in ns:
            base=raster(g,c,0,0,v);overlays.append(np.where((targets[v]==base)&(base!=15),0,targets[v]).astype(np.uint8))
        raw,rr=pack_shared(old,f['tile_count'],overlays,pool,limits)
        for v,parts in zip(ns,rr):changes[v]=b''.join(struct.pack('<BBbb',flag,t,x-80,y-80) for t,x,y,flag in parts);replacements[v]=encode_stream(raw)
        reports.append({'frames':ns,'tiles':f['tile_count'],'free_tiles':len(pool),'parts':[len(r) for r in rr]});print(json.dumps(reports[-1]),flush=True)
    nc,slack=repack_parts(c,5,changes);ng,repack=repack_graphics_bank(g,0,replacements);result=replace_entry(replace_entry(arc,2,ng),3,nc);check=verify(arc,result,targets,{})
    (out/'PL02_U.ARC').write_bytes(result);write(out/'recipe.json',{'task':'ultimate_armor_nana','kind':'ultimate_air','parent_sha256':PARENT_SHA,'parent_arc_sha256':ARC_SHA,'generated_sha256':SOURCE_SHA,'frames':FRAMES,'registration':registration,'packing':reports,'graphics_repack':repack,'parts_bank5_remaining':slack,'verification':check,'files':{'PL02_U.ARC':sha256(result)},'full_ultimate_complete':False});print(json.dumps({'output':str(out),'verification':check,'sha256':sha256(result)}))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--art-only',action='store_true');a=p.parse_args();prepare(a.output,a.art_only)
