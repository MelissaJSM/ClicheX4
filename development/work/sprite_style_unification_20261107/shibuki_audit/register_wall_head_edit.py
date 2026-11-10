"""머리 교정 원화만 고정 축척으로 등록하고 기존 새 몸/팔/발을 보존한다."""
from pathlib import Path
import sys,struct
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
import numpy as np
from PIL import Image
from scripts.c01_audio_build import read_disc
from scripts.export_x_consistency import Archive,page
from scripts.prepare_shibuki_run_cycle import quantize
from native_pose_pack import SOURCE,SOURCE_SHA,sha,need,write
from src.psx_disc import file_hash

def head_region(n,base,new,label):
 yy,xx=np.indices(base.shape);x=xx-160;y=yy-160
 upper=(x>=-18)&(x<14)&(y>=-30)&(y<=-5)
 # Guard the existing newly drawn left palm/forearm and raised wall-contact arm.
 upper&=~((x<-10)&(y>=-7))
 if n==59:upper&=~((x>=9)&(y<=-12))
 # The rear hair goes behind the sleeves. Select only lavender hair colors in
 # that small zone; never overwrite white/black clothing or skin to reshape it.
 hair=[2,5,8,14,15]if label=='base'else[2,3,4,5,6]
 tail=(x>=10)&(x<=19)&(y>=-6)&(y<=7)&(np.isin(base,hair)|np.isin(new,hair))
 return upper|tail

def main():
 need(file_hash(SOURCE)==SOURCE_SHA,'Source changed');a=Archive(read_disc(SOURCE,('PL00_U.ARC',))[0]['PL00_U.ARC'])
 src=H/'wall_head_edit01/generated.png';need(sha(src.read_bytes())=='780bab7118ad8b79a869ba70d8850c58796cf0ff9e35e82e33e01d111908e11f','Generated head source changed')
 im=Image.open(src).convert('RGBA');need(im.size==(1536,1024),'Wrong dimensions');out=H/'wall_head_edit01/native01';need(not out.exists(),'Output exists');out.mkdir()
 rows=[]
 for r,(name,mask,start)in enumerate((('base',0,0),('fourth',15,16))):
  words=struct.unpack_from('<16H',a.p,start*2);rgb=np.array([[(w>>s&31)*255//31 for s in(0,5,10)]for w in words],np.int32);items=[]
  for c,n in enumerate((55,57,59)):
   old=np.array(Image.open(H/'wall_contact_native03'/f'{name}_{n:03}_indices.png'));v=quantize(im.crop((c*512,r*512,(c+1)*512,(r+1)*512)),(64,64),rgb,128);new=np.zeros_like(old);new[120:184,128:192]=v
   region=head_region(n,old,new,name);target=old.copy();target[region]=new[region]
   Image.fromarray(target).save(out/f'{name}_{n:03}_indices.png');Image.fromarray(new).save(out/f'{name}_{n:03}_raw_indices.png');Image.fromarray(region.astype(np.uint8)*255).save(out/f'{name}_{n:03}_head_mask.png');pic=a.rgba(target,start);pic.save(out/f'{name}_{n:03}.png')
   items.extend([(f'{name} original new {n}',a.rgba(old,start)),(f'{name} corrected head {n}',pic)])
   yy,xx=np.indices(old.shape);mass=target*(yy<=155)*(xx<170);sy,sx=np.nonzero(mass)
   row={'ref':n,'form':name,'fixed_scale':.125,'main_head_y_min':int(sy.min())-160,'main_head_x_min':int(sx.min())-160,'main_head_x_max':int(sx.max())-160,'changed_pixels':int(np.count_nonzero(old!=target)),'non_head_exact':bool(np.array_equal(old[~region],target[~region])),'discarded_generated_nonhead_changes':int(np.count_nonzero(old[~region]!=new[~region])),'old_game_head_pasted':False,'art_not_packed':True}
   rows.append(row)
  page(items,a.composite(0,mask)[0],out/f'{name}_comparison.png',cols=2,scale=5)
 write(out/'registration.json',{'source_sha256':sha(src.read_bytes()),'body_source':'wall_contact_native03','head_region_only':True,'records':rows,'native_visual_validation_pending':True,'runtime_verified':False})
 print(rows)

if __name__=='__main__':main()
