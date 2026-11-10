"""관절 위치별 다리 영역에만 기존 명암을 피부·짧은 샌들 재질로 대응한다."""
from pathlib import Path
import json,sys
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT));sys.path.insert(0,str(H))
import numpy as np
from scipy.ndimage import binary_erosion,distance_transform_edt
from PIL import Image
from leg_material_preview import SRC,SHA
from scripts.c01_audio_build import read_disc
from scripts.export_x_consistency import Archive,page
from src.psx_disc import file_hash
REFS=list(range(11,17))+list(range(33,85))
HEIGHTS={11:(12,18),13:(10,18),15:(11,17),33:(8,15),35:(10,16),37:(10,16),39:(7,12),41:(10,16),43:(10,14),45:(11,17),47:(11,18),
         49:(13,None),51:(15,None),53:(14,None),55:(10,15),57:(10,15),59:(10,15),61:(10,14),63:(10,14),65:(10,14),
         67:(14,None),69:(14,None),77:(14,None),79:(13,None),81:(13,None),83:(13,None)}
def material_masks(n,old,arc):
 yy,xx=np.indices(old.shape);y=yy-160;x=xx-160;ref=n if n%2 else n-1
 if ref in (71,73,75):
  # Prone dash: the leading folded foot and trailing shin have different axes.
  front=(x>=-7)&(x<0)&(y>=19)&(y<22)
  rear=(x>=(2 if ref==75 else 3))&(x<(12 if ref==75 else 15))&(y>=15)&(y<22)
  eligible=front|rear;shoe=front|(rear&(y>=19));skin=rear&~shoe
  if ref==73:
   # Ref73/74 retains overlaid dash streaks. Any pixel differing from the
   # equivalent non-streak 71/72 pose is outside material correction.
   stable=old==arc.layer(n-2)[0];eligible&=stable;skin&=stable;shoe&=stable
  region={'front_sandal':[-7,19,0,22],'rear_leg':[2 if ref==75 else 3,15,12 if ref==75 else 15,22], 'rear_ankle_y':19,'effect_difference_protected':ref==73}
 else:
  top,ankle=HEIGHTS[ref];eligible=(y>=top)&(y<=22)&(x>=-16)&(x<22)
  line=np.full(old.shape,ankle) if ankle is not None else np.where(x<0,18,19)
  if ref==69:line=np.where(x<5,19,17)
  skin=eligible&(y<line);shoe=eligible&~skin
  region={'world_box':[-16,top,22,23],'ankle_y':ankle,'standing_ankles':None if ankle is not None else([19,17] if ref==69 else[18,19])}
 # Four-connected erosion retains the exact outside boundary and all gaps.
 inner=binary_erosion(old>0);skin&=inner;shoe&=inner
 return skin,shoe,region

def targets(arc,source):
 result={};reports=[]
 for n in REFS:
  old=arc.layer(n)[0]
  # Native ref73/74 contains a streak over the rear leg. Its color is not a
  # material shadow: borrow the same pose without streaks for shading only.
  native=source.layer(n-2 if n in (73,74) else n)[0];skin,shoe,region=material_masks(n,old,arc)
  eligible=skin|shoe;orig=native.copy();missing=eligible&(orig==0)
  if np.any(missing):
   _,ids=distance_transform_edt(native==0,return_indices=True);orig[missing]=native[tuple(ids[:,missing])]
  new=old.copy();new[skin]=np.where(np.isin(orig[skin],[5,6,9,13]),13,12)
  new[shoe]=np.select([np.isin(orig[shoe],[5,6,9]),np.isin(orig[shoe],[4,10,11]),np.isin(orig[shoe],[3,8,14])],[9,11,5],default=8)
  change=new!=old;layers={0:new}
  for bank in (5,6,7,8):
   a=arc.layer(n,bank)[0];v=a.copy();m=change&(a>0);v[m]=new[m];layers[bank]=v
  result[n]=layers
  reports.append({'ref':n,'pixels':int(change.sum()),'skin_pixels':int(skin.sum()),'sandal_pixels':int(shoe.sum()),'region':region,'alpha_exact':True,'outer_contour_exact':True})
 return result,reports

def main():
 assert file_hash(SRC)==SHA
 data,_=read_disc(SRC,('PL00_U.ARC','PL02_U.ARC'));arc=Archive(data['PL02_U.ARC']);source=Archive(data['PL00_U.ARC'])
 target,report=targets(arc,source);folder=H/'leg_expanded';folder.mkdir(exist_ok=True)
 for group,refs in [('run',range(11,17)),('air',range(33,55)),('wall',range(55,67)),('dash',range(67,85))]:
  for form,mask in [('after',0),('before',15)]:
   items=[]
   for n in refs:
    if not n%2:continue
    layers=target[n];old=arc.composite(n,mask)[0];new=arc.rgba(layers[0])
    if mask:
     for bit,b in ((8,8),(1,5),(4,7),(2,6)):new.alpha_composite(arc.rgba(layers[b],32 if b==7 else 16))
    items.extend([(f'{n} old',old),(f'{n} restored',new)])
   page(items,arc.composite(0,mask)[0],folder/f'{group}_{form}.png',cols=4,scale=3)
 (folder/'recipe.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf8')
 print(json.dumps({'refs':len(report),'changed_pixels':sum(x['pixels'] for x in report)}))
if __name__=='__main__':main()
