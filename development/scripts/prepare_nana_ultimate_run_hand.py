"""이동 손 주변의 검은 덩어리만 수정하고 수용 몸체/공중 도트를 보존한다."""
import argparse,json,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import numpy as np
from PIL import Image,ImageDraw
from scipy.ndimage import label,distance_transform_edt
from scripts.prepare_nana_fourth_pilot import entry,require,render,write
from scripts.prepare_nana_pilot import normalize
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
PARENT=ROOT/'out/ver_rin_nana/nana_ultimate_air_20261104T064717554177Z'
PARENT_SHA='aee8fd756e2ff838e36a93dc58b1950e577a5b13d9c8aa3afe76bf9953d30482'
ARC_SHA='5614728ec088b47302e33cafc1151620f573bb140f8d5e2575ae0980a3561827'
SOURCE_SHA='f61cbca6c05550c7d8f994a2ca8be3e5a537baf735c42b2b96dc9d9a660dfc16'
FRAMES=list(range(1,33))

def artwork(out):
    src=D/'run_hand_v1/generated.png';require(digest(src)==SOURCE_SHA,'Edited source changed');source=Image.open(src).convert('RGBA');require(source.getchannel('A').getextrema()==(0,255),'Transparent input required')
    arc=(PARENT/'PL02_U.ARC').read_bytes();words=struct.unpack_from('<16H',entry(arc,9),32);rgb=np.array([[(w>>s&31)*255//31 for s in (0,5,10)] for w in words],np.int32);registration=json.loads((PARENT/'ultimate_run/registration.json').read_text());order=[q['frames'][0] for q in registration];targets={};proof=[];yy,xx=np.indices((160,160))
    for i,r in enumerate(registration):
        n=n0=r['frames'][0];ex,ey=r['eye'];base=render(arc,n)[1];old=np.array(Image.open(PARENT/'ultimate_run'/f'ultimate_{n:03}.png'));shot=np.array(Image.open(PARENT/'ultimate_run'/f'ultimate_{n+1:03}.png'))
        cell=source.crop((i%4*source.width//4,i//4*source.height//4,(i%4+1)*source.width//4,(i//4+1)*source.height//4));a=np.array(cell);ls,_=label(a[:,:,3]>=192,np.ones((3,3)));sizes=np.bincount(ls.flat);sizes[0]=0;keep=ls==sizes.argmax();sy,sx=np.nonzero(keep);a[~keep,3]=0;crop=Image.fromarray(a).crop((sx.min(),sy.min(),sx.max()+1,sy.max()+1));v=normalize(crop,r['generated_size'][1],rgb);vy,vx=np.nonzero((v==14)&(np.indices(v.shape)[0]<len(v)//2))
        if not len(vx):
            rgba=np.array(crop).astype(np.int32);red,green,blue=rgba[:,:,:3].transpose(2,0,1);eyes=(green>red+10)&(green>blue+10)&(green>60)&(rgba[:,:,3]>=192);eyes[crop.height//2:]=False;vy,vx=np.nonzero(eyes);require(len(vx)>0,'Generated eye missing');vx=vx*v.shape[1]/crop.width;vy=vy*v.shape[0]/crop.height
        dx=ex-round(float(np.median(vx)));dy=ey-round(float(np.median(vy)));candidate=np.zeros_like(old);candidate[dy:dy+v.shape[0],dx:dx+v.shape[1]]=v
        box=[ex-15,ey+4,ex+1,ey+17];x,y,x2,y2=box;mask=(xx>=x)&(xx<x2)&(yy>=y)&(yy<y2);target=old.copy();target[mask]=candidate[mask]
        # Original base pixels still lie below the Ultimate overlay. Register
        # just the missing seam pixels to the edited hand/cuff, never copy the
        # old black glove back over the new hand.
        donors=(candidate>0)&mask;dist,near=distance_transform_edt(~donors,return_indices=True);missing=mask&(base>0)&(target==0);require(dist[missing].max(initial=0)<=6,'Hand edit too far from native arm');target[missing]=candidate[near[0][missing],near[1][missing]]
        require(np.array_equal(target[~mask],old[~mask]),'Body changed outside hand');require(not np.any((base>0)&(target==0)),'Base escapes hand edit');targets[n]=target;targets[n+1]=shot
        for f in (n,n+1):save_image(targets[f].tobytes(),(160,160),words,out/f'ultimate_{f:03}.png')
        proof.append({**r,'hand_edit_box':box,'body_outside_hand_identical':True,'shooting_pose_identical':True,'changed_pixels':int(np.count_nonzero(target!=old)),'dark_pixels_before':int(np.count_nonzero(mask&np.isin(old,(1,2,3,4)))),'dark_pixels_after':int(np.count_nonzero(mask&np.isin(target,(1,2,3,4)))),'base_seam_pixels':int(missing.sum()),'edited_source':src.relative_to(ROOT).as_posix()})
    for compare,name in ((False,'run_review_4x.png'),(True,'hand_before_after_6x.png')):
        board=Image.new('RGB',(1280,1280) if not compare else (1536,640),'#252c3c');draw=ImageDraw.Draw(board)
        chosen=order if not compare else (1,5,13,21)
        for i,n in enumerate(chosen):
            if not compare:
                pic=Image.open(out/f'ultimate_{n:03}.png').convert('RGBA').crop((40,40,120,112)).resize((320,288),Image.Resampling.NEAREST);x=i%4*320;y=i//4*320;board.paste(pic,(x,y+24),pic);draw.text((x+4,y+4),str(n),fill='white')
            else:
                for row in (0,1):
                    path=PARENT/'ultimate_run'/f'ultimate_{n:03}.png' if not row else out/f'ultimate_{n:03}.png';pic=Image.open(path).convert('RGBA').crop((48,56,112,104)).resize((384,288),Image.Resampling.NEAREST);x=i*384;y=row*320;board.paste(pic,(x,y+24),pic);draw.text((x+5,y+4),('BEFORE ' if not row else 'AFTER ')+str(n),fill='white')
        board.save(out/name)
    return targets,proof

def prepare(out,art_only=False):
    out=out.resolve();require(out.is_relative_to(D) and not out.exists(),'Fresh isolated output required');require(digest(PARENT/'rin_nana.bin')==PARENT_SHA and digest(PARENT/'PL02_U.ARC')==ARC_SHA,'Parent changed');out.mkdir();targets,registration=artwork(out);write(out/'registration.json',registration)
    if art_only:return
    arc=(PARENT/'PL02_U.ARC').read_bytes();g,c=entry(arc,2),entry(arc,3);bank=graphics_bank(g,0,allow_bank_aliases=True);replacements={};changes={};reports=[]
    for n in FRAMES[::2]:
        f=bank['frames'][n];ns=[q['index'] for q in bank['frames'] if q['offset']==f['offset']];require(ns==[n,n+1],'Unexpected aliases');old=decode_stream(g,f['offset'],f['limit'],f['tile_count']*128).data;keep={q['tile'] for v in ns for cb in (0,6,7,8) for q in composition_frame(c,cb,v)['parts']};pool=set(range(f['tile_count']))-keep;limits=[min(len(pool),len(composition_frame(c,5,v)['parts'])+3) for v in ns];overlays=[]
        for v in ns:
            base=raster(g,c,0,0,v);overlays.append(np.where((targets[v]==base)&(base!=15),0,targets[v]).astype(np.uint8))
        raw,rr=pack_shared(old,f['tile_count'],overlays,pool,limits)
        for v,parts in zip(ns,rr):changes[v]=b''.join(struct.pack('<BBbb',flag,t,x-80,y-80) for t,x,y,flag in parts);replacements[v]=encode_stream(raw)
        reports.append({'frames':ns,'free_tiles':len(pool),'parts':[len(r) for r in rr]});print(json.dumps(reports[-1]),flush=True)
    nc,slack=repack_parts(c,5,changes);ng,rep=repack_graphics_bank(g,0,replacements);result=replace_entry(replace_entry(arc,2,ng),3,nc);check=verify(arc,result,targets,{});(out/'PL02_U.ARC').write_bytes(result);write(out/'recipe.json',{'task':'ultimate_armor_nana','kind':'ultimate_run_hand','parent_sha256':PARENT_SHA,'parent_arc_sha256':ARC_SHA,'generated_sha256':SOURCE_SHA,'frames':FRAMES,'registration':registration,'packing':reports,'graphics_repack':rep,'parts_bank5_remaining':slack,'verification':check,'files':{'PL02_U.ARC':sha256(result)},'full_ultimate_complete':False});print(json.dumps({'output':str(out),'verification':check,'sha256':sha256(result)}))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--art-only',action='store_true');a=p.parse_args();prepare(a.output,a.art_only)
