"""새 정면 양폼의 공통 얼굴과 실제 추가된 포스 겉자락만 정합하는 후보."""
from pathlib import Path
import sys,json
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
import numpy as np
from PIL import Image,ImageDraw
from scripts.c01_audio_build import read_disc
from scripts.export_x_consistency import Archive,page
from native_pose_pack import SOURCE,SOURCE_SHA,sha,need,write
from src.psx_disc import file_hash

def poly(points):
 im=Image.new('1',(384,384));ImageDraw.Draw(im).polygon([(x+160,y+160)for x,y in points],fill=1);return np.array(im,bool)

def main():
 need(file_hash(SOURCE)==SOURCE_SHA,'Source changed');a=Archive(read_disc(SOURCE,('PL00_U.ARC',))[0]['PL00_U.ARC']);d2=H/'front156_generation02';d3=H/'front156_generation03'
 base=np.array(Image.open(d2/'iris_probe/base_156_indices.png'));full=np.array(Image.open(d2/'native01/fourth_156_indices.png'));panel=np.array(Image.open(d3/'native01/fourth_156_indices.png'))
 yy,xx=np.indices(base.shape);head=yy<156
 ornament=((xx<=153)&(yy>=140)&(yy<155))|((xx>=168)&(yy>=137)&(yy<155))
 overlay=full.copy();overlay[head]=0
 # The newly generated bow/flower modules need one native pixel of lateral registration.
 for region,dx in((((xx<=153)&(yy>=140)&(yy<155)),-1),(((xx>=168)&(yy>=137)&(yy<155)),1)):
  sy,sx=np.nonzero(region&(full>0));overlay[sy,sx+dx]=full[sy,sx]
 # Keep the two inner seam texels from that SAME new head painting.
 for wx,wy in((-7,-17),(8,-17)):
  need(full[wy+160,wx+160]>0,'New ornament seam source missing');overlay[wy+160,wx+160]=full[wy+160,wx+160]
 # Shared hands use the NEW base's exact skin, never a resized original arm.
 hand=((xx<152)|(xx>170))&(yy>=160)&(yy<166)
 overlay[hand&np.isin(full,[9])]=0
 left=poly([(-9,7),(-5,9),(-6,17),(-10,18),(-14,13),(-13,10)])
 right=poly([(8,7),(12,9),(14,14),(11,18),(8,17),(6,10)])
 cloth=np.isin(panel,[1,2,3,10,11,14,15]);left&=cloth;right&=cloth
 # New coat panel matching: whole left cloth module moved inward one pixel.
 patches=[]
 for name,mask,dx in(('left',left,1),('right',right,0)):
  sy,sx=np.nonzero(mask);overlay[sy,sx+dx]=panel[sy,sx];patches.append({'name':name,'source':'front156_generation03/native01/fourth_156_indices.png','translation':[dx,0],'pixels':int(mask.sum())})
 target=a.rgba(base);target.alpha_composite(a.rgba(overlay,16));outside=(base>0)&(overlay==0)&~head&~hand
 out=H/'front156_aligned02';out.mkdir(exist_ok=False);Image.fromarray(base).save(out/'base_indices.png');Image.fromarray(overlay).save(out/'fourth_overlay_indices.png');a.rgba(base).save(out/'base.png');target.save(out/'fourth.png')
 page([('base current156',a.composite(156,0)[0]),('base new156',a.rgba(base))],a.composite(0,0)[0],out/'base_comparison.png',cols=2,scale=6)
 page([('Fourth current156',a.composite(156,15)[0]),('Fourth new156',target)],a.composite(0,15)[0],out/'fourth_comparison.png',cols=2,scale=6)
 marked=np.array(target);bad=outside&np.isin(base,[1,4,10,11]);headred=(overlay==0)&np.isin(base,[1,4,10,11])&(yy>=140)&(yy<156)&((xx<=153)|(xx>=167));bad|=headred;need(not bad.any(),'Red base garment still visible');marked[bad]=(255,0,0,255);page([('remaining base red garment RED',Image.fromarray(marked))],a.composite(0,15)[0],out/'uncovered_red.png',cols=1,scale=7)
 write(out/'provenance.json',{'base_source':str((d2/'iris_probe/base_156_indices.png').relative_to(ROOT)),'body_source':str((d2/'native01/fourth_156_indices.png').relative_to(ROOT)),'panel_source_sha256':sha((d3/'generated.png').read_bytes()),'new_base_head_shared_y_less_than':156,'new_base_source_iris_texels':2,'old_game_head_body_used':False,'panels':patches,'new_ornament_module_translation':{'left':[-1,0],'right':[1,0]},'inner_seam_texels_from_same_new_ornament':[[-7,-17],[8,-17]],'uncovered_body_red_texels':int(bad.sum()),'uncovered_red_world':[[int(x)-160,int(y)-160,int(base[y,x])]for y,x in zip(*np.nonzero(bad))],'candidate_not_packed':True})
 print(json.dumps({'uncovered_red':int(bad.sum()),'coordinates':[[int(x)-160,int(y)-160,int(base[y,x])]for y,x in zip(*np.nonzero(bad))],'panel_pixels':patches}))
if __name__=='__main__':main()
