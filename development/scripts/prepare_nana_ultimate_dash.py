"""승인 대기 크기·명암과 사랑이 공통 모듈로 대시18참조를 등록한다."""
import argparse,json,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import numpy as np
from PIL import Image,ImageDraw
from scipy.ndimage import label,distance_transform_edt
from scripts.prepare_nana_fourth_pilot import entry,require,render,write
from scripts.prepare_nana_pilot import normalize
from scripts.prepare_nana_ultimate_shot_arm import D,full,pack_resources
from scripts.prepare_nana_ultimate_run_detail import register_shaded_legs
from scripts.prepare_shibuki_ultimate_production import pack_shared,repack_parts,records
from scripts.prepare_shibuki_capsule_nova import raster
from scripts.prepare_riko_ui import replace_entry
from scripts.project import digest
from scripts.discover_inputs import sha256
from scripts.extract_zero import save_image
from src.psx_player import graphics_bank,composition_frame,decode_stream,indexed_atlas
from src.psx_bank_repack import repack_graphics_bank
from src.psx_compress import encode_stream
PARENT=ROOT/'out/ver_rin_nana/nana_ultimate_wall_arm_20261104T084704181151Z'
PARENT_SHA='b4e3684aef63b5cfa0a68e586762ea455e42fc63c8f2623cc4bcda179b356262'
ARC_SHA='357ff84ebb17c48700ca88cf4ae6a9983494a8110aec8265cc11c28ff671e543'
SOURCE_SHA='d6e744afc4b44e1b0601529a5b51dd67ae60ed6de1ba4d90667007c8dfc24572'
FRAMES=list(range(67,85));ORDER=[67,69,71,75,77,79,81,83]

def registration(arc):
    yy,xx=np.indices((160,160));result=[]
    for n in ORDER:
        base=render(arc,n)[1];shot=render(arc,n+1)[1];ys,xs=np.nonzero((base==14)&(yy<95));ex,ey=round(float(np.median(xs))),round(float(np.median(ys)));mx=int(np.nonzero((shot>0)&(xx<ex-8)&(yy<ey+12))[1].min());my=int(np.nonzero(np.isin(shot[ey-4:ey+12,mx:mx+6],(5,6,7,8,9)))[0].min())+ey-4
        result.append({'frames':[n,n+1],'eye':[ex,ey],'sole':int(np.nonzero(base)[0].max()),'muzzle_anchor':[mx,my],'gun_module_box':[mx,my-1,mx+8,my+6],'pistol_mask_bbox':[mx,my-1,mx+8,my+6]})
    return result

