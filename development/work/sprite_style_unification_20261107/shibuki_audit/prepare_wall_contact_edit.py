"""새 원화만 사용하여 팔 접점 교정 입력을 작성한다. 게임도트 변경 없음."""
from pathlib import Path
import sys,json
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
import numpy as np
from PIL import Image,ImageDraw
from scipy.ndimage import label
from scripts.c01_audio_build import read_disc
from scripts.export_x_consistency import Archive,page
from native_pose_pack import SOURCE,SOURCE_SHA,sha,need,write
from src.psx_disc import file_hash

def hand(v):
 yy,xx=np.indices(v.shape);mask=np.isin(v,[11,12,13])&(yy<145)&(xx>164);labels,count=label(mask,np.ones((3,3)));rows=[]
 for k in range(1,count+1):
  y,x=np.nonzero(labels==k);rows.append((int(y.min()),int(x.min()),int(x.max()),int(y.max()),len(x)))
 need(bool(rows),'Raised hand not found');y0,x0,x1,y1,n=sorted(rows)[0];return [x0-160,y0-160,x1+1-160,y1+1-160]

def main():
 need(file_hash(SOURCE)==SOURCE_SHA,'Source changed');a=Archive(read_disc(SOURCE,('PL00_U.ARC',))[0]['PL00_U.ARC']);src=H/'wall_detail_inputs01';native=H/'wall_detail_native01';out=H/'wall_contact_edit01';need(not out.exists(),'Output exists');out.mkdir()
 image=Image.open(src/'generated_page02.png').convert('RGBA');board=Image.new('RGBA',image.size,(0,0,0,0));targets=[]
 for col,(n,dx)in enumerate(((61,2),(63,5),(65,2))):
  bb=hand(a.layer(n)[0]);newbb=hand(np.array(Image.open(native/f'base_{n:03}_indices.png')));target={'ref':n,'whole_new_art_translation':[dx,0],'old_palm_box_world':bb,'new_palm_box_before_translation':newbb,'remaining_hand_alignment':[bb[2]-newbb[2]-dx,bb[1]-newbb[1]],'pose_source':'new generated page02, no original game pixels pasted'};targets.append(target)
  for row in range(2):
   crop=image.crop((col*512,row*512,(col+1)*512,(row+1)*512));cell=Image.new('RGBA',(512,512),(0,0,0,0));cell.alpha_composite(crop,(dx*8,0));board.alpha_composite(cell,(col*512,row*512))
 board.save(out/'new_art_translated.png');guide=board.copy();dr=ImageDraw.Draw(guide)
 for col,item in enumerate(targets):
  x0,y0,x1,y1=item['old_palm_box_world']
  for row in range(2):dr.rectangle((col*512+(x0+32)*8,row*512+(y0+40)*8,col*512+(x1+32)*8,row*512+(y1+40)*8),outline=(20,255,80,255),width=4)
 guide.save(out/'palm_target_guide.png');write(out/'manifest.json',{'source_generated_sha256':sha((src/'generated_page02.png').read_bytes()),'source_bin_sha256':SOURCE_SHA,'records':targets,'green_box_meaning':'Only the raised skin palm from the existing accepted wall sprite. New fingers should reach these exact native locations after 1/8 registration. Green guides must not appear in final artwork.','new_source_head_and_body_preservation':True,'no_anisotropic_resize_or_stretched_sleeve':True,'no_art_generation_yet':True})
 print(json.dumps(targets))

if __name__=='__main__':main()
