"""벽 사격에 잘못 매핑한 총 뒤쪽 검은 픽셀을 승인된 팔 재질로 교정한다."""
import argparse,json,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import numpy as np
from PIL import Image,ImageDraw
from scipy.ndimage import distance_transform_edt
from scripts.prepare_nana_fourth_pilot import entry,require,write
from scripts.prepare_nana_pilot import normalize
from scripts.prepare_nana_ultimate_shot_arm import D,full,pack_resources
from scripts.prepare_shibuki_ultimate_production import pack_shared,repack_parts,records as composition_records
from scripts.prepare_shibuki_capsule_nova import raster
from scripts.prepare_riko_ui import replace_entry
from scripts.project import digest
from scripts.discover_inputs import sha256
from scripts.extract_zero import save_image
from src.psx_player import graphics_bank,composition_frame,decode_stream
from src.psx_bank_repack import repack_graphics_bank
from src.psx_compress import encode_stream
PARENT=ROOT/'out/ver_rin_nana/nana_ultimate_wall_20261104T083408815839Z'
PARENT_SHA='11216c0601f194520405eed82cc3f7396d7aaba68634af4b947cad1a7e401544'
ARC_SHA='ffbe44a7f4e51260179feaeb769ea17013eaf29fab2d64624805b8840480ecb3'
SOURCE_SHA='229eab7f7882f956bd45ee8bbf59ca088f854da2b4ccf814a7d6b37aa909ab7f'
FRAMES=list(range(55,67));SHOTS=FRAMES[1::2]

def records():return json.loads((PARENT/'ultimate_wall/registration.json').read_text('utf8'))

def excess_pixels(arc):
    result={}
    for q in records():
        n=q['frames'][1];mx,my=q['muzzle_anchor'];ex,ey=q['eye'];v=full(arc,n)
        # Outside the fixed 8x7 pistol; the old longer pistol's top/rear lies
        # above the wrist and entirely left of the accepted face silhouette.
        x1,x2=mx+8,min(mx+12,ex-6);y1,y2=my-1,my+3
        result[n]=[(int(x+x1),int(y+y1)) for y,x in np.argwhere(v[y1:y2,x1:x2]>0)]
    return result

def correct_base(arc):
    require(sha256(arc)==ARC_SHA,'Wrong wall arm source');g,c=entry(arc,2),entry(arc,3);bank=graphics_bank(g,0,allow_bank_aliases=True);coords=excess_pixels(arc);changes={};streams={};proof=[]
    for n in SHOTS:
        ns=[n-1,n];f=bank['frames'][n];require([q['index'] for q in bank['frames'] if q['offset']==f['offset']]==ns,'Unexpected aliases');raw=decode_stream(g,f['offset'],f['limit'],f['tile_count']*128).data
        keep={q['tile'] for v in ns for cb in (6,7,8) for q in composition_frame(c,cb,v)['parts']};pool={q['tile'] for v in ns for q in composition_frame(c,0,v)['parts']}-keep
        images=[raster(g,c,0,0,v) for v in ns]
        for x,y in coords[n]:images[1][y,x]=0
        new,rr=pack_shared(raw,f['tile_count'],images,pool,[len(pool)]*2)
        for v,parts in zip(ns,rr):changes[v]=b''.join(struct.pack('<BBbb',flag,t,x-80,y-80)for t,x,y,flag in parts);streams[v]=encode_stream(new)
        proof.append({'frame':n,'removed_abandoned_gun_pixels':coords[n],'base_repacked_frames':ns,'regular_and_other_layers_preserved':True})
    nc,_=repack_parts(c,0,changes);ng,_=repack_graphics_bank(g,0,streams);result=replace_entry(replace_entry(arc,2,ng),3,nc)
    newbank=graphics_bank(ng,0,allow_bank_aliases=True)
    for n in range(len(bank['frames'])):
        for cb in (0,6,7,8):
            try:before=raster(g,c,0,cb,n)
            except ValueError:
                require(n not in changes,'Changed frame is invalid');f,nf=bank['frames'][n],newbank['frames'][n]
                require(decode_stream(g,f['offset'],f['limit'],f['tile_count']*128).data==decode_stream(ng,nf['offset'],nf['limit'],nf['tile_count']*128).data and composition_records(c,cb,n)==composition_records(nc,cb,n),'Placeholder changed');continue
            want=before.copy()
            if cb==0:
                for x,y in coords.get(n,[]):want[y,x]=0
            require(np.array_equal(raster(ng,nc,0,cb,n),want),'Unexpected base layer change')
    return result,proof