def correct_base(arc):
    require(sha256(arc)==ARC_SHA,'Wrong dash parent');g,c=entry(arc,2),entry(arc,3);bank=graphics_bank(g,0,allow_bank_aliases=True);changes={};streams={};proof=[];module=np.array(Image.open(PARENT/'ultimate_gun_size/pistol_module.png'));expected={}
    for q in registration(arc):
        n,shot=q['frames'];f=bank['frames'][n];aliases=[v['index']for v in bank['frames']if v['offset']==f['offset']];require(aliases==([71,72,73,74]if n==71 else[n,n+1]),'Unexpected dash aliases');raw=decode_stream(g,f['offset'],f['limit'],f['tile_count']*128).data
        keep={p['tile']for v in aliases for cb in(6,7,8)for p in composition_frame(c,cb,v)['parts']};keep|=({6}if n==71 else set());pool={p['tile']for v in(n,shot)for p in composition_frame(c,0,v)['parts']}-keep
        images=[raster(g,c,0,0,v)for v in(n,shot)];old=images[1].copy();x,y,x2,y2=q['gun_module_box'];images[1][y:y2,x:x2]=module;mx,my=q['muzzle_anchor'];ex,ey=q['eye'];rx=min(mx+12,ex-6);images[1][my-1:my+3,mx+8:rx]=0
        new,rr=pack_shared(raw,f['tile_count'],images,pool,[len(pool)]*2)
        for v,parts in zip((n,shot),rr):changes[v]=b''.join(struct.pack('<BBbb',fl,t,px-80,py-80)for t,px,py,fl in parts);expected[v]=images[v-n]
        if n==71:
            oldatlas=np.frombuffer(indexed_atlas(raw,f['tile_count'])[0],np.uint8).reshape(-1,256);newatlas=np.frombuffer(indexed_atlas(new,f['tile_count'])[0],np.uint8).reshape(-1,256);require(np.array_equal(oldatlas[:16,96:112],newatlas[:16,96:112]),'Speed-line tile changed')
            for v,source in((73,71),(74,72)):
                parts=composition_frame(c,0,v)['parts'];extra=[p for p in parts if p['tile']==6];require(len(extra)==9,'Unexpected speed-line layout');changes[v]=changes[source]+b''.join(struct.pack('<BBbb',p['flags'],p['tile'],p['x'],p['y'])for p in extra)
        for v in aliases:streams[v]=encode_stream(new)
        proof.append({**q,'changed_base_pixels':int(np.count_nonzero(old!=images[1])),'removed_old_gun_box':[mx+8,my-1,rx,my+3],'base_aliases':aliases,'base_parts':[len(p)for p in rr]})
    nc,_=repack_parts(c,0,changes);ng,_=repack_graphics_bank(g,0,streams);result=replace_entry(replace_entry(arc,2,ng),3,nc);newbank=graphics_bank(ng,0,allow_bank_aliases=True)
    for n in range(len(bank['frames'])):
        for cb in (0,6,7,8):
            try:old=raster(g,c,0,cb,n)
            except ValueError:
                require(n not in changes,'Invalid changed frame');f,nf=bank['frames'][n],newbank['frames'][n];require(decode_stream(g,f['offset'],f['limit'],f['tile_count']*128).data==decode_stream(ng,nf['offset'],nf['limit'],nf['tile_count']*128).data and records(c,cb,n)==records(nc,cb,n),'Placeholder changed');continue
            actual=raster(ng,nc,0,cb,n)
            if cb==0 and n in(73,74):
                before=raster(g,c,0,0,n-2);after=raster(ng,nc,0,0,n-2);allowed=before!=after;require(np.array_equal(old[~allowed],actual[~allowed]),'Speed-line/body pixels changed outside gun')
            else:require(np.array_equal(actual,expected.get(n,old)if cb==0 else old),'Unexpected base layer change')
    return result,proof

