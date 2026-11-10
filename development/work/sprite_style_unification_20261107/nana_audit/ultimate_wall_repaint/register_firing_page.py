"""새 벽사격 팔 원화의 전체 native 비교용 등록. 최종 몸체 대체 아님."""
from pathlib import Path
import sys,json,argparse
import numpy as np
from PIL import Image
from scipy.ndimage import label
D=Path(__file__).resolve().parent;N=D.parent;ROOT=D.parents[3]
sys.path[:0]=[str(ROOT),str(N/'native_restore'),str(N/'base_run_repaint'),str(N/'ultimate_air_repaint')]
from preview_restore import Archive,digest,sha,write,need,helper
from register_page import register
from register_first_before import eye
def main():
 p=argparse.ArgumentParser();p.add_argument('--page',choices=['a','b'],required=True);p.add_argument('--form',choices=['before','after'],default='before');p.add_argument('--sha',required=True);v=p.parse_args();page=v.page;form=v.form;art=D/f'firing_{page}_{form}_v1/generated.png';need(digest(art)==v.sha,'ArtSHA');src=N/'ultimate_air_repaint/packed_air_candidate_v1/PL02_U.ARC';need(digest(src)=='122c92c29fd0599772e18ac5ed3f918c8f0d40703fe08c396e4ccbdbb92f2c18','ARC');a=Archive(src.read_bytes());out=D/f'firing_{page}_{form}_registered_v1';out.mkdir(exist_ok=False);offset=16 if form=='before'else 0;mask=15 if form=='before'else 0
 plan={q['ref']:q for q in json.loads((D/'inputs_v1/manifest.json').read_text('utf8'))['records']if q['form']=='before'};refs=(56,58,60)if page=='a'else(62,64,66);im=Image.open(art).convert('RGBA');pal=np.array([[(int(w)>>s&31)*255//31 for s in(0,5,10)]for w in a.words[offset:offset+16]],np.float32);rows=[];recs=[]
 for i,n in enumerate(refs):
  p=plan[n-1];cx=i%2*im.width//2;cy=i//2*im.height//2;cell=im.crop((cx,cy,cx+im.width//2,cy+im.height//2));aa=np.array(cell);labs,_=label(aa[:,:,3]>=128,np.ones((3,3)));counts=np.bincount(labs.flat);counts[0]=0;k=int(counts.argmax());yy,xx=np.nonzero(labs==k);need(len(xx)>1000,'Figure');aa[labs!=k,3]=0;box=[int(xx.min()+cx),int(yy.min()+cy),int(xx.max()+1+cx),int(yy.max()+1+cy)];crop=Image.fromarray(aa).crop((xx.min(),yy.min(),xx.max()+1,yy.max()+1));crop.save(out/f'source_{n:03}.png')
  sx,sy=eye(crop);ex,ey=map(int,p['eye_world']);ar=np.array(crop);Y,X=np.indices(ar.shape[:2]);ys,_=np.nonzero((ar[:,:,3]>=128)&(X<sx+crop.width*.18));crown=int(ys.min());scale=17/(sy-crown+1);width=round(crop.width*scale);split=round(sy+1);ntop=ey-round(split*scale)+1;hu=ey-ntop+1;bottom=p['bbox_world'][3];hl=bottom-ey-1
  upper=register(crop.crop((0,0,crop.width,split)),(width,hu),pal,'area_vote');lower=register(crop.crop((0,split,crop.width,crop.height)),(width,hl),pal,'area_vote');native=np.concatenate((upper,lower));ec=round((sx+.5)*width/crop.width-.5);ox=ex-ec;native[:hu][native[:hu]==14]=12;native[hu-1,ec]=14;target=np.zeros((384,384),np.uint8);target[ntop+160:ntop+160+len(native),ox+160:ox+160+width]=native
  Image.fromarray(target).save(out/f'{form}_{n:03}.png');rows.append((f'wall fire {n}',[('accepted idle',a.composite(0,mask)[0]),('old shot',a.composite(n,mask)[0]),('new source native',a.rgba(target,offset))]));recs.append({'ref':n,'source_crop':box,'source_eye':[sx,sy],'eye_world':[ex,ey],'scale':scale,'native_position':[ox,ntop],'native_size':[width,len(native)],'source_upper_height':split,'native_upper_height':hu,'native_lower_height':hl,'source_crown':crown,'index_sha256':sha(target.tobytes()),'registration_only':True})
 helper.grid(rows,out/'comparison.png',6);write(out/'registration.json',{'source_art_sha256':v.sha,'frames':recs,'native_packed':False,'runtime_verified':False,'whole_source_for_review_only':True});print(out)
if __name__=='__main__':main()