def artwork(out):
    arc=(PARENT/'PL02_U.ARC').read_bytes();require(sha256(arc)==ARC_SHA,'Parent ARC changed');source=D/'hand_shot_review/generated.png';require(digest(source)==SOURCE_SHA,'Approved arm source changed');im=Image.open(source).convert('RGBA');words=struct.unpack_from('<16H',entry(arc,9),32);rgb=np.array([[(w>>s&31)*255//31 for s in (0,5,10)]for w in words],np.int32)
    # Use the same authored material swatches as the accepted ground arm fix.
    cell=im.crop((0,im.height//2,im.width//3,im.height));template=normalize(cell,40,rgb,width=60)
    def material(a,allowed):
        good=np.isin(a,allowed);require(np.any(good),'Missing approved arm material');_,near=distance_transform_edt(~good,return_indices=True);return a[near[0],near[1]]
    skin=material(template[16:20,13:17],(10,11,12,13));cuff=material(template[16:20,18:20],(13,15));sleeve=material(template[16:20,20:34],(5,6,7,8,9))
    targets={n:full(arc,n)for n in FRAMES};proof=[];coords=excess_pixels(arc);module=np.array(Image.open(PARENT/'ultimate_gun_size/pistol_module.png'))
    for q in records():
        n=q['frames'][1];old=targets[n];new=old.copy();mx,my=q['muzzle_anchor'];ex,ey=q['eye'];start,end=mx+8,ex-2;top,bottom=my+2,my+10;allowed=np.zeros(old.shape,bool)
        for x,y in coords[n]:new[y,x]=0;allowed[y,x]=True
        strip=np.concatenate((np.array(Image.fromarray(skin).resize((1,4),Image.Resampling.NEAREST)),np.array(Image.fromarray(cuff).resize((1,4),Image.Resampling.NEAREST)),np.array(Image.fromarray(sleeve).resize((end-start-2,4),Image.Resampling.NEAREST))),axis=1)
        for x in range(start,end):
            ys=np.flatnonzero(new[top:bottom,x])+top
            if not len(ys):continue
            lo,hi=int(ys.min()),int(ys.max())
            for y in range(lo,hi+1):
                allowed[y,x]=True
                # A one-pixel burgundy edge belongs to the pink jacket. Do not
                # sample a black weapon outline and stretch it across the arm.
                if x>=start+2 and y in (lo,hi):new[y,x]=5
                else:new[y,x]=strip[min(3,max(0,round((y-lo)*3/max(1,hi-lo)))),x-start]
        x,y,x2,y2=q['gun_module_box'];require(np.array_equal(new[y:y2,x:x2],module),'Canonical pistol changed');require(np.array_equal(new[~allowed],old[~allowed]),'Body outside wall arm changed');targets[n]=new
        proof.append({**q,'arm_box':[start,top,end,bottom],'removed_abandoned_gun_pixels':coords[n],'changed_pixels':int(np.count_nonzero(old!=new)),'dark_pixels_before':int(np.count_nonzero(allowed&np.isin(old,(1,2,3,4)))),'dark_pixels_after':int(np.count_nonzero(allowed&np.isin(new,(1,2,3,4)))),'gun_pixels_preserved':True,'all_other_body_pixels_preserved':True})
    for n,v in targets.items():save_image(v.tobytes(),(160,160),words,out/f'ultimate_{n:03}.png')
    board=Image.new('RGB',(1440,1152),'#252c3c');draw=ImageDraw.Draw(board)
    for i,n in enumerate(SHOTS):
        for row in range(2):
            v=full(arc,n) if row==0 else targets[n];rgba=np.concatenate((rgb[v].astype(np.uint8),((v>0)*255).astype(np.uint8)[...,None]),axis=2);pic=Image.fromarray(rgba,'RGBA').crop((48,61,96,93)).resize((432,288),Image.Resampling.NEAREST);x=i%3*480;y=i//3*576+row*288;board.paste(pic,(x,y),pic);draw.text((x+4,y+3),('BEFORE 'if row==0 else'AFTER ')+str(n),fill='white')
    board.save(out/'wall_arm_before_after_9x.png');return targets,proof

def prepare(out,art_only=False):
    out=out.resolve();require(out.is_relative_to(D)and not out.exists(),'Fresh isolated path required');require(digest(PARENT/'rin_nana.bin')==PARENT_SHA,'Parent BIN changed');out.mkdir();targets,proof=artwork(out);write(out/'registration.json',proof)
    if art_only:return
    base,baseproof=correct_base((PARENT/'PL02_U.ARC').read_bytes());result,packed=pack_resources(base,targets,FRAMES);(out/'PL02_U.ARC').write_bytes(result);write(out/'recipe.json',{'task':'ultimate_armor_nana','kind':'ultimate_wall_arm','parent_sha256':PARENT_SHA,'parent_arc_sha256':ARC_SHA,'generated_sha256':SOURCE_SHA,'frames':FRAMES,'registration':proof,'base_correction':baseproof,**packed,'files':{'PL02_U.ARC':sha256(result)},'full_ultimate_complete':False});print(json.dumps({'output':str(out),'sha256':sha256(result),'verification':packed['verification']}))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--art-only',action='store_true');a=p.parse_args();prepare(a.output,a.art_only)
