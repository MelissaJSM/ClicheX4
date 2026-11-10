"""벽 55/57/59의 귀·머리만 수용 대기 크기로 맞출 편집 입력을 만든다."""
from pathlib import Path
import sys
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
import numpy as np
from PIL import Image,ImageDraw
from scripts.c01_audio_build import read_disc
from scripts.export_x_consistency import Archive,page
from native_pose_pack import SOURCE,SOURCE_SHA,need,write,sha
from src.psx_disc import file_hash

def main():
 need(file_hash(SOURCE)==SOURCE_SHA,'Source changed')
 a=Archive(read_disc(SOURCE,('PL00_U.ARC',))[0]['PL00_U.ARC']);out=H/'wall_head_edit01';need(not out.exists(),'Output already exists');out.mkdir()
 board=Image.new('RGBA',(1536,1024));guide=Image.new('RGBA',(1536,1024));d=ImageDraw.Draw(guide)
 rows=[]
 for r,(name,mask,start)in enumerate((('base',0,0),('fourth',15,16))):
  for c,n in enumerate((55,57,59)):
   path=H/'wall_contact_native03'/f'{name}_{n:03}_indices.png';v=np.array(Image.open(path));im=a.rgba(v,start)
   cell=im.crop((128,120,192,184)).resize((512,512),Image.Resampling.NEAREST);board.alpha_composite(cell,(c*512,r*512));guide.alpha_composite(cell,(c*512,r*512))
   # Target envelope for the main cranial/ear mass, not a clip rectangle.
   # Long hair behind the neck may descend, but should use broad smooth strands.
   x0=c*512+(32-14)*8;y0=r*512+(40-24)*8;x1=c*512+(32+9)*8;y1=r*512+(40-4)*8
   d.rectangle((x0,y0,x1,y1),outline=(0,255,128,220),width=3)
   rows.append({'form':name,'ref':n,'source_indices_sha256':sha(path.read_bytes()),'desired_main_head_world_envelope':[-14,-24,9,-4],'source_scale_to_preview':8,'body_or_feet_resize_allowed':False})
 board.save(out/'new_poses.png');guide.save(out/'head_envelope_guide.png')
 idle=Image.new('RGBA',(1024,512))
 for c,mask in enumerate((0,15)):idle.alpha_composite(a.composite(0,mask)[0].crop((128,120,192,184)).resize((512,512),Image.Resampling.NEAREST),(c*512,0))
 idle.save(out/'accepted_idle.png')
 write(out/'manifest.json',{'source_bin_sha256':SOURCE_SHA,'purpose':'새 벽 원화의 머리/귀 폭과 뒷머리 흐름만 교정한다. 기존 몸/팔/발은 새 원화 그대로 보존한다.','records':rows,'native_idle_head_top_y':-24,'native_idle_head_max_width_ear_and_ornament':23,'head_not_whole_body_resize':True,'old_game_head_not_copied':True,'generation_pending':True})
 print(out)

if __name__=='__main__':main()
