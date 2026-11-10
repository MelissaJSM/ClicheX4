"""공중 대시 진입/종료93/94를 승인 얼티밋 의상으로 제작한다."""
import argparse,json,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import numpy as np
from PIL import Image,ImageDraw
from scipy.ndimage import label,distance_transform_edt
from scripts.prepare_nana_fourth_pilot import entry,render,require,write
from scripts.prepare_nana_ultimate_shot_arm import D,full,pack_resources
from scripts.prepare_nana_ultimate_run_detail import register_shaded_legs
from scripts.prepare_nana_pilot import normalize
from scripts.project import digest
from scripts.discover_inputs import sha256
from scripts.extract_zero import save_image
PARENT=ROOT/'out/ver_rin_nana/nana_ultimate_dash_hair_20261104T093054664466Z'
PARENT_SHA='a54eec967b15ca5e3852178f08bff4aa0c3c18c9aebe37bef006924597d0ca06'
ARC_SHA='d17d9e632fe937d43664ae4322de3984d3821ed2b63a077a92e75216c111d66d'
SOURCE_SHA='a1aaffad0fe071bfc18749865d2e4fd69e9794bf0e0139069d4d595d2f4415e5'
FRAMES=[93,94]

def artwork(out):
    src=D/'air_transition_v1/generated.png';require(digest(src)==SOURCE_SHA,'Source changed');source=Image.open(src).convert('RGBA');require(source.getchannel('A').getextrema()==(0,255),'Transparency required')
    arc=(PARENT/'PL02_U.ARC').read_bytes();fourth=(PARENT/'modified.arc').read_bytes();words=struct.unpack_from('<16H',entry(arc,9),32);rgb=np.array([[(w>>s&31)*255//31 for s in(0,5,10)]for w in words],np.int32);yy,xx=np.indices((160,160));master=full(arc,0);targets={};proof=[]
    for i,n in enumerate(FRAMES):
        base=render(arc,n)[1];ys,xs=np.nonzero((base==14)&(yy<80));require(len(xs)>0,'Native eye missing');ex,ey=round(float(np.median(xs))),round(float(np.median(ys)));bottom=int(np.nonzero(base)[0].max());ys,xs=np.nonzero(base);width=int(xs.max()-xs.min()+3)
        cell=source.crop((i*source.width//2,0,(i+1)*source.width//2,source.height));a=np.array(cell);labs,_=label(a[:,:,3]>=192,np.ones((3,3)));sizes=np.bincount(labs.flat);sizes[0]=0;keep=labs==sizes.argmax();sy,sx=np.nonzero(keep);a[~keep,3]=0;crop=Image.fromarray(a).crop((sx.min(),sy.min(),sx.max()+1,sy.max()+1));ca=np.array(crop).astype(np.int32);cyy,_=np.indices(ca.shape[:2]);green=(ca[:,:,1]>ca[:,:,0]+5)&(ca[:,:,1]>ca[:,:,2]+5)&(ca[:,:,3]>=192)&(cyy<crop.height*.6);gy,gx=np.nonzero(green);require(len(gx)>0,'Source eye missing');cx,cy=float(np.median(gx)),float(np.median(gy));choices=[]
        for h in range(32,65):
            vy=round((cy+.5)*h/crop.height-.5);choices.append((abs(h-1-vy-(bottom-ey)),abs(vy-16),h,vy))
        _,_,h,vy=min(choices);v=normalize(crop,h,rgb,width=width);vx=round((cx+.5)*width/crop.width-.5);target=np.zeros_like(base);dx,dy=ex-vx,ey-vy;require(min(dx,dy)>=0 and dx+width<=160 and dy+h<=160,'Outside canvas');target[dy:dy+h,dx:dx+width]=v
        # Register the whole upper head, including hair roots, together.
        # Do not paste an entire idle head over the newly drawn rear hair.
        upper=target[:ey+5].copy();target[:ey+5]=0
        for y in range(ey-16,ey+5):
            sy=round(ey+(y-ey)*(vy/16 if y<=ey else 1));sy=max(0,min(upper.shape[0]-1,sy));target[y]=upper[sy]
        fx,fy=ex-76,ey-68;target[65+fy:74+fy,73+fx:83+fx]=master[65:74,73:83]
        low=ey+17;skin=np.isin(full(fourth,n),(10,11,12,13));register_shaded_legs(target,base,ex,ey,skin,yy>=low)
        dist,near=distance_transform_edt(target==0,return_indices=True);missing=(base>0)&(target==0);require(dist[missing].max(initial=0)<=7,f'Transition {n} needs pose redraw');target[missing]=target[near[0][missing],near[1][missing]]
        # Preserve native trailing hair material where it extends the new art.
        trailing=(base>0)&np.isin(base,(5,6,7,8,9))&(xx>=ex+10)&(yy<low);pink=np.isin(target,(5,6,7,8,9));_,near=distance_transform_edt(~pink,return_indices=True);wrong=trailing&~pink;target[wrong]=target[near[0][wrong],near[1][wrong]]
        require(not np.any((base>0)&(target==0)),'Base escapes');require(int(np.nonzero(target)[0].max())==bottom,'Sole moved');require(np.array_equal(target[low:]>0,base[low:]>0),'Leg silhouette moved');targets[n]=target;save_image(target.tobytes(),(160,160),words,out/f'ultimate_{n:03}.png');proof.append(dict(frames=[n,n],eye=[ex,ey],sole=bottom,generated_size=[width,h],head_eye_to_ear=16,lower_silhouette_from_y=low,face_source='accepted idle face pixels',pistol_present=False,pistol_mask_bbox=None,registration_max_distance=float(dist[missing].max(initial=0)),registration_extension_pixels=int(missing.sum())))
    board=Image.new('RGB',(1280,360),'#252c3c');draw=ImageDraw.Draw(board)
    for i,n in enumerate([0,93,94,71]):
        v=targets.get(n,full(arc,n));rgba=np.concatenate((rgb[v].astype(np.uint8),((v>0)*255).astype(np.uint8)[...,None]),axis=2);im=Image.fromarray(rgba,'RGBA').crop((40,36,120,112)).resize((320,304),Image.Resampling.NEAREST);board.paste(im,(i*320,28),im);draw.text((i*320+4,8),{0:'ACCEPTED IDLE',71:'ACCEPTED DASH'}.get(n,str(n)),fill='white')
    board.save(out/'air_transition_review_4x.png');return targets,proof

def prepare(out,art_only=False):
    out=out.resolve();require(out.is_relative_to(D)and not out.exists(),'Fresh isolated output required');require(digest(PARENT/'rin_nana.bin')==PARENT_SHA and digest(PARENT/'PL02_U.ARC')==ARC_SHA,'Parent changed');out.mkdir();targets,proof=artwork(out);write(out/'registration.json',proof)
    if art_only:return
    result,packed=pack_resources((PARENT/'PL02_U.ARC').read_bytes(),targets,FRAMES);(out/'PL02_U.ARC').write_bytes(result);write(out/'recipe.json',dict(task='ultimate_armor_nana',kind='ultimate_air_transition',parent_sha256=PARENT_SHA,parent_arc_sha256=ARC_SHA,generated_sha256=SOURCE_SHA,frames=FRAMES,registration=proof,**packed,files={'PL02_U.ARC':sha256(result)},full_ultimate_complete=False));print(json.dumps(dict(output=str(out),sha256=sha256(result),verification=packed['verification'])))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--art-only',action='store_true');a=p.parse_args();prepare(a.output,a.art_only)
