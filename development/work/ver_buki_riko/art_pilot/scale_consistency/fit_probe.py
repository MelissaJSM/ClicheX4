from pathlib import Path
import sys,json,struct,math
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT))
import numpy as np
from PIL import Image,ImageDraw,ImageFont
from scripts.repack_zero import read_inputs
from scripts.build_riko_idle import patch_frames
from scripts.extract_zero import save_image
from src.psx_player import graphics_bank,composition_frame,decode_stream
from src.psx_frame_edit import frame_coverage,read_indexed_png
P=Path(__file__).parent
source=ROOT/'work/ver_buki_riko/zero_extract/20261023T062408235550Z'
_,_,arc,gmeta,gfx,parts,_=read_inputs(source)
master=ROOT/'out/ver_buki_riko/riko_motion_20261023T143602957663Z/idle_147.png'
pal=(ROOT/'out/ver_buki_riko/riko_pilot_20261023T082720987715Z/candidate_palette.bin').read_bytes();words=struct.unpack('<16H',pal)
colors=np.array([[(w&31)*255//31,((w>>5)&31)*255//31,((w>>10)&31)*255//31] for w in words[1:]],dtype=np.int32)
bank=graphics_bank(gfx,0);geometry={}
for n in (3,4,*range(21,35),*range(7,21)):
 f=bank['frames'][n];c=composition_frame(parts,0,n);raw=decode_stream(gfx,f['offset'],f['limit'],f['tile_count']*128).data;coverage,size,bounds=frame_coverage(raw,f['tile_count'],c);safe=np.array([len(v)==1 for v in coverage]).reshape(size[1],size[0])
 if any(p['flags'] for p in c['parts']) or any(len(v)>1 for v in coverage):raise ValueError('Unsupported geometry')
 for p in c['parts']:
  if p['tile']%16==0:safe[p['y']-bounds[1]:p['y']-bounds[1]+16,p['x']-bounds[0]]=False
 world=np.zeros((128,128),dtype=bool);world[64+bounds[1]:64+bounds[3],64+bounds[0]:64+bounds[2]]=safe;geometry[n]=(size,bounds,world)
run_slots=[(7,),(8,9),(10,),(11,),(12,),(13,),(14,),(15,16),(17,),(18,),(19,),(20,),(4,)]
jump_slots=[(3,),(21,),(22,23),(24,),(25,26),(27,28,29,30,31,32),(33,),(34,)]
frames={n:read_indexed_png(master,words) for n in (5,6)};pictures={};records={};failures=[]
font=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',16)
for kind,slots,scale in [('run',run_slots,.14),('jump',jump_slots,.115)]:
 for j,ns in enumerate(slots):
  source_key=0 if kind=='run' and j==12 else j
  im=Image.open(P/f'{kind}_source_{source_key:02d}.png').convert('RGBA');a=np.array(im);h,w=math.ceil(im.height*scale),math.ceil(im.width*scale);common=np.logical_and.reduce([geometry[n][2] for n in ns]);choices=[]
  for phase in (.5,.25,.75,.125,.875):
   xs=np.minimum(((np.arange(w)+phase)/scale).astype(int),im.width-1);ys=np.minimum(((np.arange(h)+phase)/scale).astype(int),im.height-1);pixels=a[ys[:,None],xs[None,:]];mask=pixels[:,:,3]>=128;rgb=pixels[:,:,:3].astype(np.int32);ix=np.zeros((h,w),dtype=np.uint8);ix[mask]=np.argmin(((rgb[mask,None]-colors[None])**2).sum(2),1)+1
   eyes=(ix==5)&(rgb[:,:,0]>rgb[:,:,1]+20)&(rgb[:,:,2]>rgb[:,:,0]+10)&(np.indices(ix.shape)[0]<h*.48)
   ey,ex=np.nonzero(eyes)
   if not len(ex):continue
   first=ey.min();use=ey<=first+1;ex=ex[use];ey=ey[use]
   target=-2 if ns in ((3,),(4,)) else -6 if kind=='run' else -4
   ideal_x=round(target-float(ex.mean()));ideal_y=24-h
   for x in range(ideal_x-8,ideal_x+9):
    for y in (range(ideal_y-1,ideal_y+2) if kind=='run' else range(ideal_y-10,ideal_y+5)):
     if x < -64 or y < -64 or x+w>64 or y+h>64:continue
     bad=int(np.sum(mask&~common[64+y:64+y+h,64+x:64+x+w]));cost=bad*100+abs(x-ideal_x)+abs(y-ideal_y)*2+abs(phase-.5)
     choices.append((cost,bad,x,y,phase,ix,ex.mean(),ey.mean()))
  if not choices:raise ValueError(f'No purple eye {kind}{j}')
  _,bad,x,y,phase,ix,ex,ey=min(choices,key=lambda q:q[0]);rec={'kind':kind,'key':j,'slots':ns,'scale':scale,'size':[w,h],'world_origin':[x,y],'phase':phase,'outside':bad,'eye_world':[float(x+ex),float(y+ey)]};records[f'{kind}{j}']=rec
  if bad:
   rec['bad_world_pixels']=[[int(xx+x),int(yy+y)] for yy,xx in np.argwhere((ix!=0)&~common[64+y:64+y+h,64+x:64+x+w])];failures.append(rec)
  world=np.zeros((128,128),dtype=np.uint8);world[64+y:64+y+h,64+x:64+x+w]=ix;pictures[ns[0]]=world
  for n in ns:
   size,b,_=geometry[n];canvas=world[64+b[1]:64+b[3],64+b[0]:64+b[2]];frames[n]=(canvas.tobytes(),size);save_image(*frames[n],words,P/f'probe_frame_{n:03d}.png')
  save_image(ix.tobytes(),(w,h),words,P/f'probe_{kind}_{j:02d}.png')
print('FAILURES',json.dumps(failures));print('GEOMETRY',json.dumps(records))
(P/'fit_probe.json').write_text(json.dumps(records,indent=2),encoding='utf-8')
if not failures:
 try:
  _,checks=patch_frames(arc,gmeta,gfx,parts,frames,pal);print('COMPRESSION',json.dumps(checks['compression']))
 except Exception as e:print('PREFLIGHT_FAILURE',str(e))
board=Image.new('RGBA',(6*256,4*320),(42,45,54,255));draw=ImageDraw.Draw(board)
for k,(n,world) in enumerate([(147,None),*pictures.items()]):
 tile=Image.new('RGBA',(64,72))
 if n==147:tile.alpha_composite(Image.open(master).convert('RGBA'),(8,16))
 else:
  indices=world[24:96,32:96];mask=indices!=0;a=np.zeros((72,64,4),dtype=np.uint8);a[mask,:3]=colors[indices[mask]-1];a[mask,3]=255;tile=Image.fromarray(a)
 x=k%6*256;y=k//6*320;board.alpha_composite(tile.resize((256,288),Image.Resampling.NEAREST),(x,y+32));draw.text((x+5,y+5),str(n),font=font,fill='white');draw.line((x,y+288,x+255,y+288),fill=(95,95,100))
board.save(P/'fit_probe_board.png')
