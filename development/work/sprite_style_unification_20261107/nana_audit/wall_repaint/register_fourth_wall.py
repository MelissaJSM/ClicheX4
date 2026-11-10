"""새 포스 벽 원화를 기본형과 같은 눈·발 높이에 직접 등록한다."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image
from scipy.ndimage import label
D=Path(__file__).resolve().parent;ROOT=D.parents[3]
sys.path[:0]=[str(ROOT),str(D.parent/'native_restore'),str(D.parent/'base_run_repaint')]
from preview_restore import Archive,sha,digest,need,write,helper
from register_page import register
from prepare_fourth_guides import source
SOURCES=[('fourth_keys_v1',[55,57,61,65],'8e642809631175d49dd12e11c683997800915e0614cf9c1587c8e542c26164f1'),('fourth_remaining_v1',[59,63],'3c9081b0383e91d3cd72148603978d35d57174f9fc6181dc79fd5ab0e8baf12c')]
def crops(im,count):
    arr=np.array(im);labs,_=label(arr[:,:,3]>=128,np.ones((3,3)));sizes=np.bincount(labs.flat);sizes[0]=0;objects=[]
    for k in np.flatnonzero(sizes>1000):
        y,x=np.nonzero(labs==k);box=(int(x.min()),int(y.min()),int(x.max()+1),int(y.max()+1));objects.append((int(np.mean(y)>im.height/2)if count==4 else 0,float(np.mean(x)),int(k),box))
    need(len(objects)==count,'Source object count')
    out=[]
    for _,_,k,box in sorted(objects):
        cp=arr.copy();cp[labs!=k,3]=0;out.append((Image.fromarray(cp).crop(box),box))
    return out
def eye(crop):
    ar=np.array(crop).astype(float);g=(ar[:,:,1]>ar[:,:,0]+15)&(ar[:,:,1]>ar[:,:,2]+15)&(ar[:,:,3]>=128);g[crop.height//3:]=False
    labs,count=label(g);objects=[]
    for k in range(1,count+1):
        y,x=np.nonzero(labs==k)
        if len(x)>=8:objects.append((int(y.min()),-len(x),float(np.median(x)),float(np.median(y))))
    need(bool(objects),'Source eye');_,_,x,y=min(objects);return x,y
def main():
    a=Archive((D.parent/'base_run_repaint/packed_joint_v2/PL00_U.ARC').read_bytes());need(sha(a.data)=='b5b3157a5c09c8603eec579f66251d8c69228b5948ceb9f35b5303ac52dd6f97','Parent')
    out=D/'fourth_registered_v1';out.mkdir(exist_ok=True);plan=json.loads((D/'inputs.json').read_text('utf8'));palette=np.array([[(int(w)>>s&31)*255//31 for s in(0,5,10)]for w in a.words[16:32]],np.float32);records=[];rows=[]
    for folder,refs,expected in SOURCES:
        path=D/folder/'generated.png';need(digest(path)==expected,'Source art');im=Image.open(path).convert('RGBA')
        for n,(crop,box) in zip(refs,crops(im,len(refs))):
            crop.save(out/f'source_{n:03}.png');basic=np.array(Image.open(source(n)));p=next(p for p in plan['frames']if p['ref']==n);ex,ey=map(int,p['eye_world']);sx,sy=eye(crop)
            Y,X=np.indices(basic.shape);yy,_=np.nonzero((basic>0)&(X<160+ex+8)&(Y<160+ey+2));top=int(yy.min()-160);bottom=int(np.where(basic>0)[0].max()-160)+1
            opaque=np.array(crop)[:,:,3]>=128;yy,_=np.nonzero(opaque&(np.indices(opaque.shape)[1]<sx+crop.width*.15));crown=float(yy.min());scale=(ey-top+1)/(sy-crown+1);width=round(crop.width*scale);split=round(sy+1);ntop=ey-round(split*scale)+1;hu=ey-ntop+1;hl=bottom-ey-1
            upper=register(crop.crop((0,0,crop.width,split)),(width,hu),palette,'area_vote');lower=register(crop.crop((0,split,crop.width,crop.height)),(width,hl),palette,'area_vote');native=np.concatenate([upper,lower]);ec=round((sx+.5)*width/crop.width-.5);native[:hu][native[:hu]==14]=12;native[hu-1,ec]=14
            ox=ex-ec;target=np.zeros((384,384),np.uint8);target[160+ntop:160+ntop+len(native),160+ox:160+ox+width]=native;Image.fromarray(target).save(out/f'fourth_{n:03}.png');a.rgba(target,16).save(out/f'fourth_{n:03}_rgba.png')
            records.append({'ref':n,'source':path.relative_to(ROOT).as_posix(),'source_sha256':expected,'source_crop':box,'source_eye':[sx,sy],'source_crown':crown,'source_scale_x':scale,'native_position':[ox,ntop],'native_width':width,'split':split,'height_above':hu,'height_below':hl,'eye':[ex,ey],'foot_y':bottom-1,'old_art_pixels_used':0,'indexed_sha256':sha(target.tobytes())})
            rows.append((f'wall {n}',[('대기 포스',a.composite(0,15)[0]),('현재 포스',a.composite(n,15)[0]),('새 기본',a.rgba(basic)),('새 포스 직접등록',a.rgba(target,16))]))
    for i in range(0,6,3):helper.grid(rows[i:i+3],out/f'comparison_{i//3+1}.png',7)
    write(out/'registration.json',{'frames':records,'scope':'원화 전체를 머리-눈/발 높이에 등록. 손·발 x 정합은 다음 단계. 원래 그림 덮기 없음.','native_packed':False,'runtime_verified':False});print(json.dumps({'out':str(out),'refs':[p['ref']for p in records]}))
if __name__=='__main__':main()