def materials(rgb):
    src=D/'hand_shot_review/generated.png';require(digest(src)=='229eab7f7882f956bd45ee8bbf59ca088f854da2b4ccf814a7d6b37aa909ab7f','Arm source changed');im=Image.open(src).convert('RGBA');v=normalize(im.crop((0,im.height//2,im.width//3,im.height)),40,rgb,width=60)
    def clean(a,allowed):
        good=np.isin(a,allowed);require(good.any(),'Missing arm material');_,p=distance_transform_edt(~good,return_indices=True);return a[p[0],p[1]]
    return clean(v[16:20,13:17],(10,11,12,13)),clean(v[16:20,18:20],(13,15)),clean(v[16:20,20:34],(5,6,7,8,9))

def artwork(out):
    arc=(PARENT/'PL02_U.ARC').read_bytes();require(sha256(arc)==ARC_SHA,'Parent changed');src=D/'dash_v1/generated.png';require(digest(src)==SOURCE_SHA,'Dash source changed');source=Image.open(src).convert('RGBA');words=struct.unpack_from('<16H',entry(arc,9),32);rgb=np.array([[(w>>s&31)*255//31 for s in(0,5,10)]for w in words],np.int32);master=full(arc,0);targets={};proof=registration(arc);yy,xx=np.indices((160,160));fourth=(PARENT/'modified.arc').read_bytes();leg_y={q['frame']:q['native_lower_silhouette_preserved_from_y']for q in json.loads((ROOT/'work/ver_rin_nana/nana_fourth_armor/dash_art_v4/layers.json').read_text('utf8'))['registration']};module=np.array(Image.open(PARENT/'ultimate_gun_size/pistol_module.png'));skin,cuff,sleeve=materials(rgb)
    for i,q in enumerate(proof):
        n,ns=q['frames'];base=render(arc,n)[1];shot=render(arc,ns)[1];ex,ey=q['eye'];bottom=q['sole'];cell=source.crop((i%4*source.width//4,i//4*source.height//2,(i%4+1)*source.width//4,(i//4+1)*source.height//2));a=np.array(cell);labs,_=label(a[:,:,3]>=192,np.ones((3,3)));sizes=np.bincount(labs.flat);sizes[0]=0;keep=labs==sizes.argmax();sy,sx=np.nonzero(keep);a[~keep,3]=0;crop=Image.fromarray(a).crop((sx.min(),sy.min(),sx.max()+1,sy.max()+1));choices=[]
        ca=np.array(crop).astype(np.int32);sy,sx=np.indices(ca.shape[:2]);eye=(ca[:,:,1]>ca[:,:,0]+5)&(ca[:,:,1]>ca[:,:,2]+5)&(ca[:,:,3]>=192)&(sy<crop.height*.65);vy,vx=np.nonzero(eye);require(len(vx)>0,'Source eye missing');source_cx,source_cy=float(np.median(vx)),float(np.median(vy))
        for h in range(30,65):
            width=int(np.ptp(np.nonzero(base)[1]))+3;v=normalize(crop,h,rgb,width=width);cx=(source_cx+.5)*width/crop.width-.5;cy=(source_cy+.5)*h/crop.height-.5;choices.append((abs(h-1-cy-(bottom-ey)),abs(cy-16),v,cx,cy))
        require(choices,'Missing eye');_,_,v,cx,cy=min(choices,key=lambda z:z[:2]);dx,dy=ex-round(cx),ey-round(cy);target=np.zeros_like(base);target[dy:dy+v.shape[0],dx:dx+v.shape[1]]=v
        # Register physical head size independently of the crouched leg height.
        target[:ey+5,ex-10:ex+15]=0;target[ey-16:ey+5,ex-9:ex+14]=master[52:73,67:90]
        lower=yy>=leg_y[n];accepted=full(fourth,n);register_shaded_legs(target,base,ex,ey,np.isin(accepted,(10,11,12,13)),lower)
        dist,p=distance_transform_edt(target==0,return_indices=True);missing=(base>0)&(target==0)
        if dist[missing].max(initial=0)>9:
            save_image(target.tobytes(),(160,160),words,out/f'registration_failed_{n:03}.png');print(json.dumps({'frame':n,'size':list(v.shape[::-1]),'generated_eye':[cx,cy],'native_eye':[ex,ey],'maximum_distance':float(dist[missing].max()),'furthest':np.argwhere(missing&(dist==dist[missing].max())).tolist()}))
        require(dist[missing].max(initial=0)<=9,f'Dash {n} requires redraw');target[missing]=target[p[0][missing],p[1][missing]];target[bottom+1:]=0
        # Behind the shoulder the native silhouette is trailing hair. Nearest
        # coverage must not extend a gray cuff or skin over this hair region.
        pink=np.isin(target,(5,6,7,8,9));_,pink_near=distance_transform_edt(~pink,return_indices=True);tail=(xx>=ex+10)&(yy>=ey+2)&(yy<leg_y[n])&np.isin(base,(5,6,7,8,9))&~pink;target[tail]=target[pink_near[0][tail],pink_near[1][tail]]
        # Build only the front arm at native shooting coordinates. Material
        # swatches exclude weapon outlines, preventing the wall-arm regression.
        mx,my=q['muzzle_anchor'];gy,gx=np.nonzero(base!=shot);gun_region=(xx>=gx.min())&(xx<ex-1)&(yy>=min(gy.min(),my-1))&(yy<max(gy.max()+1,my+10));firing=target.copy();firing[gun_region]=shot[gun_region];x,y,x2,y2=q['gun_module_box'];firing[y:y2,x:x2]=module;rx=min(mx+12,ex-6);firing[my-1:my+3,mx+8:rx]=0
        start,end=mx+8,ex-1;top,limit=my+2,my+11;require(end-start>2,'Arm too short');strip=np.concatenate((np.array(Image.fromarray(skin).resize((1,4),Image.Resampling.NEAREST)),np.array(Image.fromarray(cuff).resize((1,4),Image.Resampling.NEAREST)),np.array(Image.fromarray(sleeve).resize((end-start-2,4),Image.Resampling.NEAREST))),axis=1)
        for xc in range(start,end):
            ys=np.flatnonzero(firing[top:limit,xc])+top
            if not len(ys):continue
            lo,hi=int(ys.min()),int(ys.max())
            for yc in range(lo,hi+1):firing[yc,xc]=5 if xc>=start+2 and yc in(lo,hi)else strip[min(3,round((yc-lo)*3/max(1,hi-lo))),xc-start]
        for yc in range(my+3,my+9):
            left=np.flatnonzero(firing[yc,ex-6:ex-1])+ex-6;right=np.flatnonzero(firing[yc,ex:ex+6])+ex
            if len(left)and len(right)and 0<int(right.min()-left.max()-1)<=5:firing[yc,int(left.max()+1):int(right.min())]=7
        firing[y:y2,x:x2]=module
        for ref,t in((n,target),(ns,firing)):targets[ref]=t;save_image(t.tobytes(),(160,160),words,out/f'ultimate_{ref:03}.png')
        q.update(generated_size=list(v.shape[::-1]),head_source='accepted idle, exact head pixels',head_eye_to_ear=16,leg_silhouette_from_y=leg_y[n],registration_max_distance=float(dist[missing].max(initial=0)),arm_box=[start,top,end,limit])
    # The extra speed-line poses use the same body and retain native effects.
    corrected,baseproof=correct_base(arc)
    for q in proof:
        n=q['frames'][1];base=render(corrected,n)[1];t=targets[n];missing=(base>0)&(t==0);coords=np.argwhere(missing);ex,ey=q['eye'];mx,my=q['muzzle_anchor'];require(all(ex-2<=x<=ex+3 and my+2<=y<=my+11 for y,x in coords),'Unexpected missing shooting pixel')
        pink=np.isin(t,(5,6,7,8,9));_,nearest=distance_transform_edt(~pink,return_indices=True);t[missing]=t[nearest[0][missing],nearest[1][missing]];q['shoulder_bridge_pixels']=[[int(x),int(y)]for y,x in coords];save_image(t.tobytes(),(160,160),words,out/f'ultimate_{n:03}.png')
    for n in(73,74):
        body=targets[n-2];base=render(corrected,n)[1];targets[n]=np.where(body>0,body,base).astype(np.uint8);save_image(targets[n].tobytes(),(160,160),words,out/f'ultimate_{n:03}.png')
    for n in FRAMES:
        base=render(corrected,n)[1];require(not np.any((base>0)&(targets[n]==0)),f'Base escapes dash {n}')
    for shoot,name in((False,'dash_review_4x.png'),(True,'dash_shot_review_4x.png')):
        board=Image.new('RGB',(1280,960),'#252c3c');draw=ImageDraw.Draw(board)
        for i,n in enumerate([*ORDER,0]):
            ref=n+int(shoot)if n else 0;v=targets[ref]if n else master;rgba=np.concatenate((rgb[v].astype(np.uint8),((v>0)*255).astype(np.uint8)[...,None]),axis=2);im=Image.fromarray(rgba,'RGBA').crop((32,36,112,112)).resize((320,304),Image.Resampling.NEAREST);x,y=i%4*320,i//4*320;board.paste(im,(x,y+16),im);draw.text((x+3,y+2),str(ref)if n else'ACCEPTED IDLE',fill='white')
        board.save(out/name)
    return targets,proof,corrected,baseproof

def prepare(out,art_only=False):
    out=out.resolve();require(out.is_relative_to(D)and not out.exists(),'Fresh isolated path required');require(digest(PARENT/'rin_nana.bin')==PARENT_SHA,'Parent BIN changed');out.mkdir();targets,proof,base,baseproof=artwork(out);write(out/'registration.json',proof)
    if art_only:return
    result,packed=pack_resources(base,targets,FRAMES);(out/'PL02_U.ARC').write_bytes(result);write(out/'recipe.json',{'task':'ultimate_armor_nana','kind':'ultimate_dash','parent_sha256':PARENT_SHA,'parent_arc_sha256':ARC_SHA,'generated_sha256':SOURCE_SHA,'frames':FRAMES,'registration':proof,'base_correction':baseproof,**packed,'files':{'PL02_U.ARC':sha256(result)},'full_ultimate_complete':False});print(json.dumps({'output':str(out),'sha256':sha256(result),'verification':packed['verification']}))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--art-only',action='store_true');a=p.parse_args();prepare(a.output,a.art_only)
