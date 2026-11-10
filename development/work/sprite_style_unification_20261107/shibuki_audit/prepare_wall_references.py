"""벽 도트 통일 다음 묶음의 실제 입력/보호접점을 읽기 전용으로 준비한다."""
from pathlib import Path
import sys,json
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
import numpy as np
from PIL import Image,ImageDraw
from scripts.c01_audio_build import read_disc
from scripts.export_x_consistency import Archive,page
from native_pose_pack import SOURCE,SOURCE_SHA,sha,need,write
from src.psx_disc import file_hash

def bbox(v):
 y,x=np.nonzero(v);return [int(x.min())-160,int(y.min())-160,int(x.max())+1-160,int(y.max())+1-160]

def main():
 need(file_hash(SOURCE)==SOURCE_SHA,'Source changed');out=H/'wall_detail_inputs01';need(not out.exists(),'Reference folder exists');out.mkdir()
 baseline=read_disc(SOURCE,('PL00_U.ARC',))[0]['PL00_U.ARC'];a=Archive(baseline);parent=(H/'prepared_front_return01/PL00_U.ARC').read_bytes();p=Archive(parent)
 for n in range(55,67):
  for mask in(0,15):need(a.composite(n,mask)[0].tobytes()==p.composite(n,mask)[0].tobytes(),'Next wall baseline has changed')
 refs=list(range(55,67,2));history=ROOT/'work/ver_buki_riko/shibuki_art/wall_v1/production19';pairs=json.loads((history/'pairs.json').read_text('utf8'))['frames']
 report=[]
 for n in refs:
  pair=next(v for v in pairs if v['run']==n);oldbody=np.zeros((384,384),np.uint8);oldbody[120:200,112:208]=np.array(Image.open(history/f'run_{n:03}.png'))
  v=a.layer(n)[0];body=a.composite(n,0)[0];shoot=a.composite(n+1,0)[0]
  y,x=np.nonzero(v);muzzle=pair['original_muzzle_world'];f=a.banks[0]['frames'][n];shared=[r['index']for r in a.banks[0]['frames']if r['offset']==f['offset']]
  row={'body_ref':n,'shot_ref':n+1,'body_bbox_world':bbox(v),'shared_gfx_refs':shared,'historical_native_body_index_diff':int(np.count_nonzero(v!=oldbody)),'historical_native_alpha_diff':int(np.count_nonzero((v>0)!=(oldbody>0))),'native_source':(history/f'run_{n:03}.png').relative_to(ROOT).as_posix(),'muzzle_world_from_verified_historical_mapping':muzzle,'source_pairs_sha256':sha((history/'pairs.json').read_bytes()),'head_do_not_copy_old_coarse_surface':True,'arm_do_not_stretch_into_rectangular_strip':True}
  # Raw reference publication is local only. No original X asset is supplied to generation.
  for mask,label in((0,'base'),(15,'fourth')):
   a.composite(n,mask)[0].save(out/f'{label}_{n:03}.png');a.composite(n+1,mask)[0].save(out/f'{label}_{n+1:03}.png')
  report.append(row)
 for group,nums in enumerate((refs[:3],refs[3:]),1):
  board=Image.new('RGBA',(1536,1024),(0,0,0,0))
  for row,(mask,label)in enumerate(((0,'base'),(15,'fourth'))):
   for col,n in enumerate(nums):
    im=a.composite(n,mask)[0];alpha=np.array(im)[:,:,3];need(not alpha[:120].any()and not alpha[184:].any()and not alpha[:,:128].any()and not alpha[:,192:].any(),'Wall reference crop clips actual pose')
    crop=im.crop((128,120,192,184)).resize((512,512),Image.Resampling.NEAREST);board.alpha_composite(crop,(col*512,row*512))
  board.save(out/f'page{group:02}_poses.png')
  page([(f'{label} {n}',a.composite(n,mask)[0])for mask,label in((0,'base'),(15,'fourth'))for n in nums],a.composite(0,0)[0],out/f'page{group:02}_review.png',cols=3,scale=4)
 idleboard=Image.new('RGBA',(1024,512),(0,0,0,0))
 for i,mask in enumerate((0,15)):idleboard.alpha_composite(a.composite(0,mask)[0].crop((128,120,192,184)).resize((512,512),Image.Resampling.NEAREST),(i*512,0))
 idleboard.save(out/'accepted_idle_reference.png')
 write(out/'manifest.json',{'source_bin_sha256':SOURCE_SHA,'source_PL00_sha256':sha(baseline),'future_parent_checkpoint_PL00_sha256':sha(parent),'all_wall_images_identical_to_checkpoint':True,'refs':report,'layout':{'source_width':1536,'source_height':1024,'columns':3,'rows':2,'top':'base','bottom':'Fourth','page01_refs':refs[:3],'page02_refs':refs[3:],'native_world_crop':[-32,-40,32,24],'integer_upscale':8,'native_origin_inside_each64px_cell':[32,40]},'reference_only_no_art_generated':True,'render_is_extracted_native_not_runtime':True,'design_goals':['accepted compact proportions and native scale','small dark hair line clusters and three-tone volume like idle','clear gold iris and segmented fringe','same body/joint coordinates across two costumes','new Fourth black/gold long side coat panels','keep wall contact palm and curled knee poses','firing barrel kept original scale/muzzle later; no arm length stretching'],'pending':['new source artwork for six exact poses in two costumes','native hand and muzzle pixel recheck after registration','all12 body/shot refs; all16 armor masks; full GPU/render validation']})
 print(json.dumps({'refs':refs,'pages':2,'muzzles':{str(v['body_ref']):v['muzzle_world_from_verified_historical_mapping']for v in report},'body_source_differences':[(v['body_ref'],v['historical_native_body_index_diff'],v['historical_native_alpha_diff'])for v in report]}))

if __name__=='__main__':main()
