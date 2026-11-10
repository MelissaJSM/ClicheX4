"""새 얼티밋 대시4키를 고정된 눈/귀 축척과 발바닥 높이에 등록한다."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image
from scipy.ndimage import label
D=Path(__file__).resolve().parent; N=D.parent; ROOT=D.parents[3]
sys.path[:0]=[str(ROOT),str(N/'native_restore'),str(N/'base_run_repaint'),str(N/'ultimate_air_repaint')]
from preview_restore import Archive,sha,digest,write,need,helper
from register_page import register
from register_first_before import eye
from check_first_geometry import info,full
SRC=N/'ultimate_wall_repaint/packed_wall_candidate_v1/PL02_U.ARC'
PARENT='e151044c37b5a59016f10d8c4d9637ffd4e192563f03c6a76df528383cfb4031'
ART=D/'before_first_v1/generated.png'; ART_SHA='513193faafe00c81d317dd122fc016901d4eda169abd5f49962126c73c9d9d22'
KEYS=(67,71,79,93)
def main():
    need(digest(SRC)==PARENT and digest(ART)==ART_SHA,'Input SHA')
    a=Archive(SRC.read_bytes());im=Image.open(ART).convert('RGBA');out=D/'before_first_registered_v2';out.mkdir(exist_ok=False)
    plan={q['ref']:q for q in json.loads((D/'inputs_v1/manifest.json').read_text('utf8'))['records'] if q['form']=='before'}
    palette=np.array([[(int(w)>>s&31)*255//31 for s in(0,5,10)] for w in a.words[16:32]],np.float32)
    records=[];rows=[]
    for i,n in enumerate(KEYS):
        p=plan[n];cx=i%2*im.width//2;cy=i//2*im.height//2
        cell=im.crop((cx,cy,cx+im.width//2,cy+im.height//2));aa=np.array(cell)
        labs,_=label(aa[:,:,3]>=128,np.ones((3,3)));counts=np.bincount(labs.flat);counts[0]=0;k=int(counts.argmax())
        yy,xx=np.nonzero(labs==k);need(len(xx)>1000,'Figure');aa[labs!=k,3]=0
        box=[int(xx.min()+cx),int(yy.min()+cy),int(xx.max()+1+cx),int(yy.max()+1+cy)]
        crop=Image.fromarray(aa).crop((xx.min(),yy.min(),xx.max()+1,yy.max()+1));crop.save(out/f'source_{n:03}.png')
        sx,sy=eye(crop)
        old=full(a,n);gy,gx=np.nonzero(old==14);need(len(gx)>0,'Native pupil')
        ey=int(gy.min()-160);ex=int(np.median(gx[gy==gy.min()])-160)
        ar=np.array(crop);Y,X=np.indices(ar.shape[:2]);ys,_=np.nonzero((ar[:,:,3]>=128)&(X<sx+crop.width*.18));crown=int(ys.min())
        scale=17/(sy-crown+1);width=round(crop.width*scale);split=round(sy+1);ntop=ey-round(split*scale)+1;hu=ey-ntop+1;bottom=p['bbox_world'][3];hl=bottom-ey-1
        upper=register(crop.crop((0,0,crop.width,split)),(width,hu),palette,'area_vote')
        lower=register(crop.crop((0,split,crop.width,crop.height)),(width,hl),palette,'area_vote')
        native=np.concatenate((upper,lower));ec=round((sx+.5)*width/crop.width-.5);ox=ex-ec
        native[:hu][native[:hu]==14]=12;native[hu-1,ec]=14
        target=np.zeros((384,384),np.uint8);target[ntop+160:ntop+160+len(native),ox+160:ox+160+width]=native
        Image.fromarray(target).save(out/f'before_{n:03}.png');a.rgba(target,16).save(out/f'before_{n:03}_rgba.png')
        yy,xx=np.nonzero(target);need(int(yy.max()-160)==bottom-1,'Foot height')
        records.append({'ref':n,'source_crop':box,'source_eye':[sx,sy],'source_crown':crown,'scale_x':scale,'native_width':width,'upper_height':hu,'lower_height':hl,'split':split,'native_position':[ox,ntop],'eye_world':[ex,ey],'bbox_world':[int(xx.min()-160),int(yy.min()-160),int(xx.max()+1-160),int(yy.max()+1-160)],'indexed_sha256':sha(target.tobytes()),'old_body_pixels_used':0,'old_geometry':info(full(a,n),[ex,ey]),'new_geometry':info(target,[ex,ey])})
        rows.append((f'Ultimate dash {n}',[('accepted idle',a.composite(0,15)[0]),('old dash',a.composite(n,15)[0]),('new authored native',a.rgba(target,16)),('new air detail',a.composite(39,15)[0])]))
    helper.grid(rows,out/'comparison.png',6)
    write(out/'registration.json',{'parent_arc_sha256':PARENT,'source_art_sha256':ART_SHA,'frames':records,'method':'눈/귀17px 축척과 기존 발바닥Y, 원화 상하부 area-vote. 손발 x/권총/경계색은 다음 국소 검사 대상. 옛 몸체나 의상 도트는 복사하지 않았다.','native_packed':False,'runtime_verified':False})
    print(out)
if __name__=='__main__':main()
