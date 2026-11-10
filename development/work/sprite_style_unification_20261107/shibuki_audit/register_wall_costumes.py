"""새 벽 두 의상을 파츠 소유와 손 접점 기준으로 정합하는 후보.

겹침 바깥의 새 기본 원화 가장자리만 기존 포스 재질색으로 등록한다.
포스 내부의 원화 디테일을 일괄 재색상하지 않는다. 아직 ARC를 쓰지 않는다.
"""
from pathlib import Path
import sys
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
import numpy as np
from PIL import Image,ImageDraw
from scripts.c01_audio_build import read_disc
from scripts.export_x_consistency import Archive,page
from native_pose_pack import SOURCE,SOURCE_SHA,need,write,sha
from src.psx_disc import file_hash

def arrays(n):
 root=H/('wall_head_edit01/native01'if n<61 else'wall_head_edit02/native01')
 return tuple(np.array(Image.open(root/f'{name}_{n:03}_indices.png'))for name in('base','fourth'))

def polygon(points):
 im=Image.new('1',(384,384));ImageDraw.Draw(im).polygon([(x+160,y+160)for x,y in points],fill=1);return np.array(im,bool)

def ownership(n):
 yy,xx=np.indices((384,384));x=xx-160;y=yy-160;owner=np.full((384,384),6,np.uint8)
 owner[y<=-5]=5
 # Hair tails belong to head, cape tails belong to the torso.
 owner[(x>=10)&(y>=-6)&(y<=6)]=5
 # Bent thigh/lower legs use the same joint envelope in both costumes.
 leg=polygon([(-15,3),(-4,2),(3,9),(7,17),(7,23),(-7,23),(-10,12),(-15,10)])
 owner[leg]=8
 arm_dx={55:0,57:0,59:0,61:4,63:6,65:4}[n]
 left=polygon([(px+arm_dx,py)for px,py in[(-20,-8),(-11,-9),(-5,-4),(-5,2),(-10,8),(-18,8)]])
 owner[left]=7
 if n==55:right=polygon([(3,-6),(10,-7),(14,-2),(16,7),(9,9),(5,3)])
 elif n==57:right=polygon([(3,-4),(10,-5),(15,0),(15,7),(7,7),(4,3)])
 elif n==59:right=polygon([(10,-29),(24,-29),(24,-10),(12,-4),(6,-3),(8,-10)])
 else:right=polygon([(13,-31),(24,-31),(24,-10),(13,-3),(6,-5),(9,-12),(13,-14)])
 owner[right]=7
 if n>=61:
  # Reuse the actual editing ownership boundary, not a rectangular ornament
  # approximation: that old approximation assigned sleeve pixels to Head.
  head_region=np.array(Image.open(H/'wall_head_edit02/native01'/f'base_{n:03}_head_mask.png'))>0
  raised=(x>=6)&(y>=-31)&(y<=-5)
  owner[raised&~head_region]=7
  owner[raised&head_region]=5
 return owner

def make_targets(a,n):
 base,raw=arrays(n);full=raw.copy();owner=ownership(n)
 outside=(base>0)&(full==0);rgb=np.array([[(w>>s&31)*255//31 for s in(0,5,10)]for w in a.words[:32]],np.int32)
 nearest={i:int(np.argmin(np.sum((rgb[17:32]-rgb[i])**2,axis=1)))+1 for i in range(1,16)}
 # Only source-alpha slivers, selected by owner/material. No global brightening.
 garment={1:2,4:11,10:10,11:11,12:9,13:9,15:1}
 marks=[]
 for y,x in zip(*np.nonzero(outside)):
  src=int(base[y,x]);part=int(owner[y,x]);dst=nearest[src]
  if part!=5 and src in garment:dst=garment[src]
  elif part==5 and src in(1,4,10,11):dst={1:2,4:11,10:10,11:11}[src]
  full[y,x]=dst;marks.append([int(x)-160,int(y)-160,src,dst,part])
 # New-base palms are the authoritative shared body joint. The skin raster is
 # identical when the outfit changes; cuff and sleeve remain the Fourth art.
 yy,xx=np.indices(base.shape);x=xx-160;y=yy-160
 if n==59:palm=(x>=12)&(x<=18)&(y<=-18)&(y>=-26)
 elif n==61:palm=(x>=12)&(x<=19)&(y<=-22)&(y>=-29)
 elif n==63:palm=(x>=13)&(x<=20)&(y<=-20)&(y>=-28)
 elif n==65:palm=(x>=12)&(x<=19)&(y<=-20)&(y>=-28)
 else:palm=np.zeros_like(base,bool)
 # Removing that overlay exposes the exact new base palm; no sprite erasure.
 full[palm]=0
 layers={0:base}
 for b in(5,6,7,8):layers[b]=np.where(owner==b,full,0).astype(np.uint8)
 want=a.rgba(base)
 for b in(8,5,7,6):want.alpha_composite(a.rgba(layers[b],16))
 return layers,want,owner,{'ref':n,'outside_source_alpha_pixels':int(outside.sum()),'edge_material_mapping_world_xy_from_to_owner':marks,'common_new_palm_pixels':int(np.count_nonzero(base[palm])),'all_raw_fourth_pixels_except_shared_new_palm_preserved':bool(np.array_equal(full[(raw>0)&~palm],raw[(raw>0)&~palm])),'uncovered_base_pixels_except_shared_new_palm':int(np.count_nonzero((base>0)&(full==0)&~palm))}

def main():
 need(file_hash(SOURCE)==SOURCE_SHA,'Source changed');a=Archive(read_disc(SOURCE,('PL00_U.ARC',))[0]['PL00_U.ARC']);out=H/'wall_costumes04';need(not out.exists(),'Output exists');out.mkdir();rows=[];items=[]
 for n in range(55,67,2):
  layers,want,owner,proof=make_targets(a,n);rows.append(proof)
  for b,v in layers.items():Image.fromarray(v).save(out/f'{n:03}_bank{b}_indices.png')
  Image.fromarray(owner).save(out/f'{n:03}_ownership.png');want.save(out/f'{n:03}_fourth.png');a.rgba(layers[0]).save(out/f'{n:03}_base.png')
  items.extend([(f'{n} raw new Fourth',a.rgba(arrays(n)[1],16)),(f'{n} aligned new Fourth',want)])
 page(items,a.composite(0,15)[0],out/'fourth_comparison.png',cols=2,scale=4)
 write(out/'registration.json',{'source_bin_sha256':SOURCE_SHA,'rows':rows,'all_old_game_art_excluded':True,'only_new_edge_texels_mapped_to_target_material_palette':True,'candidate_not_packed':True,'visual_review_pending':True})
 print([(r['ref'],r['outside_source_alpha_pixels'],r['uncovered_base_pixels_except_shared_new_palm'])for r in rows])

if __name__=='__main__':main()
