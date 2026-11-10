from pathlib import Path
import sys,json,struct,math
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT))
from scripts.repack_zero import read_inputs
from scripts.extract_zero import save_image
from src.psx_player import graphics_bank,composition_frame,decode_stream,compose_indices
from src.psx_frame_edit import frame_coverage
from work.ver_buki_riko.art_pilot.dash_v1.fit_dash import component
D=Path(__file__).parent
profile,_,arc,gmeta,gfx,parts,_=read_inputs(ROOT/'work/ver_buki_riko/zero_extract/20261023T062408235550Z')
pal=(ROOT/'out/ver_buki_riko/riko_pilot_20261023T082720987715Z/candidate_palette.bin').read_bytes();words=struct.unpack('<16H',pal)
colors=np.array([[(w&31)*255//31,((w>>5)&31)*255//31,((w>>10)&31)*255//31] for w in words],dtype=np.int32)
front=np.array(Image.open(ROOT/'out/ver_buki_riko/riko_pilot_20261023T082720987715Z/riko_idle147_indexed.png'))[:19,12:35]
bank=graphics_bank(gfx,0);geometry={}
roles=json.loads((D/'reference_roles.json').read_text('utf8'));body_frames=roles['body_frames'];effect_frames=roles['effect_frames']
for n in range(61,135):
 f=bank['frames'][n];c=composition_frame(parts,0,n);raw=decode_stream(gfx,f['offset'],f['limit'],f['tile_count']*128).data
 coverage,size,b=frame_coverage(raw,f['tile_count'],c);safe=np.array([bool(v) for v in coverage]).reshape(size[1],size[0])
 for p in c['parts']:
  if p['tile']%16==0:safe[p['y']-b[1]:p['y']-b[1]+16,p['x']-b[0]]=False
 w=np.zeros((192,192),dtype=bool);w[96+b[1]:96+b[3],96+b[0]:96+b[2]]=safe;geometry[n]=(size,b,w)
keys=[61,62,63,65,67,82,83,85,87,89,91,105,107,109,111,130,131,133]

def rgba(a):
 r=np.zeros((*a.shape,4),dtype=np.uint8);m=a!=0;r[m,:3]=colors[a[m]];r[m,3]=255;return Image.fromarray(r)

def normalize(cell,scale):
 a=np.array(cell.convert('RGBA'));groups=component(a[:,:,3]>=220);keep=np.zeros(a.shape[:2],dtype=bool)
 for y,x in groups[0]:keep[y,x]=True
 a[~keep,3]=0;yy,xx=np.nonzero(keep);a=a[yy.min():yy.max()+1,xx.min():xx.max()+1]
 h,w=[math.ceil(v*scale) for v in a.shape[:2]];xs=np.minimum(((np.arange(w)+.5)/scale).astype(int),a.shape[1]-1);ys=np.minimum(((np.arange(h)+.5)/scale).astype(int),a.shape[0]-1);a=a[ys[:,None],xs[None,:]]
 m=a[:,:,3]>=220;rgb=a[:,:,:3].astype(np.int32);ix=np.zeros((h,w),dtype=np.uint8);ix[m]=np.argmin(((rgb[m,None]-colors[None,1:])**2).sum(2),1)+1
 green=np.isin(ix,[4,8,14]);gy,gx=np.nonzero(green)
 hg=np.isin(front,[4,8,14]);hgy,hgx=np.nonzero(hg)
 hx=round(float(gx.mean()-hgx.mean()));hy=int(gy.min())-int(hgy.min())
 canvas=np.zeros((112,112),dtype=np.uint8);canvas[24:24+h,24:24+w]=ix;hx+=24;hy+=24
 # Preserve only generated arm pixels outside the fixed head foreground.
 canvas[np.isin(canvas,[4,8,14])]=0
 patch=canvas[hy:hy+19,hx:hx+23];patch[front!=0]=front[front!=0]
 yy,xx=np.nonzero(canvas);x0,y0=int(xx.min()),int(yy.min());s=canvas[y0:yy.max()+1,x0:xx.max()+1]
 return s,[hx-x0,hy-y0]

def review(worlds,records,path):
 board=Image.new('RGBA',(6*288,math.ceil(len(worlds)/6)*252),(35,40,50,255));draw=ImageDraw.Draw(board)
 for i,(n,w) in enumerate(worlds.items()):
  board.alpha_composite(rgba(w[48:128,48:144]).resize((288,240),Image.Resampling.NEAREST),(i%6*288,i//6*252+12));draw.text((i%6*288+4,i//6*252+2),str(n),fill='white')
 board.save(path)

def main():
 scale=float(sys.argv[1]) if len(sys.argv)>1 else .205;im=Image.open(D/'generated_keyposes_v1.png');xs=[0,296,592,888,1183,1479,1774];ys=[0,334,593,887]
 repair=Image.open(D/'generated_recovery_v2.png');repairs={91:(0,0,768,530),109:(768,0,1536,530),131:(0,530,768,1024),133:(768,530,1536,1024)}
 worlds={};records=[]
 for i,n in enumerate(keys):
  source_scale=.105 if n in repairs else scale
  a,head=normalize(repair.crop(repairs[n]) if n in repairs else im.crop((xs[i%6],ys[i//6],xs[i%6+1],ys[i//6+1])),source_scale);h,w=a.shape
  hx={61:-12,62:-12,63:-15,65:-17,67:-19,82:-12,83:-16,85:-18,87:-13,89:-13,91:-12,105:-12,107:-12,109:-17,111:-24,130:-14,131:-12,133:-12}[n]
  x=hx-head[0];y=24-h;safe=geometry[n][2];options=[]
  for dx in range(-10,11):
   for dy in (0,):
    tx,ty=x+dx,y+dy;bad=int(((a!=0)&~safe[96+ty:96+ty+h,96+tx:96+tx+w]).sum())
    options.append((bad*1000+abs(dx)*2+abs(dy)*8,bad,tx,ty))
  _,bad,x,y=min(options);world=np.zeros((192,192),dtype=np.uint8);world[96+y:96+y+h,96+x:96+x+w]=a;worlds[n]=world
  records.append({'frame':n,'origin':[x,y],'head_world':[x+head[0],y+head[1]],'size':[w,h],'outside':bad,'components':[len(g) for g in component(world!=0)],'source_scale':source_scale})
 review(worlds,records,D/'fit_review.png');np.savez(D/'key_worlds.npz',**{str(n):w for n,w in worlds.items()});(D/'fit_registration.json').write_text(json.dumps(records,indent=2),encoding='utf8');print(json.dumps(records))
if __name__=='__main__':main()
