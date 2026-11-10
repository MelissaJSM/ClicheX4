from pathlib import Path
import sys,json,math
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT))
from work.ver_buki_riko.art_pilot.ground_slash_v2.fit_ground import normalize,rgba,component,front,profile,arc,gmeta,gfx,parts,pal,words,bank
from src.psx_player import composition_frame,decode_stream
from src.psx_frame_edit import frame_coverage
D=Path(__file__).parent
roles=json.loads((D/'reference_roles.json').read_text('utf8'));body=roles['body_frames'];geometry={}
for n in roles['shared_references']:
 f=bank['frames'][n];comp=composition_frame(parts,0,n);raw=decode_stream(gfx,f['offset'],f['limit'],f['tile_count']*128).data
 cov,size,b=frame_coverage(raw,f['tile_count'],comp);safe=np.array([bool(v) for v in cov]).reshape(size[1],size[0])
 for p in comp['parts']:
  if p['tile']%16==0:safe[p['y']-b[1]:p['y']-b[1]+16,p['x']-b[0]]=False
 world=np.zeros((192,192),dtype=bool);world[96+b[1]:96+b[3],96+b[0]:96+b[2]]=safe;geometry[n]=(size,b,world)
def review(worlds,path):
 board=Image.new('RGBA',(9*240,2*300),(35,40,50,255));draw=ImageDraw.Draw(board)
 for i,(n,w) in enumerate(worlds.items()):
  board.alpha_composite(rgba(w[48:140,56:136]).resize((240,276),Image.Resampling.NEAREST),(i%9*240,i//9*300+24));draw.text((i%9*240+6,i//9*300+4),str(n),fill='white')
 board.save(path)
def main():
 scales=[float(x) for x in sys.argv[1:]] or [.14,.13]
 worlds={};records=[]
 for k,name in enumerate(['generated_air_v2.png','generated_landing_v3.png']):
  im=Image.open(D/name)
  for i,n in enumerate(body[k*9:k*9+9]):
   box=(round(i%3*im.width/3),round(i//3*im.height/3),round((i%3+1)*im.width/3),round((i//3+1)*im.height/3))
   a,head=normalize(im.crop(box),scales[k]);h,w=a.shape
   x=-12-head[0];y=(-23-head[1]) if k==0 else 24-h;options=[];safe=geometry[n][2]
   for dx in range(-10,11):
    for dy in (range(-5,6) if k==0 else [0]):
     tx,ty=x+dx,y+dy;bad=int(((a!=0)&~safe[96+ty:96+ty+h,96+tx:96+tx+w]).sum())
     options.append((bad*1000+abs(dx)*2+abs(dy)*3,bad,tx,ty))
   _,bad,x,y=min(options);world=np.zeros((192,192),dtype=np.uint8);world[96+y:96+y+h,96+x:96+x+w]=a
   groups=component(world!=0)
   for group in groups[1:]:
    if len(group)<=2:
     for py,px in group:world[py,px]=0
   worlds[n]=world;records.append({'frame':n,'head_world':[x+head[0],y+head[1]],'origin':[x,y],'size':[w,h],'outside':int(np.count_nonzero((world!=0)&~safe)),'components':[len(g) for g in component(world!=0)],'source_scale':scales[k],'source_crop':box,'foot_y':int(np.nonzero(world)[0].max()-96)})
 review(worlds,D/'fit_review.png');np.savez(D/'key_worlds.npz',**{str(n):w for n,w in worlds.items()});(D/'fit_registration.json').write_text(json.dumps(records,indent=2),encoding='utf8')
 print(json.dumps(records))
if __name__=='__main__':main()
