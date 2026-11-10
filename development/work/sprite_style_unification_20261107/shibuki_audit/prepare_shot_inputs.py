"""원래 총구와 새 전신을 나란히 보존한 팔 교정 입력. 완성 사격 아트가 아님."""
from pathlib import Path
import sys,json,hashlib
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
import numpy as np
from PIL import Image,ImageDraw
from scripts.c01_audio_build import read_disc
from scripts.export_x_consistency import Archive,page
from native_pose_pack import SOURCE,SOURCE_SHA
from src.psx_disc import file_hash
assert file_hash(SOURCE)==SOURCE_SHA
a=Archive(read_disc(SOURCE,('PL02_U.ARC',))[0]['PL02_U.ARC'])
pairs=json.loads((ROOT/'work/ver_buki_riko/shibuki_art/human_run_v1/paired04/pairs.json').read_text('utf8'))['frames']
out=H/'shot_inputs01';out.mkdir(exist_ok=False);report=[]
refs=list(range(3,32,2))
rgb=np.array([[(int(w)>>s&31)*255//31 for s in (0,5,10)]for w in a.words[16:32]],np.int32)
for kind,start in [('before',16),('after',0)]:
 folder=out/kind;folder.mkdir();items=[]
 for n in refs:
  v=np.array(Image.open(H/'run_registered02'/kind/f'{n:03}_indices.png'));r=next(r for r in pairs if r['run']==n)
  mx,my=map(int,r['original_muzzle']);mx+=160;my+=160
  old=np.array(a.composite(n+1,15)[0]);ix=((old[:,:,:3,None].transpose(0,1,3,2).astype(np.int32)-rgb[None,None,:,:])**2).sum(3).argmin(2).astype(np.uint8);ix[old[:,:,3]==0]=0
  # Capture only the pre-existing barrel left of the original face/hand.
  # Neither old face nor old sleeve is carried into the new character.
  mask=np.zeros((384,384),bool);mask[my-6:my+6,mx-2:mx+10]=True;mask &= ix>0
  target=v.copy();target[mask]=ix[mask]
  Image.fromarray(target).save(folder/f'{n+1:03}_anchor_indices.png');a.rgba(target,start).save(folder/f'{n+1:03}_anchor.png')
  Image.fromarray(np.where(mask,ix,0).astype(np.uint8)).save(folder/f'{n+1:03}_barrel_indices.png')
  a.rgba(v,start).save(folder/f'{n:03}_new_run.png')
  items.append((f'{n+1} ARM CORRECTION INPUT',a.rgba(target,start)))
  if kind=='before':report.append({'run_ref':n,'shoot_ref':n+1,'muzzle_world':[mx-160,my-160],'origin':[160,160],'barrel_region':[mx-2,my-6,mx+10,my+6],'edit_region_hint':[mx+8,my-3,160,my+17],'barrel_pixels':int(mask.sum()),'accepted_body_source':f'run_registered02/{kind}/{n:03}_indices.png','new_arm_art_needed':True,'warning':'현재 굽힌 팔은 그대로 남긴 교정 입력. 이 상태를 완성된 사격 그림으로 패킹하지 않는다.'})
 for k in range(0,len(refs),4):
  sheet=Image.new('RGBA',(1536,1024),(0,0,0,0))
  for j,n in enumerate(refs[k:k+4]):
   im=Image.open(folder/f'{n+1:03}_anchor.png').crop((112,128,208,192)).resize((768,512),Image.Resampling.NEAREST)
   sheet.alpha_composite(im,(j%2*768,j//2*512))
  sheet.save(folder/f'page_{k//4+1:02}.png')
  page(items[k:k+4],a.composite(0,15 if kind=='before'else 0)[0],folder/f'review_{k//4+1:02}.png',cols=2,scale=4)
(out/'inputs.json').write_text(json.dumps({'source_sha256':SOURCE_SHA,'purpose':'신규 전체 그림 유지, 원래 총구 고정, 팔/손/소매만 자연스럽게 연결하는 교정 입력','not_final_art':True,'native_crop':[112,128,208,192],'generated_expected_size':[1536,1024],'scale':.125,'old_body_copied':False,'barrel_copied_at_original_coordinate':True,'frames':report},ensure_ascii=False,indent=2)+'\n','utf8')
