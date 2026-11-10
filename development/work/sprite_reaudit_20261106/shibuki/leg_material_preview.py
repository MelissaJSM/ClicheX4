"""기존 원작 자세의 명암과 현재 알파를 사용한 하체 재질 복원 후보. 게임 쓰기 없음."""
from pathlib import Path
import hashlib,json,sys
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
import numpy as np
from scipy.ndimage import binary_erosion,distance_transform_edt
from PIL import Image,ImageDraw
from scripts.c01_audio_build import read_disc
from scripts.export_x_consistency import Archive,page
from src.psx_disc import file_hash
SRC=ROOT/'out/ver_buki_riko/hurt_capsule_fix_20261106_v1/shibuki_riko.bin'
SHA='8c1a2fa5b3f985be9945717d3d88776f2f4534030c42818843ec8093a3ce1a81'
REFS=list(range(79,85))

def targets(arc,source):
 yy,xx=np.indices((384,384));result={};reports=[]
 for n in REFS:
  old=arc.layer(n)[0];native=source.layer(n)[0]
  # Fixed native coordinates: this group has two legs below y13 and soles y22.
  # Keep the accepted outer one-pixel contour and every alpha pixel exactly.
  eligible=(yy>=173)&(yy<=182)&(xx>=144)&(xx<=179)&(old>0)
  inner=binary_erosion(old>0)&eligible
  # Feet are short sandals. Rear ankle bends one pixel lower in the stop pose.
  shoe_line=np.where(xx<160,178,179)
  skin=inner&(yy<shoe_line);shoe=inner&~skin
  orig=native.copy();missing=eligible&(orig==0)
  if np.any(missing):
   _,ids=distance_transform_edt(native==0,return_indices=True);orig[missing]=native[tuple(ids[:,missing])]
  new=old.copy()
  # Borrow native boot light/shadow placement, then express exposed skin using
  # the existing two skin indices. No global palette edits or new colors.
  new[skin]=np.where(np.isin(orig[skin],[5,6,9,13]),13,12)
  # Reuse original short shoe highlight/shadow; retain pink only as a small
  # toe/ribbon accent, instead of turning the whole shin into the old boot.
  new[shoe]=np.select([np.isin(orig[shoe],[5,6,9]),np.isin(orig[shoe],[4,10,11]),np.isin(orig[shoe],[3,8,14])],[9,11,5],default=8)
  change=new!=old
  # Material is shared by jacket and swimsuit. Overlay colors use the same
  # skin and shoe palette indices, but may have their own texel storage.
  layers={0:new}
  for bank in (5,6,7,8):
   a=arc.layer(n,bank)[0];v=a.copy();m=change&(a>0);v[m]=new[m];layers[bank]=v
  result[n]=layers
  reports.append({'ref':n,'pixels':int(change.sum()),'skin_pixels':int(skin.sum()),'sandal_pixels':int(shoe.sum()),
                  'world_region':[-16,13,20,23],'ankle_world_y':{'front':18,'rear':19},'alpha_exact':True,'outer_contour_exact':True})
 return result,reports

def main():
 assert file_hash(SRC)==SHA
 data,_=read_disc(SRC,('PL00_U.ARC','PL02_U.ARC'));arc=Archive(data['PL02_U.ARC']);source=Archive(data['PL00_U.ARC'])
 target,report=targets(arc,source);folder=H/'leg_candidate';folder.mkdir(exist_ok=True)
 pairs=[]
 for n,layers in target.items():
  for b,a in layers.items():np.save(folder/f'{n:03}_bank{b}.npy',a)
  for form,mask in [('after',0),('before',15)]:
   old,_=arc.composite(n,mask);new=arc.rgba(layers[0])
   if mask:
    for bit,b in ((8,8),(1,5),(4,7),(2,6)):new.alpha_composite(arc.rgba(layers[b],32 if b==7 else 16))
   old.save(folder/f'{form}_{n:03}_old.png');new.save(folder/f'{form}_{n:03}_new.png')
   diff=np.any(np.array(old)!=np.array(new),axis=2);rgba=np.zeros((384,384,4),np.uint8);rgba[diff]=[255,50,60,255];Image.fromarray(rgba).save(folder/f'{form}_{n:03}_mask.png')
   pairs += [(f'{form} {n} old',old),(f'{form} {n} NEW',new)]
 page(pairs,arc.composite(0,0)[0],folder/'comparison.png',cols=4,scale=3)
 (folder/'recipe.json').write_text(json.dumps({'parent':str(SRC.relative_to(ROOT)),'sha256':SHA,'frames':report,'status':'review_candidate_not_packed'},ensure_ascii=False,indent=2)+'\n','utf8')
 print(json.dumps(report))
if __name__=='__main__':main()
