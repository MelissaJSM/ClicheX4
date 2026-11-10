"""새 저체력2폼을 동일 등방축척으로 native 등록하는 비교. 다른 원화로 덮지 않음."""
from pathlib import Path
import sys,json
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
import numpy as np
from PIL import Image
from scipy.ndimage import label
from scripts.c01_audio_build import read_disc
from scripts.export_x_consistency import Archive,page
from scripts.prepare_rin_run import quantize
from native_pose_pack import SOURCE,SOURCE_SHA,sha,need,write
from src.psx_disc import file_hash
from restore_remaining_sources import clean,foot,bbox

def main():
 need(file_hash(SOURCE)==SOURCE_SHA,'Source changed');raw=read_disc(SOURCE,('PL00_U.ARC',))[0]['PL00_U.ARC'];arc=Archive(raw);src=H/'lowhp_generation01/generated.png';im=Image.open(src).convert('RGBA');need(im.size==(1536,1024),'Unexpected image size')
 cuts=[clean(im.crop((i*768,0,(i+1)*768,1024)))for i in range(2)];boxes=[bbox(np.array(c)[:,:,3]>=200)for c in cuts];scale=47/max(b[3]-b[1]for b in boxes)
 out=H/'lowhp_generation01/native01';out.mkdir(exist_ok=False);items=[];rows=[];arrays=[]
 for i,(form,start)in enumerate((('base',0),('fourth',16))):
  rgb=np.array([[(int(w)>>s&31)*255//31 for s in(0,5,10)]for w in arc.words[start+1:start+16]],np.int32)
  v=quantize(cuts[i],rgb,scale);cx,cy=foot(v>0);tx,ty=foot(np.array(arc.composite(120,15 if i else 0)[0])[:,:,3]>0);dx,dy=tx-cx,ty-cy
  a=np.zeros((384,384),np.uint8);a[dy:dy+v.shape[0],dx:dx+v.shape[1]]=v;arrays.append(a)
  Image.fromarray(a).save(out/f'{form}_120_indices.png');pic=arc.rgba(a,start);pic.save(out/f'{form}_120.png')
  items.extend([(f'{form} current120',arc.composite(120,15 if i else 0)[0]),(f'{form} new120',pic)])
  rows.append({'form':form,'source_cell':[i*768,0,(i+1)*768,1024],'source_opaque_bbox':boxes[i],'uniform_scale':scale,'translation':[dx,dy],'foot_anchor':[tx,ty],'native_bbox':bbox(a>0),'old_body_or_head_copied':False})
 page(items,arc.composite(0,0)[0],out/'comparison.png',cols=2,scale=5)
 for i,form in enumerate(('base','fourth')):page([(f'{form} new120',arc.rgba(arrays[i],16*i))],arc.composite(0,15 if i else 0)[0],out/f'{form}_idle_comparison.png',cols=1,scale=6)
 missing=(arrays[0]>0)&(arrays[1]==0);marked=np.array(arc.rgba(arrays[1],16));marked[missing]=(255,0,0,255);Image.fromarray(marked).save(out/'base_outside_fourth.png')
 write(out/'registration.json',{'source_sha256':sha(src.read_bytes()),'source_bin_sha256':SOURCE_SHA,'uniform_page_scale':scale,'requested8x_but_generated_sprite_height':max(b[3]-b[1]for b in boxes),'fixed_target47_native_height_no_xy_stretch':True,'rows':rows,'base_alpha_outside_fourth':int(missing.sum()),'missing_world':[[int(x)-160,int(y)-160]for y,x in zip(*np.nonzero(missing))],'not_packed':True})
 print(json.dumps({'scale':scale,'boxes':boxes,'native':[r['native_bbox']for r in rows],'base_outside_fourth':int(missing.sum())}))
if __name__=='__main__':main()
