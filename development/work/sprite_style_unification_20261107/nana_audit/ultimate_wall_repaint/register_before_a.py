"""새 벽3몸체를 대기 눈/귀 축척과 원래 발바닥 높이로만 등록한다."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image
from scipy.ndimage import label
D=Path(__file__).resolve().parent;ROOT=D.parents[3];N=D.parent
sys.path[:0]=[str(ROOT),str(N/'native_restore'),str(N/'base_run_repaint'),str(N/'ultimate_air_repaint')]
from preview_restore import Archive,sha,digest,write,need,helper
from register_page import register
from register_first_before import eye
from check_first_geometry import info,full
SOURCE=N/'ultimate_air_repaint/packed_air_candidate_v1/PL02_U.ARC';PARENT='122c92c29fd0599772e18ac5ed3f918c8f0d40703fe08c396e4ccbdbb92f2c18'
ART=D/'before_a_v1/generated.png';ARTSHA='199daf32bca3e529760d725cf30451c2322b1252284d5beb896d0d924faa49dc'
def run(page='a',keys=(55,57,59),artsha=ARTSHA,form='before'):
 art=D/f'{form}_{page}_v1/generated.png';offset=16 if form=='before'else 0;mask=15 if form=='before'else 0
 need(digest(SOURCE)==PARENT and digest(art)==artsha,'Sources');a=Archive(SOURCE.read_bytes());im=Image.open(art).convert('RGBA');out=D/f'{form}_{page}_registered_v1';out.mkdir(exist_ok=False)
 meta=json.loads((D/'inputs_v1/manifest.json').read_text('utf8'));plan={q['ref']:q for q in meta['records']if q['form']=='before'};palette=np.array([[(int(w)>>s&31)*255//31 for s in(0,5,10)]for w in a.words[offset:offset+16]],np.float32);records=[];rows=[]
 for i,n in enumerate(keys):
  p=plan[n];cx=i%2*im.width//2;cy=i//2*im.height//2;cell=im.crop((cx,cy,cx+im.width//2,cy+im.height//2));aa=np.array(cell);labs,_=label(aa[:,:,3]>=128,np.ones((3,3)));counts=np.bincount(labs.flat);counts[0]=0;k=int(counts.argmax());yy,xx=np.nonzero(labs==k);need(len(xx)>1000,'Figure')
  aa[labs!=k,3]=0;box=[int(xx.min()+cx),int(yy.min()+cy),int(xx.max()+1+cx),int(yy.max()+1+cy)];crop=Image.fromarray(aa).crop((xx.min(),yy.min(),xx.max()+1,yy.max()+1));crop.save(out/f'source_{n:03}.png')
  sx,sy=eye(crop);ex,ey=map(int,p['eye_world']);ar=np.array(crop);Y,X=np.indices(ar.shape[:2]);ys,_=np.nonzero((ar[:,:,3]>=128)&(X<sx+crop.width*.18));crown=int(ys.min())
  scale=17/(sy-crown+1);width=round(crop.width*scale);split=round(sy+1);ntop=ey-round(split*scale)+1;hu=ey-ntop+1;bottom=p['bbox_world'][3];hl=bottom-ey-1
  upper=register(crop.crop((0,0,crop.width,split)),(width,hu),palette,'area_vote');lower=register(crop.crop((0,split,crop.width,crop.height)),(width,hl),palette,'area_vote');native=np.concatenate((upper,lower));ec=round((sx+.5)*width/crop.width-.5);ox=ex-ec
  native[:hu][native[:hu]==14]=12;native[hu-1,ec]=14;target=np.zeros((384,384),np.uint8);target[ntop+160:ntop+160+len(native),ox+160:ox+160+width]=native
  Image.fromarray(target).save(out/f'{form}_{n:03}.png');a.rgba(target,offset).save(out/f'{form}_{n:03}_rgba.png');yy,xx=np.nonzero(target);need(int(yy.max()-160)==bottom-1,'Sole Y')
  records.append({'ref':n,'source_crop':box,'source_eye':[sx,sy],'source_crown':crown,'scale_x':scale,'native_width':width,'upper_height':hu,'lower_height':hl,'split':split,'native_position':[ox,ntop],'eye_world':[ex,ey],'bbox_world':[int(xx.min()-160),int(yy.min()-160),int(xx.max()+1-160),int(yy.max()+1-160)],'indexed_sha256':sha(target.tobytes()),'old_body_pixels_used':0,'old_geometry':info(full(a,n),[ex,ey]),'new_geometry':info(target,[ex,ey])})
  rows.append((f'Ultimate wall {form} {n}',[('accepted idle',a.composite(0,mask)[0]),('old wall',a.composite(n,mask)[0]),('new whole-body source',a.rgba(target,offset)),('new air style',a.composite(33,mask)[0])]))
 helper.grid(rows,out/'comparison.png',6);write(out/'registration.json',{'parent_arc_sha256':PARENT,'source_art_sha256':artsha,'frames':records,'method':'눈/귀17px 기준 축척과 기존 발바닥Y. 새 전신 원화 상하부 area-vote. 손발x와 원권총은 후속 국소 정합 대상.','native_packed':False,'runtime_verified':False,'new_idle_not_used':True});print(str(out))
if __name__=='__main__':run()
