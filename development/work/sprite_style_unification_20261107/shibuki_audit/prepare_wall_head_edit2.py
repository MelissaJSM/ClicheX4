"""벽 후반 3키의 머리 교정 입력. 몸/손/발은 고정한다."""
from pathlib import Path
import sys
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
import numpy as np
from PIL import Image,ImageDraw
from scripts.c01_audio_build import read_disc
from scripts.export_x_consistency import Archive
from native_pose_pack import SOURCE,need,write,sha

a=Archive(read_disc(SOURCE,('PL00_U.ARC',))[0]['PL00_U.ARC']);out=H/'wall_head_edit02';need(not out.exists(),'Output exists');out.mkdir()
board=Image.new('RGBA',(1536,1024));guide=Image.new('RGBA',(1536,1024));d=ImageDraw.Draw(guide);rows=[]
for r,(name,start)in enumerate((('base',0),('fourth',16))):
 for c,n in enumerate((61,63,65)):
  path=H/'wall_contact_native03'/f'{name}_{n:03}_indices.png';v=np.array(Image.open(path));im=a.rgba(v,start);cell=im.crop((128,120,192,184)).resize((512,512),Image.Resampling.NEAREST);board.alpha_composite(cell,(c*512,r*512));guide.alpha_composite(cell,(c*512,r*512))
  eye={61:(-2,-9),63:(0,-8),65:(-2,-8)}[n];envelope=[eye[0]-8,eye[1]-15,eye[0]+15,eye[1]+5]
  d.rectangle((c*512+(envelope[0]+32)*8,r*512+(envelope[1]+40)*8,c*512+(envelope[2]+32)*8,r*512+(envelope[3]+40)*8),outline=(0,255,128,220),width=3)
  rows.append({'form':name,'ref':n,'source_sha256':sha(path.read_bytes()),'eye_anchor_world':list(eye),'main_head_envelope':envelope,'body_palm_feet_pixel_guard':True})
board.save(out/'new_poses.png');guide.save(out/'head_envelope_guide.png')
reference=Image.new('RGBA',(1024,512))
for c,(name,mask)in enumerate((('base',0),('fourth',15))):
 im=Image.open(H/'wall_head_edit01/native01'/f'{name}_057.png');reference.alpha_composite(im.crop((128,120,192,184)).resize((512,512),Image.Resampling.NEAREST),(c*512,0))
reference.save(out/'refined_head_style.png');write(out/'manifest.json',{'purpose':'55/57/59에서 정리한 크기와 긴 머리 갈래를 61/63/65에도 통일','records':rows,'generation_pending':True})
print(out)
