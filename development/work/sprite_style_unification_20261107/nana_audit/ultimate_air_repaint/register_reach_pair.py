"""총구/어깨 동시 가이드로 새로 그린 세 팔을 공동 몸체에 등록한다."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image
from scipy.ndimage import label
ROOT=Path(__file__).resolve().parents[4];D=Path(__file__).parent;N=D.parent
sys.path[:0]=[str(ROOT),str(D),str(N/'native_restore')]
from preview_restore import Archive,sha,digest,write,need,helper
Y,X=np.indices((384,384));Y-=160;X-=160
ROWS={
50:{-13:(-27,-18),-12:(-27,-18),-11:(-27,-18),-10:(-24,-17),-9:(-23,-16),-8:(-23,-15),-7:(-22,-12),-6:(-19,-11),-5:(-19,-10),-4:(-18,-3),-3:(-17,-2),-2:(-16,-3),-1:(-14,-4)},
52:{-10:(-28,-19),-9:(-28,-19),-8:(-28,-18),-7:(-28,-18),-6:(-24,-18),-5:(-23,-17),-4:(-22,-16),-3:(-22,-15),-2:(-20,-14),-1:(-20,-11),0:(-19,-10),1:(-18,-3),2:(-17,-2),3:(-16,-3)},
54:{-9:(-29,-18),-8:(-29,-18),-7:(-29,-18),-6:(-29,-18),-5:(-24,-17),-4:(-24,-3),-3:(-23,-2),-2:(-23,-3),-1:(-17,-7)}
}
def main():
 a=Archive((N/'native_restore/nova_sync_v1/PL02_U.ARC').read_bytes());out=D/'firing_reach_pair_probe_v2';out.mkdir(exist_ok=False);rows=[];records=[]
 hands={q['ref']:q['new_hand_bbox']for q in json.loads((D/'canonical_cases_probe_v1/registration.json').read_text('utf8'))['frames']}
 for n in(50,52,54):
  images={};rec={'ref':n,'forms':{}}
  bar=np.array(Image.open(D/'weapon_constraints_v1'/f'case_{n:03}.png'));oy,ox=np.nonzero(bar);tmx=int(ox.min())-160;tmy=float(np.median(oy[ox==ox.min()]))-160;gunwindow=(X>=tmx)&(X<tmx+8)&(Y>=tmy-3)&(Y<=tmy+5)
  for form in('before','after'):
   bodypath=D/('canonical_cases_probe_v1'if form=='before'else'costume_pair_probe_v2')/f'{form}_{n-1:03}.png';body=np.array(Image.open(bodypath));sp=D/f'firing_reach_{form}_registered_v{2 if form=="before"else 3}'/f'{form}_{n:03}.png';src=np.array(Image.open(sp));sy,sx=np.nonzero(src);smx=int(sx.min())-160;smy=float(np.median(sy[sx==sx.min()]))-160;dx=tmx-smx;dy=round(tmy-smy)
   # Arm endpoints are now simultaneously authored; only <=1px x registration.
   need(abs(dx)<=1 and abs(dy)<=1,'Authored arm reach differs from fixed muzzle')
   mask=np.zeros(body.shape,bool)
   for y,(l,r)in ROWS[n].items():mask[y+160,l+160:r+161]=True
   mask&=src>0;placed=np.zeros_like(src);py,px=np.nonzero(mask);placed[py+dy,px+dx]=src[mask];source_map=np.full(body.shape,-1,np.int32);source_map[py+dy,px+dx]=py*384+px;placed[(X>=tmx)&(X<tmx+8)]=0
   hx,hy,hx1,hy1=hands[n-1];held=(X<hx1+1)&(X>=hx-8)&(Y>=hy-3)&(Y<hy1+2);target=body.copy();target[held]=0
   ey,ex=np.nonzero((body==14)&(Y<2));ex=int(np.median(ex))-160;ey=int(np.median(ey))-160;protect=((Y<=ey+4)&(X>=ex-8))|(Y>max(8,ey+20));use=(placed>0)&~(protect&(body>0));target[use]=placed[use];target[protect&(body>0)]=body[protect&(body>0)];target[gunwindow]=bar[gunwindow]
   if n==54:target[163,154]=0
   images[form]=target;images[form+'_source']=src
   for name,val in [('arm_source_mask',mask.astype(np.uint8)*255),('placed_arm',placed),('applied_arm',use.astype(np.uint8)*255),('folded_hand_remove',held.astype(np.uint8)*255)]:Image.fromarray(val).save(out/f'{form}_{name}_{n:03}.png')
   np.save(out/f'{form}_arm_source_map_{n:03}.npy',source_map)
   rec['forms'][form]={'source_body_sha256':digest(bodypath),'source_arm_sha256':digest(sp),'translation':[dx,dy],'muzzle_source':[smx,smy],'muzzle_target':[tmx,tmy],'selected_source_rows':ROWS[n],'arm_pixels_used':int(use.sum())}
  unclipped=images['after'].copy();outside=(unclipped>0)&(images['before']==0);images['after'][outside]=0
  for form in('before','after'):
   ar=images[form];Image.fromarray(ar).save(out/f'{form}_{n:03}.png');labs,count=label(ar>0,np.ones((3,3)));sizes=np.bincount(labs.flat);sizes[0]=0
   rec['forms'][form].update({'indexed_sha256':sha(ar.tobytes()),'components_8':int(count),'small_components':[{'count':int(sizes[k]),'xy':[[int(x-160),int(y-160)]for y,x in zip(*np.nonzero(labs==k))]}for k in range(1,count+1)if sizes[k]<30],'gun_window_exact':bool(np.array_equal(ar[gunwindow],bar[gunwindow]))})
  rec['after_envelope_clipped']=[[int(x-160),int(y-160),int(unclipped[y,x])]for y,x in zip(*np.nonzero(outside))];records.append(rec)
  rows.append((f'reach {n}',[('new jacket source',a.rgba(images['before_source'],16)),('fixed new body / jacket arm',a.rgba(images['before'],16)),('new bare source',a.rgba(images['after_source'],0)),('fixed new body / bare arm',a.rgba(images['after'],0))]))
 helper.grid(rows,out/'comparison.png',7);write(out/'registration.json',{'frames':records,'native_packed':False,'runtime_verified':False,'new_art_for_arm_only':True,'old_body_overlay_used':False,'no_horizontal_stretch':True,'art_review_pending':True});print(json.dumps(records))
if __name__=='__main__':main()
