"""새 저체력 재시도 원화를 등방 등록하고 수용된 머리 모듈 대조를 남긴다."""
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
 need(file_hash(SOURCE)==SOURCE_SHA,'Source changed')
 arc=Archive(read_disc(SOURCE,('PL00_U.ARC',))[0]['PL00_U.ARC']);d=H/'lowhp_generation02';src=d/'generated.png';im=Image.open(src).convert('RGBA');need(im.size==(1536,1024),'Unexpected size')
 cuts=[clean(im.crop((i*768,0,(i+1)*768,1024)))for i in range(2)];boxes=[bbox(np.array(c)[:,:,3]>=200)for c in cuts]
 yy,xx=np.indices((384,384));headmask=yy<156;head=np.where(headmask,arc.layer(116)[0],0).astype(np.uint8);ornament=np.where(headmask,arc.layer(116,5)[0],0).astype(np.uint8)
 report=[]
 for method,scale in [('whole',47/max(b[3]-b[1]for b in boxes)),('accepted_head',26/(848-533))]:
  out=d/method;out.mkdir(exist_ok=False);rows=[];imgs=[];arrays=[]
  for i,(form,pal)in enumerate((('base',0),('fourth',16))):
   rgb=np.array([[(int(w)>>s&31)*255//31 for s in(0,5,10)]for w in arc.words[pal+1:pal+16]],np.int32);v=quantize(cuts[i],rgb,scale)
   ys,xs=np.nonzero(v);sole=ys>=ys.max()-5;center=(xs[sole].min()+xs[sole].max())/2;dx=round(161-center);dy=182-int(ys.max())
   a=np.zeros((384,384),np.uint8);a[dy:dy+v.shape[0],dx:dx+v.shape[1]]=v
   if method=='accepted_head':a[headmask]=0
   pic=arc.rgba(a,pal)
   if method=='accepted_head':
    pic.alpha_composite(arc.rgba(head,0))
    if i:pic.alpha_composite(arc.rgba(ornament,16))
   Image.fromarray(a).save(out/f'{form}_body_indices.png');pic.save(out/f'{form}_120.png');arrays.append(a);imgs.append(pic)
   page([(f'{form} current120',arc.composite(120,15 if i else 0)[0]),(f'{form} {method}',pic)],arc.composite(0,15 if i else 0)[0],out/f'{form}_idle_comparison.png',cols=2,scale=6)
   rows.append({'form':form,'uniform_scale':scale,'translation':[dx,dy],'source_opaque_bbox':boxes[i],'native_body_bbox':bbox(a>0),'old_lowHP_body_or_head_used':False,'accepted_head_ref':116 if method=='accepted_head'else None})
  b=arrays[0].copy()
  if method=='accepted_head':b[head>0]=head[head>0];Image.fromarray(head).save(out/'accepted_head_indices.png');Image.fromarray(ornament).save(out/'accepted_head_ornament_indices.png')
  Image.fromarray(b).save(out/'base_120_indices.png');uncovered=(b>0)&(np.array(imgs[1])[:,:,3]==0);marked=np.array(imgs[1]);marked[uncovered]=(255,0,0,255)
  page([('new base',imgs[0]),('new Fourth',imgs[1]),('base outside Fourth RED',Image.fromarray(marked))],arc.composite(0,15)[0],out/'pair_comparison.png',cols=3,scale=6)
  obj={'source_bin_sha256':SOURCE_SHA,'source_art_sha256':sha(src.read_bytes()),'method':method,'rows':rows,'base_outside_fourth':int(uncovered.sum()),'outside_world':[[int(x)-160,int(y)-160]for y,x in zip(*np.nonzero(uncovered))],'not_packed':True};write(out/'registration.json',obj);report.append(obj)
 write(d/'registration_summary.json',report);print(json.dumps({'source_boxes':boxes,'native':[{'method':r['method'],'outside':r['base_outside_fourth'],'rows':r['rows']}for r in report]}))
if __name__=='__main__':main()
