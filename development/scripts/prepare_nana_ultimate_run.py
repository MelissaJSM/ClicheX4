"""수용 얼티밋 의상의 이동·사격32참조와 캡슐48참조를 고정 경계에 넣는다."""
import argparse,json,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import numpy as np
from PIL import Image,ImageDraw
from scipy.ndimage import label,distance_transform_edt,binary_dilation
from scripts.prepare_nana_fourth_pilot import entry,require,write,render
from scripts.prepare_nana_pilot import normalize
from scripts.prepare_riko_ui import replace_entry
from scripts.prepare_shibuki_ultimate_production import pack_shared,repack_parts,records
from scripts.prepare_shibuki_capsule_nova import raster,silhouette_frames,packed_bank
from scripts.extract_zero import save_image
from scripts.project import digest
from scripts.discover_inputs import psx_arc,sha256
from src.psx_player import graphics_bank,composition_frame,decode_stream,bank_offsets
from src.psx_sprite_batch import canvas_from_parts
from src.psx_compress import encode_stream
from src.psx_bank_repack import repack_graphics_bank
from src.psx_ui_atlas import local_composition

D=ROOT/'work/ver_rin_nana/nana_ultimate_armor'
PARENT=ROOT/'out/ver_rin_nana/nana_ultimate_start_20261030T131517719423Z'
PARENT_SHA='b2888964e995b0d63b2d862921a938fa2de59454dee5175fb55e5d697179c94e'
ARC_SHA='fbd74583c552b86c9298fa6b3d27cbe160f9c430bdffce06509257ae6ca61e7f'
GENERATED_SHA='bc6bf23cebb9276dd37947dbf2df91899545455a0b361d2371c28f4974b091cd'
SCALE_SHA='db4784d31a0d094fa8fa55b14c7dc3772e8b0525e88b534f3d478b353e8db785'
FRAMES=list(range(1,33))

