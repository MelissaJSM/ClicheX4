"""Normalize generated ladder keys at one scale, preserving shared base tile grids."""
from pathlib import Path
import sys,json,math,struct
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT))
from work.ver_buki_riko.art_pilot.ground_slash_v2.fit_ground import colors,front,component,rgba
from scripts.repack_zero import read_inputs
from scripts.extract_zero import save_image
from src.psx_player import graphics_bank,composition_frame,decode_stream,compose_indices
from src.psx_frame_edit import frame_coverage
D=Path(__file__).parent
profile,_,arc,gmeta,gfx,parts,zero_pal=read_inputs(ROOT/'work/ver_buki_riko/zero_extract/20261023T062408235550Z')
pal=struct.unpack('<16H',(ROOT/'out/ver_buki_riko/riko_pilot_20261023T082720987715Z/candidate_palette.bin').read_bytes())
bank=graphics_bank(gfx,0)
KEYS=[174,178,182,186,190,192,193,194,195,197,199,202]
BASE_COUNTS={**dict.fromkeys(range(174,178),8),**dict.fromkeys(range(178,182),9),**dict.fromkeys(range(182,186),10),**dict.fromkeys(range(186,190),8)}

def geometry(n,base_only=False):
 f=bank['frames'][n];c=composition_frame(parts,0,n);raw=decode_stream(gfx,f['offset'],f['limit'],f['tile_count']*128).data
 if base_only and n in BASE_COUNTS:c={**c,'parts':c['parts'][:BASE_COUNTS[n]]}
 cov,size,b=frame_coverage(raw,f['tile_count'],c);safe=np.array([bool(v) for v in cov]).reshape(size[1],size[0])
 for p in c['parts']:
  if p['tile']%16==0:safe[p['y']-b[1]:p['y']-b[1]+16,p['x']-b[0]+(15 if p['flip_x'] else 0)]=False
 w=np.zeros((192,192),bool);w[96+b[1]:96+b[3],96+b[0]:96+b[2]]=safe
 return size,b,w

def sample(cell,scale):
 a=np.array(cell.convert('RGBA'));groups=component(a[:,:,3]>=220);m=np.zeros(a.shape[:2],bool)
 for y,x in groups[0]:m[y,x]=True
 a[~m,3]=0;y,x=np.nonzero(m);a=a[y.min():y.max()+1,x.min():x.max()+1]
 h,w=[math.ceil(v*scale) for v in a.shape[:2]];ys=np.minimum(((np.arange(h)+.5)/scale).astype(int),a.shape[0]-1);xs=np.minimum(((np.arange(w)+.5)/scale).astype(int),a.shape[1]-1);a=a[ys[:,None],xs[None,:]]
 m=a[:,:,3]>=220;ix=np.zeros((h,w),np.uint8);ix[m]=np.argmin(((a[m,:3].astype(int)[:,None]-colors[None,1:])**2).sum(2),1)+1
 return ix

def normalize(a,head):
 gy,gx=np.nonzero(np.isin(a,[4,8,14]));hy,hx=np.nonzero(np.isin(head,[4,8,14]))
 px=round(float(gx.mean()-hx.mean()));py=int(gy.min()-hy.min())
 out=np.zeros((128,128),np.uint8);out[32:32+a.shape[0],32:32+a.shape[1]]=a;px+=32;py+=32
 # Remove generated head foreground, retain raised arms outside it.
 out[np.isin(out,[4,8,14])]=0
 mask=head!=0;patch=out[py:py+19,px:px+23];patch[mask]=head[mask]
 yy,xx=np.nonzero(out);x0,y0=int(xx.min()),int(yy.min());return out[y0:yy.max()+1,x0:xx.max()+1],[px-x0,py-y0]

def review(worlds,path):
 board=Image.new('RGBA',(8*240,math.ceil(len(worlds)/8)*288),(32,36,48));draw=ImageDraw.Draw(board)
 for i,(n,w) in enumerate(worlds.items()):
  pic=rgba(w[48:138,56:136]).resize((240,270),Image.Resampling.NEAREST);board.alpha_composite(pic,(i%8*240,i//8*288+18));draw.text((i%8*240+4,i//8*288+2),str(n),fill='white')
 board.save(path)

def main():
 im=Image.open(D/'generated_ladder.png');scale=float(sys.argv[1]) if len(sys.argv)>1 else .19
 samples={}
 for i,n in enumerate(KEYS):
  box=(round(i%4*im.width/4),round(i//4*im.height/3),round((i%4+1)*im.width/4),round((i//4+1)*im.height/3))
  samples[n]=sample(im.crop(box),scale)
 a=samples[178];gy,gx=np.nonzero(np.isin(a,[4,8,14]));cx=round((gx.min()+gx.max())/2);cy=int(gy.min())-2
 rear=np.zeros((19,23),np.uint8);part=a[max(cy,0):cy+19,max(cx-11,0):cx+12];rear[max(-cy,0):max(-cy,0)+part.shape[0],max(11-cx,0):max(11-cx,0)+part.shape[1]]=part
 save_image(rear.tobytes(),(23,19),pal,D/'rear_head_indexed.png');save_image(np.fliplr(rear).tobytes(),(23,19),pal,D/'rear_head_mirrored_indexed.png')
 worlds={};regs=[]
 for n,a in samples.items():
  head=rear if n in (174,178,182,186,190) else front
  a,hp=normalize(a,head);h,w=a.shape;safe=geometry(n,True)[2]
  hx,hy=(-11,-24) if n<190 else (-12,-24) if n==190 else (-13,-20) if n in (192,193) else (-12,-25) if n==194 else (-14,-23)
  x,y=hx-hp[0],hy-hp[1];options=[]
  for dx in range(-8,9):
   for dy in range(-4,5):
    tx,ty=x+dx,y+dy;bad=int(np.count_nonzero((a!=0)&~safe[96+ty:96+ty+h,96+tx:96+tx+w]));options.append((bad*1000+abs(dx)*3+abs(dy)*4,bad,tx,ty))
  _,bad,x,y=min(options);wld=np.zeros((192,192),np.uint8);wld[96+y:96+y+h,96+x:96+x+w]=a;worlds[n]=wld
  regs.append({'frame':n,'head_world':[x+hp[0],y+hp[1]],'head_view':'ladder_rear' if n in (174,178,182,186,190) else 'approved_front','scale':scale,'outside':bad,'components':[len(g) for g in component(wld!=0)]})
 np.savez(D/'key_worlds.npz',**{str(n):w for n,w in worlds.items()});(D/'fit_registration.json').write_text(json.dumps(regs,indent=2));review(worlds,D/'fit_review.png');print(json.dumps(regs))

if __name__=='__main__':main()
