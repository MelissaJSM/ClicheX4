"""新 기본/포스 원화의 조립 겹침 차이를 표시만 한다. 패킹하지 않는다."""
from pathlib import Path
import sys
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
import numpy as np
from PIL import Image
from scripts.c01_audio_build import read_disc
from scripts.export_x_consistency import Archive,page
from native_pose_pack import SOURCE,write

def arrays(n):
 root=H/('wall_head_edit01/native01'if n<61 else'wall_contact_native03')
 return tuple(np.array(Image.open(root/f'{name}_{n:03}_indices.png'))for name in('base','fourth'))

a=Archive(read_disc(SOURCE,('PL00_U.ARC',))[0]['PL00_U.ARC']);out=H/'wall_overlap01';out.mkdir(exist_ok=True);items=[];rows=[]
for n in range(55,67,2):
 base,full=arrays(n);outside=(base>0)&(full==0);y,x=np.nonzero(outside);pal,count=np.unique(base[outside],return_counts=True)
 image=a.rgba(base);image.alpha_composite(a.rgba(full,16));marked=np.array(image);marked[outside]=(255,0,0,255)
 items.extend([(f'{n} full intended',a.rgba(full,16)),(f'{n} base leak RED',Image.fromarray(marked))]);rows.append({'ref':n,'outside_pixels':int(outside.sum()),'indices':dict(zip(map(int,pal),map(int,count))),'world_xy_index':[[int(X)-160,int(Y)-160,int(base[Y,X])]for Y,X in zip(y,x)]})
page(items,a.composite(0,15)[0],out/'comparison.png',cols=2,scale=5);write(out/'overlap.json',{'rows':rows,'not_a_finished_art':True})
print([(r['ref'],r['outside_pixels'],r['indices'])for r in rows])
