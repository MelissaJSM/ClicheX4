from pathlib import Path
import sys,json,struct,math
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT))
from scripts.repack_zero import read_inputs
from scripts.extract_zero import save_image
from src.psx_player import graphics_bank,composition_frame,decode_stream
from src.psx_frame_edit import frame_coverage
from work.ver_buki_riko.art_pilot.dash_v1.fit_dash import component
D=Path(__file__).parent
_,_,arc,gmeta,gfx,parts,_=read_inputs(ROOT/'work/ver_buki_riko/zero_extract/20261023T062408235550Z')
pal=(ROOT/'out/ver_buki_riko/riko_pilot_20261023T082720987715Z/candidate_palette.bin').read_bytes();words=struct.unpack('<16H',pal)
colors=np.array([[(w&31)*255//31,((w>>5)&31)*255//31,((w>>10)&31)*255//31] for w in words],dtype=np.int32)
front=np.array(Image.open(ROOT/'out/ver_buki_riko/riko_pilot_20261023T082720987715Z/riko_idle147_indexed.png'))[:19,12:35]
bank=graphics_bank(gfx,0);geometry={}
for n in range(35,44):
 f=bank['frames'][n];c=composition_frame(parts,0,n);raw=decode_stream(gfx,f['offset'],f['limit'],f['tile_count']*128).data
 coverage,size,b=frame_coverage(raw,f['tile_count'],c);safe=np.array([len(set(v))==1 for v in coverage]).reshape(size[1],size[0])
 for p in c['parts']:
  if p['tile']%16==0:safe[p['y']-b[1]:p['y']-b[1]+16,p['x']-b[0]]=False
 w=np.zeros((128,128),dtype=bool);w[64+b[1]:64+b[3],64+b[0]:64+b[2]]=safe;geometry[n]=(size,b,w)

def rgba(a):
 r=np.zeros((*a.shape,4),dtype=np.uint8);m=a!=0;r[m,:3]=colors[a[m]];r[m,3]=255;return Image.fromarray(r)

def normalized(cell,scale=.14):
 a=np.array(cell.convert('RGBA'));mask=a[:,:,3]>=220;groups=component(mask);keep=np.zeros(mask.shape,dtype=bool)
 for y,x in groups[0]:keep[y,x]=True
 a[~keep,3]=0;yy,xx=np.nonzero(keep);a=a[yy.min():yy.max()+1,xx.min():xx.max()+1]
 h,w=[math.ceil(v*scale) for v in a.shape[:2]];xs=np.minimum(((np.arange(w)+.5)/scale).astype(int),a.shape[1]-1);ys=np.minimum(((np.arange(h)+.5)/scale).astype(int),a.shape[0]-1);a=a[ys[:,None],xs[None,:]]
 m=a[:,:,3]>=220;rgb=a[:,:,:3].astype(np.int32);ix=np.zeros((h,w),dtype=np.uint8);ix[m]=np.argmin(((rgb[m,None]-colors[None,1:])**2).sum(2),1)+1
 # Registration is measured from green hair, never a per-pose resize.
 green=np.isin(ix,[4,8,14]);yy,xx=np.nonzero(green);hx=int(xx.min())-1;hy=int(yy.min())-2
 canvas=np.zeros((96,96),dtype=np.uint8);canvas[16:16+h,16:16+w]=ix
 return canvas,[hx+16,hy+16]

def main():
 im=Image.open(D/'generated_wall_v3.png');cells={};heads={};scale=float(sys.argv[1]) if len(sys.argv)>1 else .13
 xs=(0,460,850,1280);ys=(0,450,850,1280)
 for i,n in enumerate(range(35,44)):
  cells[n],heads[n]=normalized(im.crop((xs[i%3],ys[i//3],xs[i%3+1],ys[i//3+1])),scale)
 # Fixed rear three-quarter view, derived once from generated pose 39.
 hx,hy=heads[39];back=cells[39][hy:hy+19,hx:hx+23].copy()
 save_image(back.tobytes(),(23,19),words,D/'rear_head_indexed.png')
 worlds={};records=[]
 for n in range(35,44):
  a=cells[n];hx,hy=heads[n];head=front if n<38 else back
  # Replace only the existing head rectangle, preserving raised arms beside it.
  patch=a[hy:hy+19,hx:hx+23]
  patch[np.isin(patch,[4,8,14])]=0
  patch[head!=0]=head[head!=0]
  yy,xx=np.nonzero(a);x0,y0=int(xx.min()),int(yy.min());s=a[y0:yy.max()+1,x0:xx.max()+1];h,w=s.shape;hl=[hx-x0,hy-y0]
  target={35:(-11,-27),36:(-12,-27),37:(-7,-27),38:(-17,-27),39:(-14,-26),40:(-14,-26),41:(-14,-26),42:(-14,-26),43:(-14,-26)}[n]
  tx,ty=target[0]-hl[0],target[1]-hl[1];safe=geometry[n][2];options=[]
  for dx in range(-8,9):
   for dy in range(-5,6):
    x,y=tx+dx,ty+dy;bad=int(((s!=0)&~safe[64+y:64+y+h,64+x:64+x+w]).sum())
    options.append((bad*1000+abs(dx)*3+abs(dy)*7,bad,x,y))
  _,bad,x,y=min(options);world=np.zeros((128,128),dtype=np.uint8);world[64+y:64+y+h,64+x:64+x+w]=s;worlds[n]=world
  records.append({'frame':n,'source_scale':scale,'origin':[x,y],'head_world':[x+hl[0],y+hl[1]],'size':[w,h],'outside':bad,'components':[len(g) for g in component(world!=0)],'bad_world':[[int(xx-64),int(yy-64)] for yy,xx in np.argwhere((world!=0)&~safe)]})
 board=Image.new('RGBA',(3*384,3*340),(40,43,55,255));draw=ImageDraw.Draw(board)
 for i,(n,w) in enumerate(worlds.items()):
  board.alpha_composite(rgba(w[24:104,16:112]).resize((384,320),Image.Resampling.NEAREST),(i%3*384,i//3*340+20));draw.text((i%3*384+4,i//3*340+4),str(n),fill='white')
 board.save(D/'fit_review.png');np.savez(D/'worlds_probe.npz',**{str(n):w for n,w in worlds.items()});(D/'fit_registration.json').write_text(json.dumps(records,indent=2),encoding='utf8');print(json.dumps(records))
if __name__=='__main__':main()
