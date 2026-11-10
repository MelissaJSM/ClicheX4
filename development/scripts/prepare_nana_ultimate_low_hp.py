"""저체력 원화의 가로 압축/머리 세로 왜곡을 교정해6참조만 교체한다."""
import argparse,json,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import numpy as np
from PIL import Image,ImageDraw
from scipy.ndimage import label,distance_transform_edt
from scripts.prepare_nana_fourth_pilot import entry,render,require,write
from scripts.prepare_nana_ultimate_shot_arm import D,full,pack_resources
from scripts.prepare_nana_ultimate_reaction import source_face
from scripts.prepare_nana_fourth_reaction_art import face_anchor
from scripts.prepare_nana_ultimate_run_detail import register_shaded_legs
from scripts.prepare_nana_pilot import normalize
from scripts.project import digest
from scripts.discover_inputs import sha256
from scripts.extract_zero import save_image
PARENT=ROOT/'out/ver_rin_nana/nana_ultimate_reaction_20261104T095637072865Z'
PARENT_SHA='f9cfbb3b4e3f3529ca62c1b21059e6ae04fdbefac6a5e0652e83d2d122db5d53'
ARC_SHA='1899997a9e581e1a9e8ba6f1133464bf63ada696ea30cbd7b28cc98ce1be08ea'
SOURCE_SHA='8b14f5f3d4818c75ada996d8ebfc028acf17debd45ec08f5eff90ceb0fc29009'
FRAMES=list(range(120,126))

def artwork(out):
    src=D/'reaction_v1/generated.png';require(digest(src)==SOURCE_SHA,'Authored source changed');source=Image.open(src).convert('RGBA');arc=(PARENT/'PL02_U.ARC').read_bytes();base=render(arc,122)[1];words=struct.unpack_from('<16H',entry(arc,9),32);rgb=np.array([[(w>>s&31)*255//31 for s in(0,5,10)]for w in words],np.int32);yy,xx=np.indices((160,160));ex,ey,face=face_anchor(base)
    cell=source.crop((2*source.width//5,0,3*source.width//5,source.height));a=np.array(cell);labs,_=label(a[:,:,3]>=192,np.ones((3,3)));sizes=np.bincount(labs.flat);sizes[0]=0;keep=labs==sizes.argmax();sy,sx=np.nonzero(keep);a[~keep,3]=0;crop=Image.fromarray(a).crop((sx.min(),sy.min(),sx.max()+1,sy.max()+1));sx,sy,ox,oy=source_face(crop,base,ex,ey);h=48;width=round(h*crop.width/crop.height);v=normalize(crop,h,rgb,width=width);cx=round((sx+.5)*width/crop.width-.5+ox);cy=round((sy+.5)*h/crop.height-.5+oy);dx,dy=ex-cx,ey-cy;body=np.zeros_like(base);body[dy:dy+h,dx:dx+width]=v
    # Keep the accepted idle head at 1:1 pixel scale. A one-row downward
    # offset conveys fatigue without narrowing or stretching the head.
    head=full(arc,0)[52:74,67:91];hx,hy=67,53;body[:75]=0;body[hy:hy+head.shape[0],hx:hx+head.shape[1]]=head
    low=87;register_shaded_legs(body,base,ex,ey,np.isin(full((PARENT/'modified.arc').read_bytes(),122),(10,11,12,13)),yy>=low);gun=[70,80,77,88];x,y,x2,y2=gun;body[y:y2,x:x2]=base[y:y2,x:x2];dist,near=distance_transform_edt(body==0,return_indices=True);missing=(base>0)&(body==0);require(dist[missing].max(initial=0)<=4,'Registration requires redraw');body[missing]=body[near[0][missing],near[1][missing]]
    save_image(body.tobytes(),(160,160),words,out/'body_122.png');targets={};proof=[]
    for n in FRAMES:
        delta={120:1,121:1,122:0,123:0,124:-1,125:-1}[n];native=render(arc,n)[1];v=body.copy()
        for y in range(160):
            shift=delta if y<90 else round(delta*max(0,98-y)/8);sy=y-shift;v[y]=body[sy]if 0<=sy<160 else 0
        # The native mouth changes at (77,69). Move that expression with the
        # correctly sized head; do not splice a second whole face over it.
        v[71+delta,77]=native[69+delta,77];facebox=[77,71+delta,78,72+delta];x,y,x2,y2=gun;y+=delta;y2+=delta;v[y:y2,x:x2]=native[y:y2,x:x2];gunbox=[x,y,x2,y2];distance,near=distance_transform_edt(v==0,return_indices=True);missing=(native>0)&(v==0);require(distance[missing].max(initial=0)<=2,'Breathing loses coverage');v[missing]=v[near[0][missing],near[1][missing]];require(int(np.nonzero(v)[0].max())==102,'Feet moved');targets[n]=v;save_image(v.tobytes(),(160,160),words,out/f'ultimate_{n:03}.png');proof.append(dict(frames=[n,n],face_box=facebox,face_anchor=[76,69+delta],pistol_mask_bbox=gunbox,breathing_delta=delta,sole=102,uniform_source_size=[width,h],source_crop_size=list(crop.size),head_scale=[1,1],head_source_box=[67,52,91,74],head_destination_box=[hx,hy+delta,hx+24,hy+delta+22],lower_silhouette_from_y=low))
    board=Image.new('RGB',(1280,720),'#252c3c');draw=ImageDraw.Draw(board)
    for i,n in enumerate([0,122,120,122,124]):
        for row in range(2):
            v=full(arc,n)if row==0 or n==0 else targets[n];rgba=np.concatenate((rgb[v].astype(np.uint8),((v>0)*255).astype(np.uint8)[...,None]),axis=2);im=Image.fromarray(rgba,'RGBA').crop((56,44,104,108)).resize((240,320),Image.Resampling.NEAREST);x,y=i*256,row*360;board.paste(im,(x,y+25),im);draw.text((x+4,y+5),'IDLE'if n==0 else('BEFORE 'if row==0 else'AFTER ')+str(n),fill='white')
    board.save(out/'low_hp_comparison_5x.png');return targets,proof

def prepare(out,art_only=False):
    out=out.resolve();require(out.is_relative_to(D)and not out.exists(),'Fresh isolated output required');require(digest(PARENT/'rin_nana.bin')==PARENT_SHA and digest(PARENT/'PL02_U.ARC')==ARC_SHA,'Parent changed');out.mkdir();targets,proof=artwork(out);write(out/'registration.json',proof)
    if art_only:return
    result,packed=pack_resources((PARENT/'PL02_U.ARC').read_bytes(),targets,FRAMES);(out/'PL02_U.ARC').write_bytes(result);write(out/'recipe.json',dict(task='ultimate_armor_nana',kind='ultimate_low_hp',parent_sha256=PARENT_SHA,parent_arc_sha256=ARC_SHA,generated_sha256=SOURCE_SHA,frames=FRAMES,registration=proof,**packed,files={'PL02_U.ARC':sha256(result)},full_ultimate_complete=False));print(json.dumps(dict(output=str(out),sha256=sha256(result),verification=packed['verification'])))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--art-only',action='store_true');a=p.parse_args();prepare(a.output,a.art_only)
