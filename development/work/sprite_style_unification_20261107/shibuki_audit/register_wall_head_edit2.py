"""후반 3키의 새 머리만 등록하고 벽손과 새 몸의 실제 픽셀은 유지한다."""
from pathlib import Path
import sys,struct
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
import numpy as np
from PIL import Image
from scripts.c01_audio_build import read_disc
from scripts.export_x_consistency import Archive,page
from scripts.prepare_shibuki_run_cycle import quantize
from native_pose_pack import SOURCE,sha,need,write

def region(n,old,new,label):
 yy,xx=np.indices(old.shape);x=xx-160;y=yy-160
 cut={61:-8,63:-6,65:-8}[n];right={61:12,63:14,65:12}[n]
 upper=(x>=-18)&(x<right)&(y>=-30)&(y<=-5)&~((x<cut)&(y>=-7))
 hair=[2,5,8,14,15]if label=='base'else[2,3,4,5,6]
 tail=(x>=10)&(x<=21)&(y>=-6)&(y<=7)&(np.isin(old,hair)|np.isin(new,hair))
 return upper|tail

a=Archive(read_disc(SOURCE,('PL00_U.ARC',))[0]['PL00_U.ARC']);src=H/'wall_head_edit02/generated.png';im=Image.open(src).convert('RGBA');need(im.size==(1536,1024),'Wrong dimensions');out=H/'wall_head_edit02/native01';need(not out.exists(),'Output exists');out.mkdir();rows=[]
for r,(name,mask,start)in enumerate((('base',0,0),('fourth',15,16))):
 rgb=np.array([[(w>>s&31)*255//31 for s in(0,5,10)]for w in struct.unpack_from('<16H',a.p,start*2)],np.int32);items=[]
 for c,n in enumerate((61,63,65)):
  old=np.array(Image.open(H/'wall_contact_native03'/f'{name}_{n:03}_indices.png'));v=quantize(im.crop((c*512,r*512,(c+1)*512,(r+1)*512)),(64,64),rgb,128);new=np.zeros_like(old);new[120:184,128:192]=v;edit=region(n,old,new,name);target=old.copy();target[edit]=new[edit]
  Image.fromarray(target).save(out/f'{name}_{n:03}_indices.png');Image.fromarray(new).save(out/f'{name}_{n:03}_raw_indices.png');Image.fromarray(edit.astype(np.uint8)*255).save(out/f'{name}_{n:03}_head_mask.png');a.rgba(target,start).save(out/f'{name}_{n:03}.png');items.extend([(f'{name} previous {n}',a.rgba(old,start)),(f'{name} refined head {n}',a.rgba(target,start))])
  yy,xx=np.indices(target.shape);eye=(target==(7 if name=='base' else 10))&(yy>=146)&(yy<=156)&(xx>=148)&(xx<=164);ey,ex=np.nonzero(eye)
  rows.append({'ref':n,'form':name,'non_head_exact':bool(np.array_equal(target[~edit],old[~edit])),'gold_eye_pixels_world':[[int(X)-160,int(Y)-160]for Y,X in zip(ey,ex)],'changed_pixels':int(np.count_nonzero(target!=old)),'discarded_generated_non_head_changes':int(np.count_nonzero(old[~edit]!=new[~edit]))})
 page(items,a.composite(0,mask)[0],out/f'{name}_comparison.png',cols=2,scale=5)
write(out/'registration.json',{'generated_sha256':sha(src.read_bytes()),'records':rows,'fixed_scale':.125,'not_packed':True,'old_head_copy':False});print(rows)
