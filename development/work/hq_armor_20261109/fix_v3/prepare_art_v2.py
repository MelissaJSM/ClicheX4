"""Register generated costume sheets into native indexed HQ animation frames."""
import sys,struct,json
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[2];H=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
from scripts.prepare_riko_ui import entry
from src.psx_ui_atlas import aliased_composition,local_composition
from src.psx_static_effect import compose_static

SIZE=(160,160);ORIGIN=(80,80)
def rgba(a,words):
 colors=np.array([[*(int(w>>s&31)*255//31 for s in (0,5,10)),255 if k else 0]for k,w in enumerate(words)],np.uint8)
 return Image.fromarray(colors[a],'RGBA')

def originals(mode):
 d=H/mode;b=(d/'originals/ST0D_0X.ARC').read_bytes();g=entry(b,0x10102);p=entry(b,10)
 words=list(struct.unpack_from('<16H',entry((d/'originals/COL0D_0X.ARC').read_bytes(),5),1120));world=[]
 for n in range(12):
  px,sz,bb,_=compose_static(g[63488:75776],local_composition(aliased_composition(p,2,n)))
  a=np.zeros((160,160),np.uint8);a[80+bb[1]:80+bb[3],80+bb[0]:80+bb[2]]=np.frombuffer(px,np.uint8).reshape(sz[1],sz[0]);world.append(a)
 return world,words

def register(mode,kind,words,basic):
 d=H/mode;sheet=Image.open(d/f'{kind}_generated.png').convert('RGBA');colors=np.array([[(w>>s&31)*255//31 for s in (0,5,10)]for w in words[1:]],np.int32)
 poses=[];info=[]
 for k,n in enumerate([0,3,6,9]):
  box=(k%2*sheet.width//2,k//2*sheet.height//2,(k%2+1)*sheet.width//2,(k//2+1)*sheet.height//2)
  im=sheet.crop(box);ar=np.array(im);ar[:,:,3]=np.where(ar[:,:,3]>=192,255,0);im=Image.fromarray(ar);bbox=im.getchannel('A').getbbox();im=im.crop(bbox)
  old=basic[n];yy,xx=np.nonzero(old);floor=int(yy.max())+1;oldh=yy.max()-yy.min()+1
  extra=(4 if kind=='force' else 6) if n!=9 else 2
  height=int(oldh+extra);scale=height/im.height;width=round(im.width*scale)
  im=im.convert('RGBa').resize((width,height),Image.Resampling.LANCZOS).convert('RGBA');ar=np.array(im)
  a=np.where(ar[:,:,3]>=128,((ar[:,:,:3].astype(np.int32)[:,:,None,:]-colors)**2).sum(3).argmin(2)+1,0).astype(np.uint8)
  _,feet=np.nonzero(a[-max(5,height//5):]);_,oldfeet=np.nonzero(old[max(0,floor-18):floor]);center=(feet.min()+feet.max())/2;target=(oldfeet.min()+oldfeet.max())/2
  x=round(target-center);y=floor-height;canvas=np.zeros((160,160),np.uint8)
  assert x>=0 and y>=0 and x+width<=160 and floor<=160
  canvas[y:floor,x:x+width]=a;poses.append(canvas);info.append({'pose':n,'cell':box,'opaque_crop':bbox,'scale':scale,'registered_bbox':[x-80,y-80,x+width-80,floor-80]})
 # Gesture shares the standing face and lower body. Only its upper-body gesture differs.
 # Keep the raised hand outside the head region. Copying the whole upper band
 # would erase Nana's palm while keeping only the lower sleeve.
 poses[1][:64,:104]=poses[0][:64,:104];poses[1][105:]=poses[0][105:]
 return poses,info

def expressions(mode,poses):
 idle,gesture,reaction,run=poses
 def face(a):
  # Retain the new closed mouth; locate native green iris clusters, not a fixed rectangle.
  mask=np.isin(a,[14,15]) if mode=='ver_rin_nana' else np.isin(a,[9,10])
  mask[66:]=False;mask[:25]=False
  if mode=='ver_buki_riko':
   # Red flowers, sunglasses and the neck ribbon share the iris palette.
   # Require nearby facial skin below the iris and exclude the head ornaments.
   skin=np.isin(a,[12,13,15]);near=np.zeros_like(mask)
   for dy in (1,2,3):
    for dx in (-1,0,1):near|=np.roll(np.roll(skin,-dy,axis=0),dx,axis=1)
   mask&=near;mask[:50]=False
  ys,xs=np.nonzero(mask)
  if not len(xs):raise ValueError('Iris registration needs inspection')
  # Exclude isolated costume/hat accents away from the face cluster.
  from collections import Counter
  row=Counter(ys).most_common(1)[0][0];mask[:max(0,row-2)]=False;mask[row+3:]=False
  ys,xs=np.nonzero(mask);mx=int(round(xs.mean()));my=int(round(ys.mean()))+5
  if mode=='ver_buki_riko':
   skinx=np.where(np.isin(a[max(0,my-2):my+1],[12,13,15]).any(axis=0))[0]
   skinx=skinx[(skinx>=mx-6)&(skinx<=mx+8)]
   if len(skinx):mx=int(round((skinx.min()+skinx.max())/2))
  return mask,(mx,my)
 eye,mouth=face(idle);closed=idle.copy();closed[eye]=1;half=idle.copy();yy,_=np.nonzero(eye);upper=eye.copy();upper[yy.min()+1:]=False;half[upper]=1
 def talking(a):
  _,(x,y)=face(a);mid=a.copy();opened=a.copy();mid[y,x]=7 if mode=='ver_rin_nana' else 9;opened[y,x:x+2]=1
  return mid,opened,(x,y)
 gm,go,gpos=talking(gesture);rm,ro,rpos=talking(reaction);_,neutral_open,npos=talking(idle)
 # World-space horizontal reflection uses the original X origin.
 mirror=idle[:,::-1].copy()
 return [idle,half,closed,gesture,gm,go,reaction,rm,ro,run,mirror,neutral_open],{'eye_pixels':int(eye.sum()),'mouths':[mouth,gpos,rpos,npos]}

def regions(mode,basic,force):
 yy,xx=np.indices((160,160));x=xx-80;y=yy-80
 result=[]
 for n,(base,full)in enumerate(zip(basic,force)):
  # Ownership follows the approved head / torso / sleeves / shoes+hem+rear veil split.
  neck=-17 if mode=='ver_rin_nana' else -14
  hem=8 if mode=='ver_rin_nana' else 19
  core=np.where(y<6,12,20)
  reg=np.where(y<neck,1,np.where(y>=hem,8,np.where(abs(x)<=core,2,4))).astype(np.uint8)
  if mode=='ver_rin_nana':
   pink=np.isin(base,[8,9,10])|np.isin(full,[8,9,10])
   hair=pink&(abs(x)>11)&(y<21);reg[hair]=1
   veil=np.isin(full,[1,3,4,5,13])&(abs(x)>17)&(y>=-25)&(y<hem)&~pink
   reg[veil]=8
  if n==10:reg=reg[:,::-1].copy()
  result.append(reg)
 return result

def make(mode):
 d=H/mode;out=d/'art';out.mkdir(exist_ok=True);basic,words=originals(mode)
 series={};reports={}
 for kind in ['force','ultimate','jacket']:
  poses,info=register(mode,kind,words,basic);frames,exp=expressions(mode,poses);series[kind]=frames;reports[kind]={'registration':info,'expressions':exp}
 masks=regions(mode,basic,series['force']);states={}
 for mask in range(16):states[mask]=[np.where((r&mask)!=0,f,b).astype(np.uint8)for r,f,b in zip(masks,series['force'],basic)]
 states[16]=series['jacket'];states[17]=series['ultimate']
 for n in range(12):assert np.array_equal(states[0][n],basic[n]) and np.array_equal(states[15][n],series['force'][n])
 board=Image.new('RGB',(6*160,3*320),(35,43,57));dr=ImageDraw.Draw(board)
 for state,frames in states.items():
  sd=out/f'{state:02}';sd.mkdir(exist_ok=True)
  for n,a in enumerate(frames):
   im=Image.fromarray(a,'P');im.putpalette([v for w in words for v in [(w&31)*255//31,(w>>5&31)*255//31,(w>>10&31)*255//31]]);im.info['transparency']=0;im.save(sd/f'{n:02}.png')
  im=rgba(frames[0],words).crop((40,20,120,144)).resize((160,248),Image.Resampling.NEAREST);x=state%6*160;y=state//6*320;board.paste(im,(x,y+30),im);dr.text((x+4,y+4),f'{state:02}',fill='white')
 board.save(out/'states.png')
 for kind,state in [('force',15),('jacket',16),('ultimate',17)]:
  board=Image.new('RGB',(1024,960),(35,43,57));dr=ImageDraw.Draw(board)
  for n,a in enumerate(states[state]):
   im=rgba(a,words).crop((16,8,144,144)).resize((256,272),0);x=n%4*256;y=n//4*320;board.paste(im,(x,y+24),im);dr.text((x+4,y+4),str(n),fill='white')
  board.save(out/(kind+'_poses.png'))
 (out/'report.json').write_text(json.dumps({'mode':mode,'palette':words,'states':18,'frames_each':12,'basic12_pixels_exact':True,'reports':reports},indent=2))
 print(mode,'prepared art')
if __name__=='__main__':make(sys.argv[1] if len(sys.argv)>1 else 'ver_rin_nana')
