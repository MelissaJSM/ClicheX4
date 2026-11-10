"""새 대시 페이지를 원눈/귀축척과 발바닥 높이에 등록; 옛 몸체 사용 없음."""
from pathlib import Path
import argparse,json,sys
import numpy as np
from PIL import Image
from scipy.ndimage import label
D=Path(__file__).resolve().parent;N=D.parent;ROOT=D.parents[3]
sys.path[:0]=[str(D),str(ROOT),str(N/'native_restore'),str(N/'base_run_repaint'),str(N/'ultimate_air_repaint')]
from preview_restore import Archive,sha,digest,write,need,helper
from register_page import register
from register_first_before import eye
from check_first_geometry import info
from prepare_inputs import SRC,EXPECTED,merged

def main():
 p=argparse.ArgumentParser();p.add_argument('--source',required=True);p.add_argument('--out',required=True);p.add_argument('--refs',type=int,nargs='+',required=True);args=p.parse_args()
 folder=D/args.source;out=D/args.out;need(D in folder.resolve().parents and D in out.resolve().parents,'Work scope');need(1<=len(args.refs)<=4 and len(set(args.refs))==len(args.refs),'Refs')
 art=folder/'generated.png';g=json.loads((folder/'generation.json').read_text('utf8'));need(digest(SRC)==EXPECTED and digest(art)==g['workspace_sha256'],'Input SHA')
 a=Archive(SRC.read_bytes());im=Image.open(art).convert('RGBA');out.mkdir(exist_ok=False)
 plan={q['ref']:q for q in json.loads((D/'inputs_v1/manifest.json').read_text('utf8'))['records']if q['form']=='before'}
 pal=np.array([[(int(w)>>s&31)*255//31 for s in(0,5,10)]for w in a.words[16:32]],np.float32);records=[];rows=[]
 for i,n in enumerate(args.refs):
  need(n in plan and n not in(73,74),'Direct ordinary body ref')
  cx=i%2*im.width//2;cy=i//2*im.height//2;aa=np.array(im.crop((cx,cy,cx+im.width//2,cy+im.height//2)))
  lab,_=label(aa[:,:,3]>=128,np.ones((3,3)));counts=np.bincount(lab.flat);counts[0]=0;k=int(counts.argmax());yy,xx=np.nonzero(lab==k);need(len(xx)>1000,'Figure area');aa[lab!=k,3]=0
  box=[int(xx.min()+cx),int(yy.min()+cy),int(xx.max()+1+cx),int(yy.max()+1+cy)];crop=Image.fromarray(aa).crop((xx.min(),yy.min(),xx.max()+1,yy.max()+1));crop.save(out/f'source_{n:03}.png')
  sx,sy=eye(crop);old=merged(a,n,15);gy,gx=np.nonzero(old==14);need(len(gx)>0,'Native pupil');ey=int(gy.min()-160);ex=int(np.median(gx[gy==gy.min()])-160)
  ar=np.array(crop);Y,X=np.indices(ar.shape[:2]);ys,_=np.nonzero((ar[:,:,3]>=128)&(X<sx+crop.width*.18));crown=int(ys.min());scale=17/(sy-crown+1);width=round(crop.width*scale);split=round(sy+1);ntop=ey-round(split*scale)+1;hu=ey-ntop+1;bottom=plan[n]['bbox_world'][3];hl=bottom-ey-1
  need(1<=width<=64 and 1<=hl<=64,'Native size guard')
  up=register(crop.crop((0,0,crop.width,split)),(width,hu),pal,'area_vote');lo=register(crop.crop((0,split,crop.width,crop.height)),(width,hl),pal,'area_vote');native=np.concatenate((up,lo));ec=round((sx+.5)*width/crop.width-.5);ox=ex-ec
  native[:hu][native[:hu]==14]=12;native[hu-1,ec]=14
  target=np.zeros((384,384),np.uint8);target[ntop+160:ntop+160+len(native),ox+160:ox+160+width]=native
  Image.fromarray(target).save(out/f'before_{n:03}.png');a.rgba(target,16).save(out/f'before_{n:03}_rgba.png');yy,xx=np.nonzero(target);need(int(yy.max()-160)==bottom-1,'Sole Y')
  records.append({'ref':n,'source_crop':box,'source_eye':[sx,sy],'source_crown':crown,'scale_x':scale,'native_width':width,'upper_height':hu,'lower_height':hl,'split':split,'native_position':[ox,ntop],'eye_world':[ex,ey],'bbox_world':[int(xx.min()-160),int(yy.min()-160),int(xx.max()+1-160),int(yy.max()+1-160)],'indexed_sha256':sha(target.tobytes()),'old_body_pixels_used':0,'old_geometry':info(old,[ex,ey]),'new_geometry':info(target,[ex,ey])})
  rows.append((f'Ultimate before {n}',[('accepted idle',a.composite(0,15)[0]),('old body',a.composite(n,15)[0]),('new authored native',a.rgba(target,16)),('accepted new air',a.composite(39,15)[0])]))
 helper.grid(rows,out/'comparison.png',6);write(out/'registration.json',{'parent_arc_sha256':EXPECTED,'source_art':str(art.relative_to(ROOT)),'source_art_sha256':digest(art),'frames':records,'method':'원눈 위치/눈-귀17px·기존 최하단 soleY를 고정해 새 원화만 area_vote 등록한다. 손발x·권총·부분폼은 후속 검토 대상.','native_packed':False,'runtime_verified':False});print(out)
if __name__=='__main__':main()
