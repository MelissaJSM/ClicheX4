"""패킹 전에 새 12참조의16마스크/양팔 조합과 변환 원점을 확인한다."""
from pathlib import Path
import sys
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
import numpy as np
from PIL import Image
from scripts.c01_audio_build import read_disc
from scripts.export_x_consistency import Archive,page
from native_pose_pack import SOURCE,need,write,sha

def targets():
 result={}
 for n in range(55,67):
  d=H/('wall_costumes04'if n%2 else'wall_shots_registered03');result[n]={b:np.array(Image.open(d/f'{n:03}_bank{b}_indices.png'))for b in(0,5,6,7,8)}
 return result

def compose(a,layers,mask,arm):
 im=a.rgba(layers[0])
 for bit,b in((8,8),(1,5),(4,7),(2,6)):
  if mask&bit:im.alpha_composite(a.rgba(layers[b],32 if arm==2 and b==7 else 16))
 return im

def main():
 a=Archive(read_disc(SOURCE,('PL00_U.ARC',))[0]['PL00_U.ARC']);d=targets();out=H/'wall_partial_preview02';need(not out.exists(),'Output exists');out.mkdir();checks=[]
 for n,layers in d.items():
  items=[]
  for mask in range(16):
   one=compose(a,layers,mask,1);two=compose(a,layers,mask,2);need(one.tobytes()==two.tobytes(),'Shibuki arm palette equality changed');items.append((f'{n} mask{mask:X}',one));checks.append({'ref':n,'mask':mask,'arms_identical':True,'rgba_sha256':sha(one.tobytes())})
  page(items,a.composite(0,15)[0],out/f'{n:03}.png',cols=4,scale=3)
 write(out/'verification.json',{'target_refs':list(d),'mask_arm_combinations':len(checks)*2,'arms_exact':True,'records':checks,'native_unpack_test_pending':True,'visually_reviewed_refs':[]})
 print({'combinations':len(checks)*2})

if __name__=='__main__':main()
