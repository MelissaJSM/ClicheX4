"""원화 팔 의미영역 등록. 원화 외 채색/가로늘림 없이 앞머리 혼입을 배제한다."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image,ImageDraw
from scipy.ndimage import label
ROOT=Path(__file__).resolve().parents[4];D=Path(__file__).parent;N=D.parent
sys.path[:0]=[str(ROOT),str(D),str(N/'native_restore')]
from preview_restore import Archive,sha,digest,write,need,helper
Y,X=np.indices((384,384));Y-=160;X-=160
def getpage(n):return 'a'if n<=40 else'b'if n<=48 else'c'
# Inclusive bounds traced from the authored native 050/052/054 index grid.
# These are source texels, not new colors. The source map records every copy.
ROWS={
50:{-12:(-20,-14),-11:(-20,-14),-10:(-18,-13),-9:(-17,-12),-8:(-17,-10),-7:(-16,-10),-6:(-14,-9),-5:(-14,-8),-4:(-13,-7),-3:(-12,-2),-2:(-11,2),-1:(-9,2),0:(-6,2),1:(-3,3)},
52:{-9:(-21,-15),-8:(-21,-14),-7:(-21,-14),-6:(-18,-13),-5:(-17,-12),-4:(-17,-11),-3:(-16,-10),-2:(-15,-9),-1:(-14,-8),0:(-13,-7),1:(-12,-5),2:(-10,2),3:(-8,3),4:(-6,4),5:(-4,5)},
54:{-8:(-21,-14),-7:(-21,-14),-6:(-21,-14),-5:(-18,-10),-4:(-17,-7),-3:(-17,-3),-2:(-16,2),-1:(-14,3),0:(-11,4),1:(-9,4)}
}
def main():
 a=Archive((N/'native_restore/nova_sync_v1/PL02_U.ARC').read_bytes());out=D/'firing_joint_probe_v3';out.mkdir(exist_ok=False);rows=[];records=[]
 hands={q['ref']:q['new_hand_bbox']for q in json.loads((D/'canonical_cases_probe_v1/registration.json').read_text('utf8'))['frames']}
 for n in range(34,55,2):
  bpath=D/'canonical_cases_probe_v1'/f'before_{n-1:03}.png';body=np.array(Image.open(bpath));sp=D/f'firing_{getpage(n)}_registered_v1'/f'before_{n:03}.png';src=np.array(Image.open(sp));bar=np.array(Image.open(D/'weapon_constraints_v1'/f'case_{n:03}.png'));oy,ox=np.nonzero(bar);tmx=int(ox.min())-160;tmy=float(np.median(oy[ox==ox.min()]))-160;sy,sx=np.nonzero(src);smx=int(sx.min())-160;smy=float(np.median(sy[sx==sx.min()]))-160;dx=tmx-smx;dy=round(tmy-smy)
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
  for name,val in [('before',target),('new_arm_module',placed),('folded_hand_remove',held.astype(np.uint8)*255),('arm_mask',use.astype(np.uint8)*255),('source_arm_mask',mask.astype(np.uint8)*255)]:Image.fromarray(val).save(out/f'{name}_{n:03}.png')
  np.save(out/f'arm_source_map_{n:03}.npy',source_map)
  labs,count=label(target>0,np.ones((3,3)));sizes=np.bincount(labs.flat);sizes[0]=0
  small=[{'pixels':int(sizes[k]),'coordinates_xy':[[int(x-160),int(y-160)]for y,x in zip(*np.nonzero(labs==k))]}for k in range(1,count+1)if sizes[k]<30]
  records.append({'ref':n,'source_body_sha256':digest(bpath),'source_new_arm_sha256':digest(sp),'source_muzzle':[smx,smy],'target_muzzle':[tmx,tmy],'arm_translation':[dx,dy],'source_rows':ROWS.get(n),'old_arm_pixels_used':0,'original_case_pixels':int((bar>0).sum()),'alpha_components_8':int(count),'small_components':small,'body_pixels_changed':int(np.count_nonzero(body!=target)),'indexed_sha256':sha(target.tobytes()),'art_review_pending':True})
  rows.append((f'fire {n}',[('fixed new body',a.rgba(body,16)),('new arm full source',a.rgba(src,16)),('semantic arm / original gun candidate',a.rgba(target,16))]))
 for i in range(0,len(rows),4):helper.grid(rows[i:i+4],out/f'comparison_{i//4+1}.png',6)
 write(out/'registration.json',{'frames':records,'native_packed':False,'runtime_verified':False,'no_horizontal_arm_stretch':True,'scope':'새 사격팔 의미영역을 강체 이동. 새 비사격 머리/하체 보존. 검수 전 후보.'});print(json.dumps(records))
if __name__=='__main__':main()
