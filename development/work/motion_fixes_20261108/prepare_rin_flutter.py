from pathlib import Path
import json,sys,struct,hashlib
import numpy as np
from PIL import Image,ImageDraw
from scipy.ndimage import label
W=Path(__file__).resolve().parent;ROOT=W.parents[1];sys.path.insert(0,str(ROOT))
from scripts.export_x_consistency import Archive
D=W/'ver_rin_nana';O=D/'rin_flutter';O.mkdir(exist_ok=True);arc=Archive((D/'PL01_U.ARC').read_bytes());old=arc.layer(46)[0];Y,X=np.indices(old.shape);x=X-160;y=Y-160
colors=np.array([[(int(w)>>s&31)*255//31 for s in(0,5,10)]for w in arc.words[1:16]],np.int32)
src=Image.open(D/'rin_dash_generated.png').convert('RGBA');targets={};reports=[]
# Only the independent trailing ribbon/hair section. The root and entire actor body stay exact.
region=(x>=3)&(x<=35)&(y>=-7)&(y<=np.where(x<7,2,10))
for i,n in enumerate((46,47,48)):
 cell=src.crop((round(i*src.width/3),0,round((i+1)*src.width/3),src.height));a=np.array(cell);a[:,:,3]=np.where(a[:,:,3]>=192,255,0);cell=Image.fromarray(a);bb=cell.getchannel('A').getbbox();cut=cell.crop(bb);scale=34/cut.height;size=(round(cut.width*scale),34);cut=cut.convert('RGBa').resize(size,Image.Resampling.LANCZOS).convert('RGBA');aa=np.array(cut)
 p=np.where(aa[:,:,3]>=128,((aa[:,:,:3].astype(np.int32)[:,:,None,:]-colors)**2).sum(3).argmin(2)+1,0).astype('uint8');registered=np.zeros_like(old);registered[150:184,136:136+p.shape[1]]=p
 choices=[]
 for dy in(-1,0,1):
  for dx in(-1,0,1):
   q=np.roll(np.roll(registered,dy,0),dx,1);new=old.copy();new[region]=q[region]
   labs,count=label(new>0,np.ones((3,3)));missing=np.count_nonzero((old>0)&(q==0)&region&(x<7));score=(count-1)*1000+missing*20+abs(dy)+abs(dx)
   choices.append((score,dx,dy,new))
 score,dx,dy,new=min(choices,key=lambda q:q[:3]);assert score<1000,'Ribbon detached';assert np.array_equal(new[~region],old[~region]);assert 25<np.count_nonzero(new!=old)<250
 targets[n]=new;Image.fromarray(new).save(O/f'{n:03}_indices.png');arc.rgba(new).save(O/f'{n:03}.png');reports.append({'frame':n,'source_cell':i,'source_bbox':bb,'scale':scale,'register_delta':[dx,dy],'changed_pixels':int(np.count_nonzero(new!=old)),'body_and_root_exact':True,'connected':True})
assert len({a.tobytes()for a in targets.values()})==3
sheet=Image.new('RGB',(4*400,340),(31,38,50));d=ImageDraw.Draw(sheet)
for i,(lab,a)in enumerate([('before 46/47/48',old)]+[(f'new {n}',a)for n,a in targets.items()]):
 im=arc.rgba(a).crop((120,132,216,196)).resize((384,256),Image.Resampling.NEAREST);sheet.paste(im,(i*400+8,45),im);d.text((i*400+10,12),lab,fill='white')
sheet.save(O/'review.png');frames=[]
for a in targets.values():
 im=Image.new('RGB',(384,256),(31,38,50));pic=arc.rgba(a).crop((120,132,216,196)).resize((384,256),Image.Resampling.NEAREST);im.paste(pic,(0,0),pic);frames.append(im)
frames[0].save(O/'preview.gif',save_all=True,append_images=frames[1:],duration=50,loop=0)
(O/'targets.json').write_text(json.dumps({'source_arc_sha256':hashlib.sha256(arc.data).hexdigest(),'source_art':'rin_dash_generated.png','prompt':'rin_dash_prompt.txt','tool':'built-in image_gen','frames':reports,'animation_table_unchanged':True,'gif_preview_duration_ms':50},indent=2)+'\n','utf8');print(json.dumps(reports))
