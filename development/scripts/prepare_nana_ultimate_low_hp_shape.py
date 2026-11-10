"""대기 체형을 기준으로 저체력 몸통·팔·다리를 새 원화에서 등록한다."""
import argparse,json,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import numpy as np
from PIL import Image,ImageDraw
from scipy.ndimage import label,distance_transform_edt
from scripts.prepare_nana_fourth_pilot import entry,render,require,write
from scripts.prepare_nana_ultimate_shot_arm import D,full,pack_resources
from scripts.prepare_nana_pilot import normalize
from scripts.project import digest
from scripts.discover_inputs import sha256
from scripts.extract_zero import save_image
PARENT=ROOT/'out/ver_rin_nana/nana_ultimate_low_hp_20261104T101405078239Z'
PARENT_SHA='1cf2d96949548cf1b4e468a561fa82f67019017e6df5b74779f2ed50aad1ab9f'
ARC_SHA='1bb77ca9f4e6c4af4135fe025e8c00a2dc0b2865be9a564d5e96ea28bb982d05'
SOURCE_SHA='57e335a6506f2f851ba97391bc27e5f8df31954bb44fff543fe5b805fba5c214'
FRAMES=list(range(120,126))

def artwork(out):
    src=D/'low_hp_shape_v1/generated.png';require(digest(src)==SOURCE_SHA,'New body source changed');source=Image.open(src).convert('RGBA');arc=(PARENT/'PL02_U.ARC').read_bytes();base=render(arc,122)[1];words=struct.unpack_from('<16H',entry(arc,9),32);rgb=np.array([[(w>>s&31)*255//31 for s in(0,5,10)]for w in words],np.int32);yy,xx=np.indices((160,160));a=np.array(source);labs,_=label(a[:,:,3]>=192,np.ones((3,3)));sizes=np.bincount(labs.flat);sizes[0]=0;keep=labs==sizes.argmax();sy,sx=np.nonzero(keep);a[~keep,3]=0;crop=Image.fromarray(a).crop((sx.min(),sy.min(),sx.max()+1,sy.max()+1));ca=np.array(crop).astype(np.int32);cyy,cxx=np.indices(ca.shape[:2]);green=(ca[:,:,1]>ca[:,:,0]+8)&(ca[:,:,1]>ca[:,:,2]+8)&(ca[:,:,3]>=192)&(cyy<crop.height*.45);gy,gx=np.nonzero(green);require(len(gx)>0,'Source eye missing');h=51;width=round(h*crop.width/crop.height);v=normalize(crop,h,rgb,width=width);cx=round((float(np.median(gx))+.5)*width/crop.width-.5);cy=round((float(np.median(gy))+.5)*h/crop.height-.5);dx=76-cx;dy=103-h;body=np.zeros_like(base);body[dy:dy+h,dx:dx+width]=v
    # Match planted ankle positions by translation only. Retain the new
    # thighs/calves and their thickness instead of tracing the thin base.
    save_image(body.tobytes(),(160,160),words,out/'registered_before_foot.png');print(json.dumps(dict(source_size=[width,h],source_eye=[cx,cy],position=[dx,dy],foot_spans={str(y):np.flatnonzero(body[y]).tolist()for y in(90,98,100,102)},native_foot_spans={str(y):np.flatnonzero(base[y]).tolist()for y in(98,100,102)})),flush=True)
    shifts=[];old=body.copy();body[90:]=0;legs,count=label((old>0)&(yy>=90),np.ones((3,3)));require(count==2,'Expected two separated calves');leg_ids=sorted(range(1,count+1),key=lambda k:float(np.nonzero(legs==k)[1].mean()))
    for side,k in enumerate(leg_ids):
        region=legs==k;native_region=xx<82 if side==0 else xx>=82
        my,mx=np.nonzero(region&(yy>=100));ny,nx=np.nonzero((base>0)&native_region&(yy>=100));require(len(mx)and len(nx),'Foot landmark missing');shift=round(float(np.median(nx))-float(np.median(mx)));shifts.append(shift)
        for y in range(90,103):
            xs=np.flatnonzero((old[y]>0)&region[y]);delta=round(shift*(y-90)/12);dest=xs+delta;require(np.all(body[y,dest]==0),'Calves collide');body[y,dest]=old[y,xs]
    head=full(arc,0)[52:74,67:91];body[:75]=0;body[53:75,67:91]=head
    distance,near=distance_transform_edt(body==0,return_indices=True);missing=(base>0)&(body==0);require(distance[missing].max(initial=0)<=4,'Body needs local pose redraw');body[missing]=body[near[0][missing],near[1][missing]]
    save_image(body.tobytes(),(160,160),words,out/'body_122.png');targets={};proof=[];gun=[68,82,77,93];save_image(body[82:93,68:77].tobytes(),(9,11),words,out/'lowered_weapon_patch.png')
    for n in FRAMES:
        delta={120:1,121:1,122:0,123:0,124:-1,125:-1}[n];native=render(arc,n)[1];v=body.copy()
        for y in range(160):
            shift=delta if y<90 else round(delta*max(0,98-y)/8);sy=y-shift;v[y]=body[sy]if 0<=sy<160 else 0
        v[71+delta,77]=native[69+delta,77];distance,near=distance_transform_edt(v==0,return_indices=True);missing=(native>0)&(v==0);require(distance[missing].max(initial=0)<=2,'Breathing loses base coverage');v[missing]=v[near[0][missing],near[1][missing]];targets[n]=v;save_image(v.tobytes(),(160,160),words,out/f'ultimate_{n:03}.png');proof.append(dict(frames=[n,n],face_box=[77,71+delta,78,72+delta],breathing_delta=delta,sole=102,uniform_source_size=[width,h],source_crop_size=list(crop.size),head_scale=[1,1],head_source_box=[67,52,91,74],head_destination_box=[67,53+delta,91,75+delta],pistol_mode='authored_lowered',pistol_mask_bbox=[68,82+delta,77,93+delta],pistol_template_file='lowered_weapon_patch.png',foot_translation_only=shifts,old_leg_silhouette_not_reused=True))
    board=Image.new('RGB',(1024,720),'#252c3c');draw=ImageDraw.Draw(board)
    for i,n in enumerate([0,120,122,124]):
        for row in range(2):
            v=full(arc,n)if row==0 or n==0 else targets[n];rgba=np.concatenate((rgb[v].astype(np.uint8),((v>0)*255).astype(np.uint8)[...,None]),axis=2);im=Image.fromarray(rgba,'RGBA').crop((56,44,104,108)).resize((240,320),Image.Resampling.NEAREST);x,y=i*256,row*360;board.paste(im,(x,y+25),im);draw.text((x+4,y+5),'IDLE'if n==0 else('BEFORE 'if row==0 else'AFTER ')+str(n),fill='white')
    board.save(out/'low_hp_body_comparison_5x.png');return targets,proof

def prepare(out,art_only=False):
    out=out.resolve();require(out.is_relative_to(D)and not out.exists(),'Fresh isolated output required');require(digest(PARENT/'rin_nana.bin')==PARENT_SHA and digest(PARENT/'PL02_U.ARC')==ARC_SHA,'Parent changed');out.mkdir();targets,proof=artwork(out);write(out/'registration.json',proof)
    if art_only:return
    result,packed=pack_resources((PARENT/'PL02_U.ARC').read_bytes(),targets,FRAMES);(out/'PL02_U.ARC').write_bytes(result);write(out/'recipe.json',dict(task='ultimate_armor_nana',kind='ultimate_low_hp_shape',parent_sha256=PARENT_SHA,parent_arc_sha256=ARC_SHA,generated_sha256=SOURCE_SHA,frames=FRAMES,registration=proof,**packed,files={'PL02_U.ARC':sha256(result)},full_ultimate_complete=False));print(json.dumps(dict(output=str(out),sha256=sha256(result),verification=packed['verification'])))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--art-only',action='store_true');a=p.parse_args();prepare(a.output,a.art_only)
