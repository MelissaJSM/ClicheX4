"""노바 준비213..216과 돌진217..220을 수용 나나 크기로 등록한다."""
import argparse,json,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import numpy as np
from PIL import Image,ImageDraw
from scipy.ndimage import label,binary_dilation,binary_erosion,binary_fill_holes
from scripts.prepare_nana_fourth_pilot import entry,require,write
from scripts.prepare_nana_ultimate_shot_arm import D,full
from scripts.prepare_nana_pilot import normalize
from scripts.prepare_shibuki_capsule_nova import raster
from scripts.prepare_shibuki_ultimate_production import pack_shared,repack_parts,records
from scripts.prepare_nana_ultimate_run import verify
from scripts.prepare_riko_ui import replace_entry
from scripts.extract_zero import save_image
from scripts.project import digest
from scripts.discover_inputs import sha256
from src.psx_player import graphics_bank,composition_frame,decode_stream,bank_offsets,indexed_atlas
from src.psx_compress import encode_stream
from src.psx_bank_repack import repack_graphics_bank
PARENT=ROOT/'out/ver_rin_nana/nana_ultimate_vehicle_20261104T123644751122Z'
PARENT_SHA='f019bf62e4b420b28c838c0269bd141c0cdfe107c48fd2ab4037fcfb4bbb3871'
ARC_SHA='68700f1748bb4beb275e8c4e077078169c17396f786d9aa0564de2c5e3f2dd6b'
FRAMES=list(range(213,221));ORDER=[213,215,217]
SIZE=(256,160)

