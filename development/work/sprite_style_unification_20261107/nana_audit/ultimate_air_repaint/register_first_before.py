"""얼티밋 새 공중4키: 원화 직접 등록. 머리/의상 옛 도트 덮기 없음."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[4];D=Path(__file__).parent;N=D.parent
sys.path[:0]=[str(ROOT),str(N/'native_restore'),str(N/'base_run_repaint'),str(N/'wall_repaint')]
from preview_restore import Archive,sha,digest,write,need,helper
from register_page import register,crop_cell
from scipy.ndimage import label
SRC=N/'native_restore/nova_sync_v1/PL02_U.ARC';SHA='bced7f9086a9e6a72440bab25cda7e0c87ccc121a2ffbbc970f750dee257da45'
ART=D/'before_first_v1/generated.png';ART_SHA='d99a968ade69d04be0f58c768ea90eb5641074f88c12d6cb1ea3c97995ead79d'

def eye(crop):
    ar=np.array(crop).astype(int);Y,_=np.indices(ar.shape[:2]);green=(ar[:,:,1]>ar[:,:,0]+15)&(ar[:,:,1]>ar[:,:,2]+15)&(ar[:,:,3]>=128)&(Y<crop.height*.55)
    labs,count=label(green);items=[]
    for k in range(1,count+1):
        y,x=np.nonzero(labs==k)
        if len(x)>=8:items.append((int(y.min()),-len(x),float(np.median(x)),float(np.median(y))))
    need(bool(items),'Source eye');_,_,x,y=min(items);return x,y

def main():
    need(digest(SRC)==SHA and digest(ART)==ART_SHA,'Input SHA');a=Archive(SRC.read_bytes());out=D/'before_first_registered_v2';out.mkdir(exist_ok=False)
    plan=json.loads((D/'inputs_first_v1/before_poses.json').read_text('utf8'));im=Image.open(ART).convert('RGBA')
    palette=np.array([[(int(w)>>s&31)*255//31 for s in(0,5,10)]for w in a.words[16:32]],np.float32);records=[];rows=[]
    for i,p in enumerate(plan):
        n=p['ref'];crop,box=crop_cell(im,i);crop.save(out/f'source_{n:03}.png');sx,sy=eye(crop);ex,ey=map(int,p['eye_world']);ar=np.array(crop);Y,X=np.indices(ar.shape[:2]);ys,_=np.nonzero((ar[:,:,3]>=128)&(X<sx+crop.width*.18));crown=int(ys.min())
        scale=17/(sy-crown+1);width=round(crop.width*scale);split=round(sy+1);ntop=ey-round(split*scale)+1;hu=ey-ntop+1;bottom=p['bbox_world'][3];hl=bottom-ey-1
        upper=register(crop.crop((0,0,crop.width,split)),(width,hu),palette,'area_vote');lower=register(crop.crop((0,split,crop.width,crop.height)),(width,hl),palette,'area_vote');native=np.concatenate((upper,lower))
        ec=round((sx+.5)*width/crop.width-.5);ox=ex-ec
        # Only quantized green eye fragments are consolidated at their original
        # pupil position. No old face, hair, limb, or clothing pixel is copied.
        native[:hu][native[:hu]==14]=12;native[hu-1,ec]=14
        target=np.zeros((384,384),np.uint8);target[ntop+160:ntop+160+len(native),ox+160:ox+160+width]=native
        Image.fromarray(target).save(out/f'before_{n:03}.png');a.rgba(target,16).save(out/f'before_{n:03}_rgba.png')
        yy,xx=np.nonzero(target);need(int(yy.max()-160)==bottom-1,'Foot height');records.append({'ref':n,'source_crop':box,'source_eye':[sx,sy],'source_crown':crown,'scale_x':scale,'native_width':width,'upper_height':hu,'lower_height':hl,'split':split,'native_position':[ox,ntop],'eye_world':[ex,ey],'bbox_world':[int(xx.min()-160),int(yy.min()-160),int(xx.max()+1-160),int(yy.max()+1-160)],'indexed_sha256':sha(target.tobytes()),'old_body_pixels_used':0})
        rows.append((f'Ultimate {n}',[('accepted idle',a.composite(0,15)[0]),('current pose',a.composite(n,15)[0]),('new authored native',a.rgba(target,16))]))
    helper.grid(rows,out/'comparison.png',7);write(out/'registration.json',{'parent_arc_sha256':SHA,'source_art_sha256':ART_SHA,'frames':records,'method':'fixed eye/ear17px and original footheight; source upper/lower area-vote quantization. Hand/foot x contacts pending, not packed.','runtime_verified':False,'whole_air_completed':False})
    print(json.dumps({'out':str(out),'refs':[p['ref']for p in plan]}))
if __name__=='__main__':main()
