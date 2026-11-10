from pathlib import Path
import sys,json
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT))
import numpy as np
from PIL import Image,ImageDraw
from work.ver_buki_riko.art_pilot.ryuenjin_v2.probe_fit import cells,heads
from work.ver_buki_riko.art_pilot.ladder_v1.fit_ladder import sample,normalize,front,component
from work.ver_buki_riko.art_pilot.wall_saber_v1.fit_wall import original,rgba,pal
from scripts.extract_zero import save_image
D=Path(__file__).parent
def replace_head(a,head):
 gy,gx=np.nonzero(np.isin(a,[4,8,14]));hy,hx=np.nonzero(np.isin(head,[4,8,14]))
 px=round(float(gx.mean()-hx.mean()));py=int(gy.min()-hy.min());out=np.zeros((128,128),np.uint8)
 out[32:32+a.shape[0],32:32+a.shape[1]]=a
 out[32+max(0,int(gy.min())-3):32+int(gy.max())+3,32+max(0,int(gx.min())-2):32+int(gx.max())+3]=0
 px+=32;py+=32;patch=out[py:py+19,px:px+23];patch[head!=0]=head[head!=0]
 yy,xx=np.nonzero(out);x0,y0=int(xx.min()),int(yy.min());return out[y0:yy.max()+1,x0:xx.max()+1],[px-x0,py-y0]
def fit():
 poses={};records=[];board=Image.new('RGBA',(1200,500),(32,36,48));dr=ImageDraw.Draw(board)
 for i,(n,im,scale,head) in enumerate(((146,cells[0],.074,front),(148,Image.open(D/'generated_rear.png'),.038,heads[1]),(156,cells[2],.074,front))):
  a,hp=(replace_head if n==146 else normalize)(sample(im,scale),head)
  loose=[]
  for c in component(a!=0)[1:]:
   loose.append(len(c))
   if len(c)>3:raise ValueError(('Detached major piece',n,loose))
   for y,x in c:a[y,x]=0
  h,w=a.shape;s=original(n)[2];opts=[]
  for y in range(-40,-5):
   for x in range(-32,1):
    bad=int(np.count_nonzero((a!=0)&~s[96+y:96+y+h,96+x:96+x+w]));target=abs(y+h-24)*4 if n==146 else abs(y+hp[1]+27)*2
    opts.append((bad*10000+abs(x+hp[0]+17)*2+target,bad,x,y))
  best=min(opts);_,bad,x,y=best
  poses[str(n)]=a;save_image(a.tobytes(),(w,h),pal,D/f'key_{n:03d}.png')
  records.append({'frame':n,'source_scale':scale,'head_local':hp,'position':[x,y],'head_world':[x+hp[0],y+hp[1]],'size':[w,h],'body_pixels':int(np.count_nonzero(a))-int(np.count_nonzero(head)),'outside':bad,'loose_background_removed':loose})
  board.alpha_composite(rgba(a).resize((w*6,h*6),Image.Resampling.NEAREST),(i*400,40));dr.text((i*400+4,4),str(n)+' '+str(bad),fill='white')
 np.savez(D/'key_pixels.npz',**poses);(D/'key_registration.json').write_text(json.dumps(records,indent=2),'utf8');board.save(D/'key_review.png');print(json.dumps(records))
if __name__=='__main__':fit()