def artwork(out,scale_fix=False):
    require(digest(PARENT/'PL02_U.ARC')==ARC_SHA,'Unsupported Ultimate source')
    generated=D/('run_scale_v1/generated.png' if scale_fix else 'run_v1/generated.png');require(digest(generated)==(SCALE_SHA if scale_fix else GENERATED_SHA),'Generated source changed')
    source=Image.open(generated).convert('RGBA');require(source.getchannel('A').getextrema()==(0,255),'Transparency required')
    arc=(PARENT/'PL02_U.ARC').read_bytes();words=struct.unpack_from('<16H',entry(arc,9),32)
    rgb=np.array([[(w>>s&31)*255//31 for s in (0,5,10)] for w in words],np.int32)
    order=json.loads((ROOT/'work/ver_rin_nana/nana_art/run_v1/plan.json').read_text('utf8'))['order']
    yy,xx=np.indices((160,160));results={};proof=[];board=Image.new('RGB',(1024,1152),'#252c3c');dr=ImageDraw.Draw(board)
    for i,n in enumerate(order):
        base=render(arc,n)[1];shot=render(arc,n+1)[1]
        ey,ex=np.nonzero((base==14)&(yy<80));require(len(ex)>0,'Missing accepted eye');eye_x=int(round(float(np.median(ex))));eye_y=int(round(float(np.median(ey))));bottom=int(np.nonzero(base)[0].max())
        cell=source.crop((i%4*source.width//4,i//4*source.height//4,(i%4+1)*source.width//4,(i//4+1)*source.height//4));a=np.array(cell)
        ls,count=label(a[:,:,3]>=128,np.ones((3,3)));sizes=np.bincount(ls.flat);sizes[0]=0;keep=ls==sizes.argmax();sy,sx=np.nonzero(keep);a[~keep,3]=0;crop=Image.fromarray(a).crop((sx.min(),sy.min(),sx.max()+1,sy.max()+1))
        variants=[]
        for h in range(38,57):
            v=normalize(crop,h,rgb);vy,vx=np.nonzero((v==14)&(np.indices(v.shape)[0]<h//2))
            if not len(vx):continue
            cy,cx=float(np.median(vy)),float(np.median(vx));score=abs((h-1-cy)-(bottom-eye_y))
            if scale_fix:score=abs(cy-16)*5+score
            variants.append((score,abs(h-(bottom-eye_y+18)),v,cx,cy))
        require(bool(variants),'Generated eye missing');_,_,v,cx,cy=min(variants,key=lambda q:q[:2]);dx=eye_x-round(cx);dy=eye_y-round(cy)
        target=np.zeros_like(base);require(dx>=0 and dy>=0 and dx+v.shape[1]<=160 and dy+v.shape[0]<=160,'Artwork overflow');target[dy:dy+v.shape[0],dx:dx+v.shape[1]]=v
        # Native face/eyes and foot trajectory lock character scale and motion.
        face=(yy>=eye_y-2)&(yy<=eye_y+4)&(xx>=eye_x-2)&(xx<=eye_x+4)
        target[face]=base[face]
        hip=eye_y+17
        if scale_fix:
            lower=(yy>=hip)|((xx>=eye_x+14)&(yy>=eye_y+12))
            foot=binary_dilation(np.isin(base,(5,6))&lower,iterations=1)&lower
        else:lower=yy>=hip+4;foot=np.zeros_like(base,dtype=bool)
        target[lower]=0
        for y in range(eye_y+12 if scale_fix else hip+4,160):
            ids=np.flatnonzero((base[y]>0)&lower[y])
            if not len(ids):continue
            for run in np.split(ids,np.flatnonzero(np.diff(ids)>1)+1):
                l,r=int(run.min()),int(run.max());target[y,l:r+1]=1
                if r-l>=2:
                    target[y,l+1:r]=12
                    if r-l>=4:target[y,r-1]=11
                    if y>=bottom-2:target[y,l+1:r]=15
                    if scale_fix:
                        for x in range(l+1,r):
                            if foot[y,x]:target[y,x]=15
        # Preserve all original soles and prevent a changed body anchor.
        target[bottom]=np.where(base[bottom],1,0);target[bottom+1:]=0
        dist,nearest=distance_transform_edt(target==0,return_indices=True);missing=(base>0)&(target==0)
        require(dist[missing].max(initial=0)<=6,f'Pose {n} needs redraw, missing silhouette too far: {np.argwhere(missing & (dist>6)).tolist()}')
        target[missing]=target[nearest[0][missing],nearest[1][missing]];target[face]=base[face]
        diff=base!=shot;gy,gx=np.nonzero(diff);require(len(gx)>0,'Missing shot pair')
        # Copy the forward firing arm only. A full difference bounding box
        # also contains the face and chest and would restore the base costume.
        gunbox=(xx>=gx.min())&(xx<eye_x+1)&(yy>=eye_y+2)&(yy<eye_y+10);firing=target.copy();firing[gunbox]=shot[gunbox]
        lowered=(xx<eye_x+1)&(yy>=eye_y+10)&(yy<hip+1);firing[lowered]=shot[lowered]
        stray=(shot>0)&(firing==0);firing[stray]=shot[stray]
        # Costume sleeve can change color; the existing pistol/hand pixels cannot.
        gun_end=int(gx.min())+6
        sleeve=gunbox&(xx>=gun_end)&(xx<eye_x)&(yy>=eye_y+3)&np.isin(firing,(2,3,4));firing[sleeve]=np.choose(firing[sleeve]-2,[7,8,9])
        pistol=gunbox&(xx<gun_end);require(np.array_equal(firing[pistol],shot[pistol]),'Sarang-i muzzle/grip changed')
        for y in range(eye_y+3,eye_y+8):
            row=firing[y];left=np.flatnonzero(row[eye_x-10:eye_x-2])+eye_x-10;right=np.flatnonzero(row[eye_x:eye_x+6])+eye_x
            if len(left) and len(right) and 0<int(right.min()-left.max()-1)<=5:
                for x in range(int(left.max()+1),int(right.min())):
                    if not row[x]:row[x]=7
        for f,b,t in ((n,base,target),(n+1,shot,firing)):
            require(not np.any((b>0)&(t==0)),f'Underlying base visible {f}');results[f]=t
            save_image(t.tobytes(),(160,160),words,out/f'ultimate_{f:03}.png')
        pic=Image.open(out/f'ultimate_{n:03}.png').convert('RGBA').crop((48,40,112,112)).resize((256,288),Image.Resampling.NEAREST);board.paste(pic,(i%4*256,i//4*288),pic);dr.text((i%4*256+3,i//4*288+4),str(n),fill='white')
        proof.append({'frames':[n,n+1],'eye':[eye_x,eye_y],'sole':bottom,'generated_size':list(v.shape[::-1]),'eye_to_ear_top':int(eye_y-np.nonzero(target)[0].min()),'idle_eye_to_ear_top':16,'scale_fix':scale_fix,'native_silhouette_extension_pixels':int(missing.sum()),'max_registration_distance':float(dist[missing].max(initial=0)),'pistol_exact':True,'pistol_mask_bbox':[int(gx.min()),int(gy.min()),gun_end,int(gy.max()+1)]})
    board.save(out/'run_review_4x.png')
    shotboard=Image.new('RGB',board.size,'#252c3c')
    for i,n in enumerate(order):
        pic=Image.open(out/f'ultimate_{n+1:03}.png').convert('RGBA').crop((40,40,112,112)).resize((256,256),Image.Resampling.NEAREST);shotboard.paste(pic,(i%4*256,i//4*288+16),pic)
    shotboard.save(out/'shoot_review.png');return results,proof

def verify(before,after,targets,capsules):
    require(len(before)==len(after),'ARC length changed');g,c=entry(before,2),entry(before,3);ng,nc=entry(after,2),entry(after,3)
    # Preserve duplicate ARC entries by their actual byte ranges, not type lookup.
    for e in psx_arc(before):
        if int(e['type'],16) not in (2,3):require(before[e['offset']:e['offset']+e['size']]==after[e['offset']:e['offset']+e['size']],'Non-graphics entry changed')
    protected=decoded=base_layers=0
    for bi in range(len(bank_offsets(g,allow_aliases=True))):
        ob=graphics_bank(g,bi,allow_bank_aliases=True);nb=graphics_bank(ng,bi,allow_bank_aliases=True);require((ob['base'],ob['end'],len(ob['frames']))==(nb['base'],nb['end'],len(nb['frames'])),'Bank boundary changed')
        for a,b in zip(ob['frames'],nb['frames']):
            require(a['tile_count']==b['tile_count'],'Tile count changed');old=decode_stream(g,a['offset'],a['limit'],a['tile_count']*128).data;new=decode_stream(ng,b['offset'],b['limit'],b['tile_count']*128).data;decoded+=1
            if bi==0 and a['index'] in targets:
                n=a['index'];size=(targets[n].shape[1],targets[n].shape[0])
                for cb in (0,6,7,8):require(np.array_equal(canvas_from_parts(old,a['tile_count'],local_composition(composition_frame(c,cb,n)),size=size),canvas_from_parts(new,b['tile_count'],local_composition(composition_frame(nc,cb,n)),size=size)),'Underlying/protected player layer changed');base_layers+=1
                base=raster(ng,nc,0,0,n,size);overlay=raster(ng,nc,0,5,n,size);require(np.array_equal(np.where(overlay,overlay,base),targets[n]),'Run pixels differ')
                basepal=np.array(struct.unpack_from('<16H',entry(after,9)));armorp=np.array(struct.unpack_from('<16H',entry(after,9),32));exposed=(base>0)&(overlay==0);require(np.all(basepal[base[exposed]]==armorp[base[exposed]]),'Exposed base uses different palette')
            elif bi in capsules:require(np.array_equal(raster(ng,nc,bi,bi+8,a['index']),capsules[bi][a['index']]),'Capsule pixels differ')
            else:require(old==new,'Protected graphics changed');protected+=1
    compositions=0
    for cb in range(len(bank_offsets(c))):
        for n in range(composition_frame(c,cb,0)['bank_frame_count']):
            if (cb==5 and n in targets) or cb-8 in capsules:continue
            require(records(c,cb,n)==records(nc,cb,n),'Protected composition changed');compositions+=1
    return {'decoded_graphics':decoded,'protected_graphics':protected,'protected_player_layers':base_layers,'protected_compositions':compositions,'new_ultimate_frames':len(targets),'capsule_frames':sum(map(len,capsules.values())),'palette_timing_logic_preserved':True,'runtime_verified':False}

def prepare(out,art_only=False,scale_fix=False,detail_fix=False):
    out=out.resolve();require(out.is_relative_to(D) and not out.exists(),'Fresh task output required');require(digest(PARENT/'rin_nana.bin')==PARENT_SHA,'Parent changed')
    approval=json.loads((ROOT/'projects/ver_rin_nana/nana_ultimate_candidate.json').read_text('utf8'));require(approval['full_animation_production_approved'],'Production approval missing')
    out.mkdir()
    if detail_fix:
        from scripts.prepare_nana_ultimate_run_detail import artwork as detail_art,DETAIL_SHA
        targets,registration=detail_art(out)
    else:targets,registration=artwork(out,scale_fix)
    write(out/'registration.json',registration)
    if art_only:return
    arc=(PARENT/'PL02_U.ARC').read_bytes();g,c=entry(arc,2),entry(arc,3);bank=graphics_bank(g,0,allow_bank_aliases=True);replacements={};changes={};reports=[]
    for n in range(1,33,2):
        f=bank['frames'][n];ns=[q['index'] for q in bank['frames'] if q['offset']==f['offset']];require(ns==[n,n+1],'Unexpected alias')
        old=decode_stream(g,f['offset'],f['limit'],f['tile_count']*128).data;keep={q['tile'] for v in ns for b in (0,6,7,8) for q in composition_frame(c,b,v)['parts']};pool=set(range(f['tile_count']))-keep;original_limits=[len(composition_frame(c,5,v)['parts']) for v in ns];limits=[min(len(pool),q+3) for q in original_limits]
        overlays=[]
        for v in ns:
            base=raster(g,c,0,0,v);target=targets[v];overlay=np.where((target==base)&(base!=15),0,target).astype(np.uint8);overlays.append(overlay)
        raw,rr=pack_shared(old,f['tile_count'],overlays,pool,limits)
        for v,parts,limit in zip(ns,rr,limits):
            require(0<len(parts)<=limit,'Part budget exceeded');changes[v]=b''.join(struct.pack('<BBbb',flag,t,x-80,y-80) for t,x,y,flag in parts);replacements[v]=encode_stream(raw)
        reports.append({'frames':ns,'tiles':f['tile_count'],'writable_tiles':len(pool),'original_parts':original_limits,'parts':[len(r) for r in rr],'encoded_bytes':len(encode_stream(raw))});print(json.dumps(reports[-1]),flush=True)
    nc,slack=repack_parts(c,5,changes)
    ng,rep=repack_graphics_bank(g,0,replacements)
    full=raster(ng,nc,0,0,0)
    for cb in (8,5,7,6):
        layer=raster(ng,nc,0,cb,0);full[layer>0]=layer[layer>0]
    capsules={};cap_proof=[];words=[0,0xffff,0xfdc8,0xe920]+[0x8000]*12;board=Image.new('RGB',(960,384),'#252c3c')
    for row,gb in enumerate(range(10,14)):
        images=silhouette_frames(ng,nc,gb,gb+8,full>0);ng,nc,proof=packed_bank(ng,nc,gb,gb+8,images);capsules[gb]=images;cap_proof.append(proof);print(json.dumps(proof),flush=True)
        for n,im in enumerate(images):
            pic=save_image(im.tobytes(),(160,160),words,out/f'capsule_{gb}_{n:02}.png').convert('RGBA').crop((40,32,120,112));board.paste(pic,(n*80,row*96+16),pic)
    board.resize((1920,768),Image.Resampling.NEAREST).save(out/'capsule_review_2x.png')
    result=replace_entry(replace_entry(arc,2,ng),3,nc);proof=verify(arc,result,targets,capsules);(out/'PL02_U.ARC').write_bytes(result)
    write(out/'recipe.json',{'task':'ultimate_armor_nana','kind':'ultimate_run_capsule','parent_sha256':PARENT_SHA,'parent_arc_sha256':ARC_SHA,'generated_sha256':DETAIL_SHA if detail_fix else SCALE_SHA if scale_fix else GENERATED_SHA,'scale_fix':scale_fix or detail_fix,'detail_fix':detail_fix,'frames':FRAMES,'registration':registration,'packing':reports,'graphics_repack':rep,'parts_bank5_remaining':slack,'capsule_packing':cap_proof,'verification':proof,'files':{'PL02_U.ARC':sha256(result)},'full_ultimate_complete':False});print(json.dumps({'output':str(out),'verification':proof,'sha256':sha256(result)}))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--art-only',action='store_true');p.add_argument('--scale-fix',action='store_true');p.add_argument('--detail-fix',action='store_true');a=p.parse_args();prepare(a.output,a.art_only,a.scale_fix,a.detail_fix)
