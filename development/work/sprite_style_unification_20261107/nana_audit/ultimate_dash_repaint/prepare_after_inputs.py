"""새 대시 전신10개를 고정한 후폼 의상 편집 입력. 원본 자원 무수정."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image
D=Path(__file__).resolve().parent;N=D.parent;ROOT=D.parents[3]
sys.path[:0]=[str(ROOT),str(D),str(N/'native_restore')]
from preview_restore import Archive,digest,sha,write,need
from prepare_inputs import SRC,EXPECTED
from collect_before_bodies import SOURCES
WINDOW=(120,120,200,200)
def main():
 need(digest(SRC)==EXPECTED,'Parent');a=Archive(SRC.read_bytes());out=D/'after_inputs_v1';out.mkdir(exist_ok=False);records=[]
 for page,refs in [('a',(67,71,79,93)),('b',(69,75,77,81)),('c',(83,94))]:
  board=Image.new('RGBA',(1280,1280));rows=[]
  for i,n in enumerate(refs):
   p=D/SOURCES[n]/f'before_{n:03}.png';ar=np.array(Image.open(p));im=a.rgba(ar,16);outside=np.array(im)[:,:,3].copy();outside[120:200,120:200]=0;need(not outside.any(),'Input clips');board.alpha_composite(im.crop(WINDOW).resize((640,640),Image.Resampling.NEAREST),(i%2*640,i//2*640));Y,X=np.indices(ar.shape);ys,xs=np.nonzero((ar==14)&(Y<170));ey=ys.min();ex=np.median(xs[ys==ey]);ys,xs=np.nonzero(ar)
   rows.append({'ref':n,'source':p.relative_to(ROOT).as_posix(),'source_sha256':digest(p),'eye_world':[float(ex-160),int(ey-160)],'bbox_world':[int(xs.min()-160),int(ys.min()-160),int(xs.max()+1-160),int(ys.max()+1-160)],'cell':[i%2,i//2]})
  if len(refs)==2:
   for i,n in enumerate((0,39),2):board.alpha_composite(a.composite(n,0)[0].crop(WINDOW).resize((640,640),Image.Resampling.NEAREST),(i%2*640,i//2*640))
  board.save(out/f'{page}_fixed_bodies.png');write(out/f'{page}_poses.json',rows);records.extend(rows)
 master=Image.new('RGBA',(1280,1280))
 for i,n in enumerate((0,33,39,65)):master.alpha_composite(a.composite(n,0)[0].crop(WINDOW).resize((640,640),Image.Resampling.NEAREST),(i%2*640,i//2*640))
 master.save(out/'after_style_master.png');write(out/'manifest.json',{'parent_arc_sha256':EXPECTED,'window':WINDOW,'cell':[640,640],'scale':8,'records':records,'images':{p.name:digest(p)for p in out.glob('*.png')},'scope':'전폼의 새 머리/눈/사지/권총을 보존하며 재킷만 기존 후폼 의상으로 전환할 원화 입력. c하단2셀은 참조.','native_packed':False,'runtime_verified':False});print(out)
if __name__=='__main__':main()