def pack_wide_effect(raw,count,image,pool):
    """U=0 타일은 첫 열이 빈 조각에만 배정한다."""
    ys,xs=np.nonzero(image);normal=sorted(t for t in pool if t%16);edges=sorted(t for t in pool if not t%16);choices=[]
    for dy in range(16):
        for dx in range(16):
            cells=sorted(set(zip(((xs-dx)//16).tolist(),((ys-dy)//16).tolist())));rr=[(max(0,min(240,x*16+dx)),max(0,min(144,y*16+dy)))for x,y in cells]
            need=max(0,len(rr)-len(normal));safe=[i for i,(x,y)in enumerate(rr)if not image[y:y+16,x].any()]
            if len(rr)<=len(pool)and need<=len(safe):choices.append((len(rr),dy,dx,rr,safe,need))
    require(bool(choices),'Wide effect has no safe tile layout');_,_,_,rr,safe,need=min(choices,key=lambda q:q[:3]);edge_assignment={i:t for i,t in zip(safe[:need],edges)};normal=iter(normal);tiles=[edge_assignment[i]if i in edge_assignment else next(normal)for i in range(len(rr))];data=bytearray(raw);_,locations,_=indexed_atlas(raw,count)
    for t,(x,y)in zip(tiles,rr):
        patch=image[y:y+16,x:x+16]
        for py in range(16):
            for px in range(16):
                pos,shift=locations[(t//16*16+py)*256+t%16*16+px];data[pos]=(data[pos]&~(15<<shift))|(int(patch[py,px])<<shift)
    return bytes(data),[[(t,x,y,0)for t,(x,y)in zip(tiles,rr)]]

def layer(arc,b,n):return raster(entry(arc,2),entry(arc,3),0,b,n,SIZE)

def artwork(arc):
    source=D/'nova_art_v1/generated.png';provenance=json.loads((source.parent/'provenance.json').read_text('utf8'));require(digest(source)==provenance['sha256'],'Source changed');src=Image.open(source).convert('RGBA');require(src.getchannel('A').getextrema()==(0,255),'Transparency required');master=full(arc,0);words=struct.unpack_from('<16H',entry(arc,9),32);rgb=np.array([[(w>>s&31)*255//31 for s in(0,5,10)]for w in words],np.int32);targets={};proof=[]
    for i,n in enumerate(ORDER):
        a=np.array(src.crop((i*src.width//3,0,(i+1)*src.width//3,src.height)));labs,_=label(a[:,:,3]>=192,np.ones((3,3)));sizes=np.bincount(labs.flat);sizes[0]=0;keep=labs==sizes.argmax();sy,sx=np.nonzero(keep);a[~keep,3]=0;crop=Image.fromarray(a).crop((sx.min(),sy.min(),sx.max()+1,sy.max()+1));ca=np.array(crop).astype(np.int32);yy,_=np.indices(ca.shape[:2]);gy,gx=np.nonzero((ca[:,:,1]>ca[:,:,0]+5)&(ca[:,:,1]>ca[:,:,2]+5)&(ca[:,:,3]>=192)&(yy<crop.height*.6));require(len(gx)>0,'Source eye missing')
        h={213:48,215:53,217:34}[n];w=round(h*crop.width/crop.height);v=normalize(crop,h,rgb,width=w);cx=round((float(np.median(gx))+.5)*w/crop.width-.5);cy=round((float(np.median(gy))+.5)*h/crop.height-.5);ex,ey={213:(75,68),215:(79,68),217:(65,80)}[n];dx,dy=ex-cx,ey-cy;target=np.zeros((160,256),np.uint8);target[dy:dy+h,dx:dx+w]=v
        head=master[52:74,67:90];hx,hy=ex-9,ey-16;target[:hy]=0;target[hy:ey+5,hx:ex+12]=0;region=target[hy:hy+22,hx:hx+23];region[head>0]=head[head>0]
        protected=np.zeros_like(target,bool);protected[hy:hy+22,hx:hx+23]=head>0;rim=(target>0)&~binary_erosion(target>0,np.ones((3,3),bool))&(target==5)&~protected;target[rim]=1
        targets[n]=target;proof.append(dict(frames=[n,n],eye=[ex,ey],head_box=[hx,hy,hx+23,hy+22],source_size=[w,h],source_crop_size=list(crop.size),pistol_present=False,pistol_mask_bbox=None))
    # Native shared preparation pairs keep the same body and origin.
    for n in (214,216):targets[n]=targets[n-1].copy();proof.append(dict(frames=[n,n],shared_body=n-1,pistol_present=False,pistol_mask_bbox=None))
    oldbody=layer(arc,5,217);body=targets[217]
    for n in (218,220):
        old=layer(arc,5,n);candidates=[]
        for dy in range(-4,5):
            for dx in range(-12,13):
                shifted=np.roll(np.roll(oldbody,dy,0),dx,1);score=int(np.count_nonzero((shifted>0)&(shifted==old)));candidates.append((score,-abs(dx)-abs(dy),dx,dy))
        _,_,dx,dy=max(candidates);mask=binary_dilation(np.roll(np.roll(oldbody>0,dy,0),dx,1));newbody=np.roll(np.roll(body,dy,0),dx,1);result=old.copy();result[mask]=0
        envelope=binary_fill_holes(old>0);fill=mask&envelope;result[fill]=14;result[newbody>0]=newbody[newbody>0]
        preserve=~mask&(newbody==0);require(np.array_equal(result[preserve],old[preserve]),'Outer Nova effect changed');require(not np.any(envelope&(result==0)),'Nova envelope has a gap');targets[n]=result;proof.append(dict(frames=[n,n],body_source=217,body_offset=[dx,dy],effect_outer_preserved=True,energy_fill_pixels=int(fill.sum()),energy_fill_index=14,pistol_present=False,pistol_mask_bbox=None))
    silhouette=binary_dilation(body>0,iterations=2);flash=np.zeros_like(body);flash[silhouette]=7;flash[body>0]=6;targets[219]=flash;proof.append(dict(frames=[219,219],body_source=217,flash_only=True,pistol_present=False,pistol_mask_bbox=None))
    return targets,sorted(proof,key=lambda q:q['frames'][0])

def correct_base(arc):
    """남은 X 준비4자세를 같은 나나 몸으로 교체하고 다른 레이어를 보존한다."""
    require(sha256(arc)==ARC_SHA,'Unsupported parent');targets,_=artwork(arc);g,c=entry(arc,2),entry(arc,3);bank=graphics_bank(g,0,allow_bank_aliases=True);changes={};replacements={};proof=[]
    for n in (213,215):
        f=bank['frames'][n];ns=[q['index']for q in bank['frames']if q['offset']==f['offset']];require(ns==[n,n+1],'Unexpected preparation aliases');raw=decode_stream(g,f['offset'],f['limit'],f['tile_count']*128).data;protected={p['tile']for k in ns for b in(5,6,7,8)for p in composition_frame(c,b,k)['parts']};pool={p['tile']for k in ns for p in composition_frame(c,0,k)['parts']}-protected;pool={t for t in pool if t%16!=0};new,rr=pack_shared(raw,f['tile_count'],[targets[k]for k in ns],pool,[len(pool)]*2)
        for k,parts in zip(ns,rr):changes[k]=b''.join(struct.pack('<BBbb',fl,t,x-80,y-80)for t,x,y,fl in parts);replacements[k]=encode_stream(new)
        proof.append(dict(frames=ns,pool=sorted(pool),parts=[len(q)for q in rr]))
    nc,slack=repack_parts(c,0,changes);ng,rep=repack_graphics_bank(g,0,replacements);result=replace_entry(replace_entry(arc,2,ng),3,nc)
    for bi in range(len(bank_offsets(g,allow_aliases=True))):
        for a,b in zip(graphics_bank(g,bi,allow_bank_aliases=True)['frames'],graphics_bank(ng,bi,allow_bank_aliases=True)['frames']):
            if bi==0 and a['index']in changes:continue
            require(decode_stream(g,a['offset'],a['limit'],a['tile_count']*128).data==decode_stream(ng,b['offset'],b['limit'],b['tile_count']*128).data,'Other base graphics changed')
    for cb in range(len(bank_offsets(c))):
        for n in range(composition_frame(c,cb,0)['bank_frame_count']):
            if cb==0 and n in changes:continue
            require(records(c,cb,n)==records(nc,cb,n),'Other base composition changed')
    for n in changes:
        require(np.array_equal(layer(result,0,n),targets[n]),'New base differs')
        for b in(5,6,7,8):require(np.array_equal(layer(result,b,n),layer(arc,b,n)),'Other base layer changed')
    return result,dict(frames=sorted(changes),packing=proof,parts_slack=slack,graphics_repack=rep,other_references_preserved=True)

def prepare(out,art_only=False):
    out=out.resolve();require(out.is_relative_to(D)and not out.exists(),'Fresh isolated output required');require(digest(PARENT/'rin_nana.bin')==PARENT_SHA and digest(PARENT/'PL02_U.ARC')==ARC_SHA,'Parent changed');out.mkdir();arc=(PARENT/'PL02_U.ARC').read_bytes();targets,proof=artwork(arc);write(out/'registration.json',proof);words=struct.unpack_from('<16H',entry(arc,9),32)
    board=Image.new('RGB',(1536,640),'#46545c');draw=ImageDraw.Draw(board)
    for n in FRAMES:save_image(targets[n].tobytes(),SIZE,words,out/f'ultimate_{n:03}.png')
    for i,n in enumerate((213,215,217,218,219,220)):
        im=Image.open(out/f'ultimate_{n:03}.png').convert('RGBA');pic=im.crop((35,35,175,115)).resize((560,320),Image.Resampling.NEAREST) if n==220 else im.crop((35,35,115,115)).resize((320,320),Image.Resampling.NEAREST);x=i%3*512;y=i//3*320;board.paste(pic,(x,y),pic);draw.text((x+4,y+4),str(n),fill='white')
    board.save(out/'nova_review.png')
    if art_only:return
    base,bproof=correct_base(arc);g,c=entry(base,2),entry(base,3);bank=graphics_bank(g,0,allow_bank_aliases=True);replacements={};changes={};packing=[]
    for n in ORDER+[218,219,220]:
        f=bank['frames'][n];ns=[q['index']for q in bank['frames']if q['offset']==f['offset']];raw=decode_stream(g,f['offset'],f['limit'],f['tile_count']*128).data;keep={p['tile']for k in ns for b in(0,6,7,8)for p in composition_frame(c,b,k)['parts']};pool={t for t in range(f['tile_count'])if t not in keep}
        if n in(218,220):new,rr=pack_wide_effect(raw,f['tile_count'],targets[n],pool)
        else:
            pool={t for t in pool if t%16};new,rr=pack_shared(raw,f['tile_count'],[targets[k]for k in ns],pool,[len(pool)]*len(ns))
        for k,parts in zip(ns,rr):changes[k]=b''.join(struct.pack('<BBbb',fl,t,x-80,y-80)for t,x,y,fl in parts);replacements[k]=encode_stream(new)
        packing.append(dict(frames=ns,free_tiles=len(pool),parts=[len(q)for q in rr]))
    nc,slack=repack_parts(c,5,changes);ng,rep=repack_graphics_bank(g,0,replacements);result=replace_entry(replace_entry(base,2,ng),3,nc);check=verify(base,result,targets,{});(out/'PL02_U.ARC').write_bytes(result);write(out/'recipe.json',dict(task='ultimate_armor_nana',kind='ultimate_nova',parent_sha256=PARENT_SHA,parent_arc_sha256=ARC_SHA,frames=FRAMES,registration=proof,base_correction=bproof,packing=packing,graphics_repack=rep,parts_bank5_remaining=slack,verification=check,files={'PL02_U.ARC':sha256(result)},full_ultimate_complete=False));print(json.dumps(dict(output=str(out),sha256=sha256(result),verification=check)))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--art-only',action='store_true');a=p.parse_args();prepare(a.output,a.art_only)
