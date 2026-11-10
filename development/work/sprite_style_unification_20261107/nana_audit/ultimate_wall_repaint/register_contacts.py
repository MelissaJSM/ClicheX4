"""새 원화의 벽손과 아래쪽 발 모듈만 작은 강체이동으로 기존 접점에 맞춘다."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image,ImageDraw
from scipy.ndimage import label
D=Path(__file__).resolve().parent;ROOT=D.parents[3];N=D.parent
sys.path[:0]=[str(ROOT),str(N/'native_restore'),str(N/'ultimate_air_repaint')]
from preview_restore import Archive,write,digest,sha,need,helper
from check_first_geometry import full
HANDS={55:([ (13,-17),(18,-17),(18,-6),(13,-6),(11,-8),(11,-11),(13,-13)],-1,-1),57:([(14,-19),(20,-19),(20,-9),(13,-9),(11,-11),(12,-14)],0,-1),61:([(14,-21),(20,-21),(20,-10),(14,-10),(12,-13),(12,-16)],-1,0),63:([(17,-24),(23,-24),(23,-12),(16,-12),(13,-15),(13,-18)],-2,-1),65:([(12,-25),(18,-25),(18,-17),(13,-17),(11,-19)],0,-1)}
FEET={55:(9,14,-1),57:(10,12,-1),59:(12,14,-1),61:(10,13,-1),63:(12,14,-2)}
def move(ar,mask,dx,dy):
 yy,xx=np.nonzero(mask&(ar>0));source=ar.copy();new=ar.copy();new[yy,xx]=0;oy,ox=yy+dy,xx+dx;coll=(new[oy,ox]>0)&(new[oy,ox]!=source[yy,xx]);over=[]
 for k in np.flatnonzero(coll):over.append({'xy':[int(ox[k]-160),int(oy[k]-160)],'before':int(new[oy[k],ox[k]]),'source':int(source[yy[k],xx[k]])})
 new[oy,ox]=source[yy,xx];return new,{'source_pixels':len(yy),'shift':[dx,dy],'collisions':over}
def main():
 a=Archive((N/'ultimate_air_repaint/packed_air_candidate_v1/PL02_U.ARC').read_bytes());out=D/'contacts_probe_v2';out.mkdir(exist_ok=False);Y,X=np.indices((384,384));rows=[];records=[]
 for n in(55,57,59,61,63,65):
  path=D/('before_a_registered_v1'if n<61 else'before_b_registered_v1')/f'before_{n:03}.png';original=np.array(Image.open(path));target=original.copy();changes=[]
  if n==59:
   need(target[140,150]==5,'Isolated hair point');lab,num=label(target>0,np.ones((3,3)));need(int((lab==lab[140,150]).sum())==1,'Not an isolated texel');target[140,150]=0;changes.append({'region':'native isolated hair point','xy':[-10,-20],'before':5,'after':0,'reason':'한 장의 새 전신 원화 축소 후 머리에서 단독 분리된1점 제거. 원래 게임 머리를 붙이지 않음.'})
  if n in HANDS:
   polygon,dx,dy=HANDS[n];im=Image.new('L',(384,384));ImageDraw.Draw(im).polygon([(x+160,y+160)for x,y in polygon],fill=255);mask=np.array(im)>0;target,rec=move(target,mask,dx,dy);rec.update(region='new wall hand/cuff',polygon=polygon);changes.append(rec);Image.fromarray(np.where(mask,255,0).astype(np.uint8)).save(out/f'hand_mask_{n:03}.png')
  if n in FEET:
   x,y,dx=FEET[n];mask=(X>=160+x)&(Y>=160+y);target,rec=move(target,mask,dx,0);rec.update(region='new lower leg/shoe',lower_bound=[x,y]);changes.append(rec)
  need(label(target>0,np.ones((3,3)))[1]==1,f'Disconnected {n}');need(np.max(np.nonzero(target)[0])==np.max(np.nonzero(original)[0]),'Sole height')
  Image.fromarray(target).save(out/f'before_{n:03}.png');records.append({'ref':n,'source':path.relative_to(ROOT).as_posix(),'source_sha256':digest(path),'changes':changes,'result_sha256':sha(target.tobytes()),'connected':True,'body_color_fill_used':False,'old_sprite_pixels_used':0})
  rows.append((f'wall {n}',[('idle',a.composite(0,15)[0]),('old contact',a.composite(n,15)[0]),('new source registration',a.rgba(original,16)),('new local contacts',a.rgba(target,16))]))
 for i in range(2):helper.grid(rows[i*3:i*3+3],out/f'comparison_{i+1}.png',6)
 write(out/'registration.json',{'frames':records,'method':'직접 확인한 색인 격자에서 새 손/커프와 아래 종아리/신발만1~2px 강체이동. 몸 전체/머리/의상색/원화 질감은 일괄 보정하지 않는다.','art_review_pending':True,'native_packed':False,'runtime_verified':False});print(str(out))
if __name__=='__main__':main()
