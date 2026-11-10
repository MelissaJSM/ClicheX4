"""Normalize generated wall keys at one common scale; report geometry before editing."""
from pathlib import Path
import sys,json,math,struct
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT))
from work.ver_buki_riko.art_pilot.ladder_v1.fit_ladder import sample,normalize,front,component
from scripts.repack_zero import read_inputs
from scripts.extract_zero import save_image
from src.psx_player import graphics_bank,composition_frame,decode_stream,compose_indices
from src.psx_frame_edit import frame_coverage
from work.ver_buki_riko.art_pilot.sword_v1.inspect_sword import rgba,pal,epal
D=Path(__file__).parent
profile,_,arc,gmeta,gfx,parts,zpal=read_inputs(ROOT/'work/ver_buki_riko/zero_extract/20261023T062408235550Z')
bank=graphics_bank(gfx,1)
KEYS=[50,51,54,57,61,65]

def original(n):
 f=bank['frames'][n];c=composition_frame(parts,5,n);raw=decode_stream(gfx,f['offset'],f['limit'],f['tile_count']*128).data
 data,size,b,_=compose_indices(raw,f['tile_count'],c);cov,_,_=frame_coverage(raw,f['tile_count'],c)
 safe=np.array([bool(v) for v in cov]).reshape(size[1],size[0])
 for p in c['parts']:
  if p['tile']%16==0:safe[p['y']-b[1]:p['y']-b[1]+16,p['x']-b[0]]=False
 w=np.zeros((192,192),bool);w[96+b[1]:96+b[3],96+b[0]:96+b[2]]=safe
 return np.frombuffer(data,np.uint8).reshape(size[1],size[0]),b,w

def review(worlds,path):
 board=Image.new('RGBA',(3*384,math.ceil(len(worlds)/3)*312),(32,36,48));draw=ImageDraw.Draw(board)
 pairs={51:52,53:52,54:55,56:55,57:58,59:60,61:62,63:64,65:64}
 for i,(n,w) in enumerate(worlds.items()):
  _,b,safe=original(n);cell=Image.new('RGBA',(192,192));s=np.zeros((192,192,4),np.uint8);s[safe]=[51,55,66,255];cell.alpha_composite(Image.fromarray(s));cell.alpha_composite(rgba(w))
  e=pairs.get(n)
  if e:
   a,eb,_=original(e);cell.alpha_composite(rgba(a,epal),(96+eb[0],96+eb[1]))
  pic=cell.crop((16,52,144,150)).resize((384,294),Image.Resampling.NEAREST);board.alpha_composite(pic,(i%3*384,i//3*312+18));draw.text((i%3*384+5,i//3*312+2),str(n)+' STATIC',fill='white')
 board.save(path)

def main():
 scale=float(sys.argv[1]) if len(sys.argv)>1 else .125
 im=Image.open(D/'generated_wall_compact.png');worlds={};regs=[]
 for i,n in enumerate(KEYS):
  cell=im.crop((i%3*512,i//3*512,(i%3+1)*512,(i//3+1)*512))
  a,hp=normalize(sample(cell,scale),front);h,w=a.shape;safe=original(n)[2]
  hx,hy=-12,-25;x,y=hx-hp[0],hy-hp[1];options=[]
  for dx in range(-7,8):
   for dy in range(-4,5):
    tx,ty=x+dx,y+dy;bad=int(np.count_nonzero((a!=0)&~safe[96+ty:96+ty+h,96+tx:96+tx+w]));options.append((bad*1000+abs(dx)*3+abs(dy)*4,bad,tx,ty))
  _,bad,x,y=min(options);wld=np.zeros((192,192),np.uint8);wld[96+y:96+y+h,96+x:96+x+w]=a;worlds[n]=wld
  regs.append({'frame':n,'head_world':[x+hp[0],y+hp[1]],'uniform_scale':scale,'outside':bad,'components':[len(g) for g in component(wld!=0)]})
 np.savez(D/'key_worlds.npz',**{str(n):w for n,w in worlds.items()});(D/'fit_registration.json').write_text(json.dumps(regs,indent=2));review(worlds,D/'fit_review.png');print(json.dumps(regs))

if __name__=='__main__':main()
