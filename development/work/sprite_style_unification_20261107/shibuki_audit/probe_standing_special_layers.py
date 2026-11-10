"""95/97 새 두 의상 공통 머리와 부분 아머 소유를 비교하는 비패킹 후보."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
from scripts.export_x_consistency import Archive,page
from prepare_lowhp_final import compose
def main():
 o=H/'standing_special_layers01';need(not o.exists(),'Fresh layers');o.mkdir();s=H/'standing_special_native02';p=H/'prepared_hurt_base01/PL00_U.ARC';a=Archive(p.read_bytes());yy,xx=np.indices((384,384));x=xx-160;y=yy-160;rgb=np.array([[(int(w)>>k&31)*255//31 for k in(0,5,10)]for w in a.words[:32]],np.int32);remap=np.argmin(((rgb[:16,None]-rgb[None,17:32])**2).sum(2),axis=1)+1;rows=[];pics=[]
 for n in(95,97):
  base=np.array(Image.open(s/f'base_{n:03}_indices.png'));source=np.array(Image.open(s/f'fourth_{n:03}_indices.png'));deco=(x>=(1 if n==95 else 0))&(x<13)&(y>=-22)&(y<-5);common=(y<-5)&~deco;overlay=source.copy();overlay[common]=0;missing=(base>0)&(overlay==0)&~common;edge=[]
  for py,px in zip(*np.nonzero(missing)):
   need(base[py,px]in(2,15),'Unexpected non-outline mismatch');q=int(remap[base[py,px]]);overlay[py,px]=q;edge.append([int(x[py,px]),int(y[py,px]),int(base[py,px]),q])
  owner=np.full(base.shape,6,np.uint8);leg=(y>=13)|((y>=10)&(x>=-8)&(x<6));owner[leg]=8
  if n==95:arm=(y>=0)&(y<10)&((x<-9)|(x>=6))
  else:arm=((x<=-8)&(y>=-5)&(y<9))|((x>=-3)&(x<4)&(y>=-3)&(y<8))
  owner[arm]=7;owner[y<-5]=5;layers={0:base,**{b:np.where(owner==b,overlay,0).astype('uint8')for b in(5,6,7,8)}};full=compose(a,layers,15);full.save(o/f'fourth_{n:03}.png');a.rgba(base).save(o/f'base_{n:03}.png');need(np.array_equal(np.array(full)[:,:,3]>0,(base>0)|(overlay>0)),'Alpha logic')
  for b,v in layers.items():Image.fromarray(v).save(o/f'{n:03}_bank{b}_indices.png')
  Image.fromarray(common.astype('uint8')*255).save(o/f'{n:03}_common_head_mask.png');Image.fromarray(owner).save(o/f'{n:03}_ownership.png');Image.fromarray(missing.astype('uint8')*255).save(o/f'{n:03}_outline_registration_mask.png');page([(f'{n} mask{m:X}',compose(a,layers,m))for m in range(16)],a.composite(0,15)[0],o/f'partial_{n:03}.png',cols=4,scale=4);pics.extend([(f'{n} new source',a.rgba(source,16)),(f'{n} common/parts',full),(f'{n} head only',compose(a,layers,1)),(f'{n} arms only',compose(a,layers,4))]);rows.append({'ref':n,'new_base_exact':True,'new_base_common_head_no_old_head_used':True,'head_common_opaque':int(((base>0)&common).sum()),'decoration_region':{'x_min':1 if n==95 else 0,'x_max_exclusive':13,'y_min':-22,'y_max_exclusive':-5},'outline_registration_cells':edge,'outline_registration_count':len(edge),'new_source_alpha_elsewhere_exact':True,'layer_pixels':{str(b):int((v>0).sum())for b,v in layers.items()},'layer_hashes':{str(b):sha(v.tobytes())for b,v in layers.items()}})
 page(pics,a.composite(0,15)[0],o/'common_comparison.png',cols=4,scale=5);write(o/'report.json',{'source_native_sha256':sha((s/'report.json').read_bytes()),'parent_sha256':sha(a.data),'rows':rows,'ownership_policy':'새 기본 머리 공통, 포스 장식 Head, 앞팔·소매 Arm, 상의/옆머리 Body, 하체 Leg. 다른 각도 대기머리 복사 없음.','source_outline_policy':'두 의상의 1px 윤곽 불일치만 새 기본 원화의 기존 어두운 색을 원포스 CLUT 최근접으로 등록. 모든 새 내부무늬는 원화 표본이며 임의 검정채움 아님.','new96_policy':'원US 및 현재PL00의 96=95 x+1을 후속 패킹에서 유지. 현PL02에 자동적용 안함.','partial_visual_review_pending':True,'arc_written':False,'runtime_verified':False});print(json.dumps(rows))
if __name__=='__main__':main()
