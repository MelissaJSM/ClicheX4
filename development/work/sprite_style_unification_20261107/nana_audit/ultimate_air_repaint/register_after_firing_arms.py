"""맨팔 사격 원화에서 팔을 분리하고 새 공통 몸체/총 위치에 정합한다."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image,ImageDraw
from scipy.ndimage import label
ROOT=Path(__file__).resolve().parents[4];D=Path(__file__).parent;N=D.parent
sys.path[:0]=[str(ROOT),str(D),str(N/'native_restore')]
from preview_restore import Archive,sha,digest,write,need,helper
from register_firing_arms_v3 import getpage,ROWS
Y,X=np.indices((384,384));Y-=160;X-=160
def main():
 a=Archive((N/'native_restore/nova_sync_v1/PL02_U.ARC').read_bytes());out=D/'firing_costume_pair_probe_v1';out.mkdir(exist_ok=False);rows=[];records=[]
 hands={q['ref']:q['new_hand_bbox']for q in json.loads((D/'canonical_cases_probe_v1/registration.json').read_text('utf8'))['frames']}
 for n in range(34,55,2):
  bp=D/'firing_joint_probe_v3'/f'before_{n:03}.png';before=np.array(Image.open(bp));bodypath=D/'costume_pair_probe_v2'/f'after_{n-1:03}.png';body=np.array(Image.open(bodypath));sp=D/f'firing_{getpage(n)}_after_registered_v1'/f'after_{n:03}.png';src=np.array(Image.open(sp));bar=np.array(Image.open(D/'weapon_constraints_v1'/f'case_{n:03}.png'));oy,ox=np.nonzero(bar);tmx=int(ox.min())-160;tmy=float(np.median(oy[ox==ox.min()]))-160;sy,sx=np.nonzero(src);smx=int(sx.min())-160;smy=float(np.median(sy[sx==sx.min()]))-160;dx=tmx-smx;dy=round(tmy-smy)
  ey,ex=np.nonzero((body==14)&(Y<2));ex=int(np.median(ex))-160;ey=int(np.median(ey))-160
  poly=[(-45,smy-3),(-12,smy-3),(-7,smy),(2,smy+1),(4,smy+4),(-5,smy+5),(-45,smy+5)]
  m=Image.new('1',(384,384));ImageDraw.Draw(m).polygon([(round(x+160),round(y+160))for x,y in poly],fill=1);mask=np.array(m).astype(bool)
  if n in ROWS:
   mask[:]=False
   for y,(l,r)in ROWS[n].items():mask[y+160,l+160:r+161]=True
  else:mask&=~((Y<=ey+4)&(X>=ex-8))
  mask&=src>0
  placed=np.zeros_like(src);py,px=np.nonzero(mask);placed[py+dy,px+dx]=src[mask];source_map=np.full(body.shape,-1,np.int32);source_map[py+dy,px+dx]=py*384+px
  placed[(X>=tmx)&(X<tmx+8)]=0
  hx,hy,hx1,hy1=hands[n-1];held=(X<hx1+1)&(X>=hx-8)&(Y>=hy-3)&(Y<hy1+2);target=body.copy();target[held]=0
  protect=((Y<=ey+4)&(X>=ex-8))|(Y>max(8,ey+20));use=(placed>0)&~(protect&(body>0));target[use]=placed[use];target[protect&(body>0)]=body[protect&(body>0)]
  gunwindow=(X>=tmx)&(X<tmx+8)&(Y>=tmy-3)&(Y<=tmy+5);target[gunwindow]=bar[gunwindow]
  if n==54:
   # Bottom of the newly drawn folded hand is hidden by the firing posture.
   before[163,154]=0;target[163,154]=0
  unclipped=target.copy();outside=(target>0)&(before==0);target[outside]=0
  for name,val in [('before',before),('after',target),('after_unclipped',unclipped),('after_new_arm_module',placed),('after_envelope_clip',outside.astype(np.uint8)*255),('after_arm_mask',use.astype(np.uint8)*255),('after_source_arm_mask',mask.astype(np.uint8)*255)]:Image.fromarray(val).save(out/f'{name}_{n:03}.png')
  np.save(out/f'after_arm_source_map_{n:03}.npy',source_map)
  labs,count=label(target>0,np.ones((3,3)));sizes=np.bincount(labs.flat);sizes[0]=0;small=[{'pixels':int(sizes[k]),'coordinates_xy':[[int(x-160),int(y-160)]for y,x in zip(*np.nonzero(labs==k))]}for k in range(1,count+1)if sizes[k]<30]
  records.append({'ref':n,'before_source_sha256':digest(bp),'after_body_sha256':digest(bodypath),'after_new_arm_sha256':digest(sp),'source_muzzle':[smx,smy],'target_muzzle':[tmx,tmy],'arm_translation':[dx,dy],'source_rows':ROWS.get(n),'old_arm_pixels_used':0,'original_case_exact':bool(np.array_equal(target[gunwindow],bar[gunwindow])),'alpha_components_8':int(count),'small_components':small,'jacket_envelope_clipped':[[int(x-160),int(y-160),int(unclipped[y,x])]for y,x in zip(*np.nonzero(outside))],'after_indexed_sha256':sha(target.tobytes()),'art_review_pending':True})
  rows.append((f'pair {n}',[('new before candidate',a.rgba(before,16)),('new bare arm full source',a.rgba(src,0)),('same body / paired arm candidate',a.rgba(target,0))]))
 for i in range(0,len(rows),4):helper.grid(rows[i:i+4],out/f'comparison_{i//4+1}.png',6)
 write(out/'registration.json',{'frames':records,'native_packed':False,'runtime_verified':False,'no_horizontal_arm_stretch':True,'scope':'새 맨팔 원화 의미영역 강체 이동. 재킷 팔 알파 내 국소 의상 등록. 미술 검수 전 후보.'});print(json.dumps(records))
if __name__=='__main__':main()
