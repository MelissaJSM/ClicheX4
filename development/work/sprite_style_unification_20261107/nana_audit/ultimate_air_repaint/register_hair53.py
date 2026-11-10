"""53 전신 재작화의 뒤머리만 등록. 앞머리/귀/얼굴/의상/손발은 보존."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image
from scipy.ndimage import label
ROOT=Path(__file__).resolve().parents[4];D=Path(__file__).parent;N=D.parent
sys.path[:0]=[str(ROOT),str(D),str(N/'native_restore'),str(N/'base_run_repaint')]
from preview_restore import Archive,sha,digest,write,need,helper
from register_page import register
from register_first_before import eye
SRC=D/'hair53_settle_v1/generated.png';EXPECTED='cc5092874b0d0cebfd14dd56be95f1e98249a3b038741d99de423f832988b3d8'
def main():
 need(digest(SRC)==EXPECTED,'Art hash');out=D/'hair53_registered_v2';out.mkdir(exist_ok=False);a=Archive((N/'native_restore/nova_sync_v1/PL02_U.ARC').read_bytes());old=np.array(Image.open(D/'before_last_registered_v1/before_053.png'))
 raw=np.array(Image.open(SRC).convert('RGBA'));labs,_=label(raw[:,:,3]>=128,np.ones((3,3)));count=np.bincount(labs.flat);count[0]=0;k=int(count.argmax());yy,xx=np.nonzero(labs==k);box=[int(xx.min()),int(yy.min()),int(xx.max()+1),int(yy.max()+1)];raw[labs!=k,3]=0;crop=Image.fromarray(raw).crop(box);sx,sy=eye(crop);meta=next(r for r in json.loads((D/'before_last_registered_v1/registration.json').read_text('utf8'))['frames']if r['ref']==53);ex,ey=meta['eye_world'];arr=np.array(crop);Yc,Xc=np.indices(arr.shape[:2]);crown=int(np.nonzero((arr[:,:,3]>=128)&(Xc<sx+crop.width*.18))[0].min());scale=17/(sy-crown+1);w=round(crop.width*scale);split=round(sy+1);top=ey-round(split*scale)+1;hu=ey-top+1;bottom=meta['bbox_world'][3];hl=bottom-ey-1;pal=np.array([[(int(v)>>s&31)*255//31 for s in(0,5,10)]for v in a.words[16:32]],np.float32)
 value=np.concatenate((register(crop.crop((0,0,crop.width,split)),(w,hu),pal,'area_vote'),register(crop.crop((0,split,crop.width,crop.height)),(w,hl),pal,'area_vote')));ec=round((sx+.5)*w/crop.width-.5);ox=ex-ec;src=np.zeros_like(old);src[160+top:160+top+len(value),160+ox:160+ox+w]=value
 Y,X=np.indices(old.shape);Y=Y-160;X=X-160
 region=((Y>=-17)&(Y<-10)&(X>=9))|((Y>=-10)&(Y<-4)&(X>=11))|((Y>=-4)&(Y<5)&(X>=13))|((Y==5)&(X>=11))|((Y==6)&(X>=10))|((Y>=7)&(Y<15)&(X>=9))
 # These semantic gates lie outside the fixed face and clothing. Any skin,
 # white cuff or grey-shorts texel is independently excluded from replacement.
 protected=(old>=10)|np.isin(old,(2,3,4));mask=region&~protected
 new=old.copy();new[mask]=0;authored=mask&np.isin(src,(1,5,6,7,8,9));new[authored]=src[authored]
 need(np.array_equal(old[~mask],new[~mask]),'Protected pixels');need(label(new>0,np.ones((3,3)))[1]==1,'Detached hair');need(np.array_equal(old[Y>=15],new[Y>=15]),'Feet moved');need(np.array_equal(old[Y<-17],new[Y<-17]),'Crown changed')
 Image.fromarray(new).save(out/'before_053.png');Image.fromarray(src).save(out/'registered_source_053.png');Image.fromarray(mask.astype(np.uint8)*255).save(out/'rear_hair_semantic_mask.png');helper.grid([('53 settled hair',[('accepted idle',a.composite(0,15)[0]),('new previous',a.rgba(old,16)),('same new body / settling hair',a.rgba(new,16))])],out/'comparison.png',9)
 yy,xx=np.nonzero(new);write(out/'registration.json',{'ref':53,'source_sha256':EXPECTED,'source_crop':box,'source_eye':[sx,sy],'eye_world':[ex,ey],'native_position':[ox,top],'native_size':[w,len(value)],'changed_pixels':int(np.count_nonzero(new!=old)),'source_authored_hair_pixels':int(authored.sum()),'semantic_mask_sha256':sha(mask.tobytes()),'indexed_sha256':sha(new.tobytes()),'protected_pixels_exact':True,'ear_face_jacket_hands_legs_shoes_exact':True,'bounds_world':[int(xx.min()-160),int(yy.min()-160),int(xx.max()+1-160),int(yy.max()+1-160)],'art_review_pending':True,'native_packed':False,'runtime_verified':False});print(str(out))
if __name__=='__main__':main()
