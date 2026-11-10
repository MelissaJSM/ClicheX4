"""같은3/4각도의 수용 대기 머리/눈감김 모듈과 새 피로 상체의 연결 비교."""
from pathlib import Path
import sys,json
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
import numpy as np
from PIL import Image
from scripts.c01_audio_build import read_disc
from scripts.export_x_consistency import Archive,page
from scripts.prepare_rin_run import quantize
from native_pose_pack import SOURCE,SOURCE_SHA,sha,need,write
from src.psx_disc import file_hash
from restore_remaining_sources import clean,bbox

def main():
 need(file_hash(SOURCE)==SOURCE_SHA,'Source changed');arc=Archive(read_disc(SOURCE,('PL00_U.ARC',))[0]['PL00_U.ARC']);d=H/'lowhp_generation01';im=Image.open(d/'generated.png').convert('RGBA');out=d/'native_modular02';out.mkdir(exist_ok=False)
 yy,xx=np.indices((384,384));headmask=yy<156
 # Actual accepted closed-eye idle116; includes its original one-pixel breathing descent.
 head=np.where(headmask,arc.layer(116)[0],0).astype(np.uint8);ornament=np.where(headmask,arc.layer(116,5)[0],0).astype(np.uint8)
 scale=26/(847-477);rows=[];imgs=[];arrays=[]
 for i,(form,pal)in enumerate((('base',0),('fourth',16))):
  src=clean(im.crop((i*768,0,(i+1)*768,1024)));rgb=np.array([[(int(w)>>s&31)*255//31 for s in(0,5,10)]for w in arc.words[pal+1:pal+16]],np.int32);v=quantize(src,rgb,scale)
  ys,xs=np.nonzero(v);sole=ys>=ys.max()-5;sole_center=(xs[sole].min()+xs[sole].max())/2;dx=round(161-sole_center);dy=182-int(ys.max())
  body=np.zeros((384,384),np.uint8);body[dy:dy+v.shape[0],dx:dx+v.shape[1]]=v;body[headmask]=0
  full=arc.rgba(body,pal);full.alpha_composite(arc.rgba(head,0))
  if i:full.alpha_composite(arc.rgba(ornament,16))
  full.save(out/f'{form}_120.png');Image.fromarray(body).save(out/f'{form}_body_indices.png');arrays.append(body);imgs.append(full)
  page([(f'{form} new body + accepted head116',full)],arc.composite(0,15 if i else 0)[0],out/f'{form}_idle_comparison.png',cols=1,scale=6)
  rows.append({'form':form,'new_body_source_scale':scale,'new_body_translation':[dx,dy],'source_neck_y':477,'source_foot_y':847,'target_neck_y':156,'target_foot_y':182,'accepted_head_ref':116,'head_region':'y<156; existing116 one-pixel breath descent retained','old_lowHP_head_used':False,'new_body_copied_from_old':False,'new_body_bbox':bbox(body>0)})
 Image.fromarray(head).save(out/'accepted_head_indices.png');Image.fromarray(ornament).save(out/'accepted_head_ornament_indices.png')
 # Full remains a multi-CLUT composite, exactly matching accepted head colors.
 base=arrays[0].copy();base[head>0]=head[head>0];Image.fromarray(base).save(out/'base_120_indices.png')
 uncovered=(base>0)&(np.array(imgs[1])[:,:,3]==0);marked=np.array(imgs[1]);marked[uncovered]=(255,0,0,255)
 page([('new base',imgs[0]),('new Fourth',imgs[1]),('base outside Fourth RED',Image.fromarray(marked))],arc.composite(0,15)[0],out/'pair_comparison.png',cols=3,scale=5)
 write(out/'registration.json',{'source_bin_sha256':SOURCE_SHA,'source_art_sha256':sha((d/'generated.png').read_bytes()),'rows':rows,'shared_head_index_exact':True,'base_outside_fourth':int(uncovered.sum()),'outside_world':[[int(x)-160,int(y)-160]for y,x in zip(*np.nonzero(uncovered))],'not_packed':True,'idle_head_reuse_parent_authorized':True})
 print(json.dumps({'scale':scale,'body_boxes':[r['new_body_bbox']for r in rows],'outside':int(uncovered.sum())}))
if __name__=='__main__':main()
