"""Read-only native coordinate review for authored follow-up pages."""
from pathlib import Path
import sys,json,struct,hashlib
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from scripts.overhaul_sprites_audit import render,rgba
from scripts.prepare_riko_ui import entry
D=Path(__file__).parent/'rin_extension';O=D/'after141_contact_review';O.mkdir(exist_ok=True)
arc=(D/'prepared_ground_wall_v1/PL01_U.ARC').read_bytes();pal=struct.unpack_from('<16H',entry(arc,9))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def cell(a,label,crop=(128,128,192,192),scale=8):
 im=Image.new('RGB',((crop[2]-crop[0])*scale+32,(crop[3]-crop[1])*scale+38),(26,33,43));im.paste(rgba(a,pal).crop(crop).resize(((crop[2]-crop[0])*scale,(crop[3]-crop[1])*scale),Image.Resampling.NEAREST),(32,28),rgba(a,pal).crop(crop).resize(((crop[2]-crop[0])*scale,(crop[3]-crop[1])*scale),Image.Resampling.NEAREST));dr=ImageDraw.Draw(im);dr.text((4,2),label,fill='white')
 for x in range(crop[0],crop[2]+1):
  if x%4==0:dr.line((32+(x-crop[0])*scale,28,32+(x-crop[0])*scale,im.height-10),fill=(70,78,87));dr.text((32+(x-crop[0])*scale,15),str(x),fill='silver')
 for y in range(crop[1],crop[3]+1):
  if y%4==0:dr.line((32,28+(y-crop[1])*scale,im.width,28+(y-crop[1])*scale),fill=(70,78,87));dr.text((2,28+(y-crop[1])*scale),str(y),fill='silver')
 return im
records=[];measures=[]
def bb(a):
 y,x=np.where(a);return [int(x.min()),int(y.min()),int(x.max()+1),int(y.max()+1)]if len(y)else None
for folder,keys in [('ground_second01',[83,85,87,89]),('ground_recovery01',[91,105,107,130]),('movement_returns01',[133,134,3,4])]:
 for n in keys:
  src=D/folder/'native'/f'b0_{n:03}_indices.png';a=render(arc,0,0,n)[0];z=np.array(Image.open(src));left=cell(a,f'{n} before');right=cell(z,f'{n} new source');out=Image.new('RGB',(left.width*2,left.height));out.paste(left,(0,0));out.paste(right,(left.width,0));out.save(O/f'{n:03}_grid.png')
  records.append({'ref':n,'source':str(src.relative_to(ROOT)),'source_sha256':sha(src),'old_bbox':rgba(a,pal).getbbox(),'new_bbox':rgba(z,pal).getbbox(),'sheet':str((O/f'{n:03}_grid.png').relative_to(ROOT))})
  stats=[]
  for v in(a,z):
   face=np.isin(v,[12,13,14]);face[154:]=False;face[:128]=False;face[:,:130]=False;face[:,175:]=False;eye=v==15;eye[154:]=False
   foot=v>0;foot[:176]=False;xx=np.indices(v.shape)[1]
   stats.append({'face':bb(face),'eyes':[[int(x),int(y)]for y,x in zip(*np.where(eye))],'foot_left':bb(foot&(xx<160)),'foot_right':bb(foot&(xx>=160))})
  measures.append({'ref':n,'old':stats[0],'new':stats[1]})
(O/'source.json').write_text(json.dumps({'candidate_review_only':True,'records':records,'game_modified':False},ensure_ascii=False,indent=2)+'\n','utf8')
(O/'measures.json').write_text(json.dumps(measures,indent=2)+'\n','utf8');print(json.dumps(measures))
