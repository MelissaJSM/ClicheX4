from pathlib import Path
import sys,json,struct,math
from collections import deque
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT))
from scripts.repack_zero import read_inputs
from scripts.extract_zero import save_image
from src.psx_player import graphics_bank,composition_frame,decode_stream
from src.psx_frame_edit import frame_coverage,read_indexed_png
D=Path(__file__).parent
source=ROOT/'work/ver_buki_riko/zero_extract/20261023T062408235550Z'
_,_,arc,gmeta,gfx,parts,_=read_inputs(source)
pal=(ROOT/'out/ver_buki_riko/riko_pilot_20261023T082720987715Z/candidate_palette.bin').read_bytes();words=struct.unpack('<16H',pal)
colors=np.array([[(w&31)*255//31,((w>>5)&31)*255//31,((w>>10)&31)*255//31] for w in words[1:]],dtype=np.int32)
head=np.array(Image.open(ROOT/'out/ver_buki_riko/riko_pilot_20261023T082720987715Z/riko_idle147_indexed.png'))[:19,12:35];hm=head!=0
hc=np.zeros((*head.shape,3),dtype=int);hc[hm]=colors[head[hm]-1]
hg=(hc[:,:,1]>hc[:,:,0]+8)&(hc[:,:,1]>hc[:,:,2]+8)&hm;hgy,hgx=np.nonzero(hg)
bank=graphics_bank(gfx,0);geometry={}
for n in range(44,53):
 f=bank['frames'][n];c=composition_frame(parts,0,n);raw=decode_stream(gfx,f['offset'],f['limit'],f['tile_count']*128).data
 coverage,size,b=frame_coverage(raw,f['tile_count'],c);safe=np.array([len(v)==1 for v in coverage]).reshape(size[1],size[0])
 for p in c['parts']:
  if p['tile']%16==0:safe[p['y']-b[1]:p['y']-b[1]+16,p['x']-b[0]]=False
 w=np.zeros((128,128),dtype=bool);w[64+b[1]:64+b[3],64+b[0]:64+b[2]]=safe;geometry[n]=(size,b,w)
def component(a):
 unseen=set(map(tuple,np.argwhere(a)));groups=[]
 while unseen:
  seed=unseen.pop();q=deque([seed]);g=[seed]
  while q:
   y,x=q.popleft()
   for dy,dx in [(-1,-1),(-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0),(1,1)]:
    v=(y+dy,x+dx)
    if v in unseen:unseen.remove(v);q.append(v);g.append(v)
  groups.append(g)
 return sorted(groups,key=len,reverse=True)
def normalize(cell,scale=.148,phase=.5,head_registration_x=0,head_registration_y=0):
 a=np.array(cell.convert('RGBA'));groups=component(a[:,:,3]>=180);keep=np.zeros(a.shape[:2],dtype=bool)
 for y,x in groups[0]:keep[y,x]=True
 a[~keep,3]=0;yy,xx=np.nonzero(keep);a=a[yy.min():yy.max()+1,xx.min():xx.max()+1]
 h,w=[math.ceil(v*scale) for v in a.shape[:2]];xs=np.minimum(((np.arange(w)+phase)/scale).astype(int),a.shape[1]-1);ys=np.minimum(((np.arange(h)+phase)/scale).astype(int),a.shape[0]-1);a=a[ys[:,None],xs[None,:]]
 mask=a[:,:,3]>=180;rgb=a[:,:,:3].astype(np.int32);ix=np.zeros((h,w),dtype=np.uint8);ix[mask]=np.argmin(((rgb[mask,None]-colors[None])**2).sum(2),1)+1
 green=(rgb[:,:,1]>rgb[:,:,0]+8)&(rgb[:,:,1]>rgb[:,:,2]+8)&mask&(np.indices(ix.shape)[0]<24);gy,gx=np.nonzero(green)
 hx=round(float(gx.mean()-hgx.mean()))+head_registration_x
 s=np.zeros((112,112),dtype=np.uint8);s[24:24+h,24:24+w]=ix
 s[:24+19+head_registration_y,24+hx-4:24+hx+28]=0;sub=s[24+head_registration_y:43+head_registration_y,24+hx:24+hx+23];sub[hm]=head[hm]
 yy,xx=np.nonzero(s);x0,y0,x1,y1=int(xx.min()),int(yy.min()),int(xx.max()+1),int(yy.max()+1)
 return s[y0:y1,x0:x1],[24+hx-x0,24+head_registration_y-y0]
def rgba(world):
 m=world!=0;r=np.zeros((*world.shape,4),dtype=np.uint8);r[m,:3]=colors[world[m]-1];r[m,3]=255;return Image.fromarray(r)
if __name__=='__main__':
 im=Image.open(D/(sys.argv[1] if len(sys.argv)>1 else 'generated_dash.png'));worlds={};records=[]
 scale=float(sys.argv[2]) if len(sys.argv)>2 else .148
 cols=2 if 'generated_fit' in im.filename else 3
 nums=(46,49,50,51) if cols==2 else (44,45,46,49,50,51)
 for i,n in enumerate(nums):
  cell=im.crop((round(i%cols*im.width/cols),round(i//cols*im.height/2),round((i%cols+1)*im.width/cols),round((i//cols+1)*im.height/2)));s,hl=normalize(cell,scale);h,w=s.shape;safe=geometry[n][2]
  target={44:(-17,-22),45:(-27,-16),46:(-29,-10),49:(-15,-22),50:(-13,-24),51:(-12,-22)}[n];tx,ty=target[0]-hl[0],24-h
  choices=[]
  for x in range(tx-6,tx+7):
   for y in range(ty-3,ty+5):
    bad=int(((s!=0)&~safe[64+y:64+y+h,64+x:64+x+w]).sum());headbad=int((hm&~safe[64+y+hl[1]:64+y+hl[1]+19,64+x+hl[0]:64+x+hl[0]+23]).sum())
    cost=bad*1000+headbad*100000+abs(x-tx)*3+abs(y+h-24)*15
    choices.append((cost,bad,x,y))
  _,bad,x,y=min(choices);world=np.zeros((128,128),dtype=np.uint8);world[64+y:64+y+h,64+x:64+x+w]=s;worlds[n]=world
  records.append({'frame':n,'source_scale':scale,'origin':[x,y],'head_world':[x+hl[0],y+hl[1]],'size':[w,h],'outside':bad,'components':[len(g) for g in component(world!=0)],'bad_world':[[int(xx-64),int(yy-64)] for yy,xx in np.argwhere((world!=0)&~safe)]})
 board=Image.new('RGBA',(3*384,2*340),(40,43,55,255));draw=ImageDraw.Draw(board)
 for i,(n,w) in enumerate(worlds.items()):
  board.alpha_composite(rgba(w[24:104,16:112]).resize((384,320),Image.Resampling.NEAREST),(i%3*384,i//3*340+20));draw.text((i%3*384+4,i//3*340+4),str(n),fill='white')
 board.save(D/'fit_review.png');np.savez(D/'worlds_probe.npz',**{str(n):w for n,w in worlds.items()});(D/'fit_registration.json').write_text(json.dumps(records,indent=2),encoding='utf8');print(json.dumps([{k:v for k,v in r.items() if k!='bad_world'} for r in records]))
