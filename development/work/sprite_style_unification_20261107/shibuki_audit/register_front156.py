"""新 정면156 전체 그림의 고정 등방축척·접지·공유범위 비교. 패킹하지 않음."""
from pathlib import Path
import sys,json,argparse
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
import numpy as np
from PIL import Image
from scripts.c01_audio_build import read_disc
from scripts.export_x_consistency import Archive,page
from scripts.prepare_rin_run import quantize
from native_pose_pack import SOURCE,SOURCE_SHA,sha,need,write
from src.psx_disc import file_hash
from restore_remaining_sources import clean,bbox

def main(folder):
 need(file_hash(SOURCE)==SOURCE_SHA,'Source changed');a=Archive(read_disc(SOURCE,('PL00_U.ARC',))[0]['PL00_U.ARC']);d=H/folder;im=Image.open(d/'generated.png').convert('RGBA');need(im.size==(1536,1024),'Unexpected image size')
 cuts=[clean(im.crop((i*768,0,(i+1)*768,1024)))for i in range(2)];boxes=[bbox(np.array(c)[:,:,3]>=200)for c in cuts];scale=47/max(b[3]-b[1]for b in boxes)
 out=d/'native01';out.mkdir(exist_ok=False);rows=[];arrays=[]
 for i,(form,pal,mask)in enumerate((('base',0,0),('fourth',16,15))):
  rgb=np.array([[(int(w)>>s&31)*255//31 for s in(0,5,10)]for w in a.words[pal+1:pal+16]],np.int32);v=quantize(cuts[i],rgb,scale);ys,xs=np.nonzero(v);sole=ys>=ys.max()-3;cx=(xs[sole].min()+xs[sole].max())/2;dx=round(160-cx);dy=182-int(ys.max());t=np.zeros((384,384),np.uint8);t[dy:dy+v.shape[0],dx:dx+v.shape[1]]=v;arrays.append(t)
  Image.fromarray(t).save(out/f'{form}_156_indices.png');pic=a.rgba(t,pal);pic.save(out/f'{form}_156.png');page([(f'{form} current156',a.composite(156,mask)[0]),(f'{form} new156',pic)],a.composite(0,mask)[0],out/f'{form}_comparison.png',cols=2,scale=6)
  rows.append({'form':form,'uniform_scale':scale,'translation':[dx,dy],'source_opaque_bbox':boxes[i],'native_bbox':bbox(t>0),'foot_center_x':160,'foot_bottom_y':182,'original_art_copied':False})
 outside=(arrays[0]>0)&(arrays[1]==0);marked=np.array(a.rgba(arrays[1],16));marked[outside]=(255,0,0,255)
 page([('new base',a.rgba(arrays[0])),('new Fourth',a.rgba(arrays[1],16)),('base outside Fourth RED',Image.fromarray(marked))],a.composite(0,15)[0],out/'pair_comparison.png',cols=3,scale=6)
 info={'source_art_sha256':sha((d/'generated.png').read_bytes()),'source_bin_sha256':SOURCE_SHA,'records':rows,'base_alpha_outside_fourth':int(outside.sum()),'outside_by_base_index':{str(i):int(np.count_nonzero(outside&(arrays[0]==i)))for i in range(1,16)},'outside_world':[[int(x)-160,int(y)-160]for y,x in zip(*np.nonzero(outside))],'not_packed':True,'old_simplified_head_or_body_overwrite':False};write(out/'registration.json',info);print(json.dumps(info))
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--folder',choices=['front156_generation01','front156_generation02','front156_generation03'],default='front156_generation01');main(ap.parse_args().folder)
