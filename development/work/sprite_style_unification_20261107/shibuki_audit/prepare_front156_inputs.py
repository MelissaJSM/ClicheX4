"""정면 귀환156의 실제 포즈와 대기 질감 기준을 별도 이미지로 준비."""
from pathlib import Path
import sys,json
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from PIL import Image
from scripts.c01_audio_build import read_disc
from scripts.export_x_consistency import Archive
from native_pose_pack import SOURCE,SOURCE_SHA,sha,need,write
from src.psx_disc import file_hash

def main():
 need(file_hash(SOURCE)==SOURCE_SHA,'Source changed');a=Archive(read_disc(SOURCE,('PL00_U.ARC',))[0]['PL00_U.ARC']);out=H/'front156_generation01';out.mkdir(exist_ok=False)
 for n,name in((156,'pose_reference'),(0,'idle_reference')):
  im=Image.new('RGBA',(1536,1024))
  for i,mask in enumerate((0,15)):
   v=a.composite(n,mask)[0].crop((112,96,208,224)).resize((768,1024),Image.Resampling.NEAREST);im.alpha_composite(v,(i*768,0))
  im.save(out/f'{name}.png')
 write(out/'inputs.json',{'source_bin_sha256':SOURCE_SHA,'source_arc_sha256':sha(a.data),'native_origin':[160,160],'native_crop':[112,96,208,224],'reference_scale':8,'sprite_height':47,'finger_tip_world':[[-17,4],[17,4]],'foot_bottom_world':22,'source_ref':156,'targets_after_master':[156,157,158],'selection_targets':[19,20,21],'original_game_art_sent':False,'source_images_are_accepted_mod_sprites':True,'not_runtime':True})
if __name__=='__main__':main()
