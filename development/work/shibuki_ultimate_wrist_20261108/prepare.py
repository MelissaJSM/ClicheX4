"""얼티밋 전/후 아래팔만 총열 축에 맞춘 좌표 등록 후보."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image
H=Path(__file__).resolve().parent;ROOT=H.parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'work/motion_fixes_20261108')]
from common import board,write,sha
from scripts.export_x_consistency import Archive
from pack import pack
OLD=ROOT/'work/sprite_style_unification_20261107/shibuki_audit';GD=OLD/'ultimate_dash_barrel_guard01';PBS=(0,5,6,7,8)
SHOULDER={67:(-6,-1),69:(-9,4),71:(-14,10),75:(-13,10),77:(-9,1),79:(-5,-1),81:(-4,-2),83:(-5,-3)}
SETTINGS={68:(1,1,2),70:(1,1,2),72:(2,1,3),74:(2,1,3),76:(2,1,3),78:(1,2,3),80:(1,3,2),84:(2,0,3)}
FACE={68:(-12,-10,0,-1),70:(-15,-5,-3,4),72:(-22,1,-10,10),74:(-22,1,-10,10),76:(-21,1,-9,10),78:(-16,-8,-4,1),80:(-12,-11,0,-2),84:(-13,-14,-1,-5)}
def main(packed=False):
 a=Archive((H/'PL02_U.ARC').read_bytes());meta=json.loads((GD/'report.json').read_text('utf8'))['rows'];targets={};report=[];out=H/'candidate';out.mkdir(exist_ok=True)
 yy,xx=np.indices((384,384));x=xx-160;y=yy-160
 for n,(pull,lift,elbow) in SETTINGS.items():
  q=72 if n==74 else n;body=q-1;r=next(r for r in meta if r['shot_ref']==q);mx,my=r['muzzle_world'];sx,sy=SHOULDER[body]
  guard=np.array(Image.open(GD/f'{q:03}_mask.png'))>0
  head=np.array(Image.open(OLD/f'ultimate_dash_contacts04/{body:03}_head_mask.png'))>0
  legs=np.array(Image.open(OLD/f'ultimate_dash_contacts04/{body:03}_legs_mask.png'))>0
  # Old head masks are broad regions, including empty space occupied by the
  # firing wrist. Protect only the actual common head texels, not that space.
  neutral=a.layer(body)[0];firing=a.layer(n)[0]
  head&=(neutral>0)&(neutral==firing)
  # Shooting heads are not identical to their neutral pose. The face rectangle
  # includes deliberate transparent cuts in the bangs: retain those too.
  x0,y0,x1,y1=FACE[n]
  head|=(x>=x0)&(x<x1)&(y>=y0)&(y<y1)
  protect=guard|head|legs
  left=mx+10;right=sx+1;newleft=left-pull
  oldx=left+(x-newleft)*(right-left)/(right-newleft);t=np.clip((oldx-left)/(right-left),0,1)
  rise=lift*(1-t)+elbow*np.sin(np.pi*t)
  mapx=np.rint(oldx+160).astype(int).clip(0,383);mapy=np.rint(y+rise+160).astype(int).clip(0,383)
  mask=(x>=left)&(x<right)&(y>=my-2)&(y<sy+10)&~protect
  mapped=mask[mapy,mapx]&(x>=newleft)&(x<right)&~protect
  for b in PBS:
   v=a.layer(n,b)[0];dest=v.copy();dest[mask]=0;dest[mapped]=v[mapy,mapx][mapped];dest[protect]=v[protect]
   # Speed streaks belong to the original effect and keep their exact locations.
   if n==74:
    plain=a.layer(72,b)[0];fx=(v>0)&(plain==0);dest[fx]=v[fx]
   targets[n,b]=dest;Image.fromarray(dest).save(out/f'layer{b}_{n:03}.png')
   assert np.array_equal(dest[protect],v[protect])
  Image.fromarray((mask|mapped).astype('uint8')*255).save(out/f'mask_{n:03}.png')
  report.append({'ref':n,'pull_wrist_left':pull,'raise_wrist':lift,'raise_elbow_peak':elbow,'shoulder_anchor':[sx,sy],'muzzle_world':[mx,my],'head_legs_gun_exact':True})
 if packed:
  data,proof=pack(a.data,targets,PBS);(H/'PL02_fixed.ARC').write_bytes(data);write(H/'pack.json',proof);b=Archive(data)
 def render(n,mask):
  if packed:return b.composite(n,mask)[0]
  im=a.rgba(targets[n,0]);
  if mask:
   for pb in (8,5,7,6):im.alpha_composite(a.rgba(targets[n,pb],32 if pb==7 else 16))
  return im
 for form,mask in [('before',15),('after',0)]:
  pics=[]
  for n in SETTINGS:pics.extend([(f'{n} current {form}',a.composite(n,mask)[0]),(f'{n} wrist axis {form}',render(n,mask))])
  board(pics,out/(form+'.png'),cols=4)
  frames=[]
  for n in [68,70,72,74,76,72,74,76,78,80,84]:
   im=Image.new('RGB',(384,320),(28,36,49));s=render(n,mask).crop((112,120,208,200)).resize((384,320),Image.Resampling.NEAREST);im.paste(s,(0,0),s);frames.append(im)
  frames[0].save(out/(form+'.gif'),save_all=True,append_images=frames[1:],duration=80,loop=0)
 write(out/'registration.json',report);print('candidate ready; packed',packed)
if __name__=='__main__':main('--pack' in sys.argv)
