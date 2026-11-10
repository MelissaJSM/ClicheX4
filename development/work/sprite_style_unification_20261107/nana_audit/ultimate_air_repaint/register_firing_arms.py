"""새 사격팔을 강체 정합하고 기존 총구8열을 보존하는 중간안."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image,ImageDraw
from scipy.ndimage import label
ROOT=Path(__file__).resolve().parents[4];D=Path(__file__).parent;N=D.parent
sys.path[:0]=[str(ROOT),str(D),str(N/'native_restore')]
from preview_restore import Archive,sha,digest,write,need,helper
from check_first_geometry import full
Y,X=np.indices((384,384));Y=Y-160;X=X-160
def getpage(n):return 'a'if n<=40 else'b'if n<=48 else'c'
def main():
 a=Archive((N/'native_restore/nova_sync_v1/PL02_U.ARC').read_bytes());out=D/'firing_joint_probe_v2';out.mkdir(exist_ok=False);rows=[];records=[]
 hands={q['ref']:q['new_hand_bbox']for q in json.loads((D/'canonical_cases_probe_v1/registration.json').read_text('utf8'))['frames']}
 for n in range(34,55,2):
  bpath=D/'canonical_cases_probe_v1'/f'before_{n-1:03}.png';body=np.array(Image.open(bpath));sp=D/f'firing_{getpage(n)}_registered_v1'/f'before_{n:03}.png';src=np.array(Image.open(sp));bar=np.array(Image.open(D/'weapon_constraints_v1'/f'case_{n:03}.png'));oy,ox=np.nonzero(bar);tmx=int(ox.min())-160;tmy=float(np.median(oy[ox==ox.min()]))-160;sy,sx=np.nonzero(src);smx=int(sx.min())-160;smy=float(np.median(sy[sx==sx.min()]))-160;dx=tmx-smx;dy=round(tmy-smy)
  ey,ex=np.nonzero((body==14)&(Y<2));ex=int(np.median(ex))-160;ey=int(np.median(ey))-160
  # A polygon traces the new front arm and its small shoulder attachment;
  # all source head, legs, rear arm and hips remain outside this source ROI.
  poly=[(-45,smy-3),(-12,smy-3),(-7,smy),(2,smy+1),(4,smy+4),(-5,smy+5),(-45,smy+5)]
  if n in(50,52):poly=[(-45,smy-3),(-13,smy-3),(-10,smy+3),(-5,smy+8),(4,smy+10),(6,smy+14),(-5,smy+13),(-11,smy+8),(-18,smy+4),(-45,smy+4)]
  m=Image.new('1',(384,384));ImageDraw.Draw(m).polygon([(round(x+160),round(y+160))for x,y in poly],fill=1);mask=np.array(m).astype(bool)&(src>0)
  source_head=(Y<=ey+4)&(X>=ex-8);mask&=~source_head
  placed=np.zeros_like(src);py,px=np.nonzero(mask);placed[py+dy,px+dx]=src[mask];source_map=np.full(body.shape,-1,np.int32);source_map[py+dy,px+dx]=py*384+px
  # Clear the generated candidate gun before restoring the original weapon.
  placed[(X>=tmx)&(X<tmx+8)]=0
  # Remove only the NEW folded front hand/gun module from the nonfiring body.
  hx,hy,hx1,hy1=hands[n-1];held=(X<hx1+1)&(X>=hx-8)&(Y>=hy-3)&(Y<hy1+2);target=body.copy();target[held]=0
  protect=((Y<=ey+4)&(X>=ex-8))|(Y>max(8,ey+20));use=(placed>0)&~protect;target[use]=placed[use];target[protect& (body>0)]=body[protect&(body>0)]
  # Exact native casing includes its originally fitted fingertip in8columns.
  gunwindow=(X>=tmx)&(X<tmx+8)&(Y>=tmy-3)&(Y<=tmy+5);target[gunwindow]=bar[gunwindow]
  # Source palette/geometry is unchanged; discarded ROI texels are reported.
  Image.fromarray(target).save(out/f'before_{n:03}.png');Image.fromarray(placed).save(out/f'new_arm_module_{n:03}.png');Image.fromarray(held.astype(np.uint8)*255).save(out/f'folded_hand_remove_{n:03}.png');Image.fromarray(use.astype(np.uint8)*255).save(out/f'arm_mask_{n:03}.png');np.save(out/f'arm_source_map_{n:03}.npy',source_map)
  ly,lx=np.nonzero(target);records.append({'ref':n,'source_body_sha256':digest(bpath),'source_new_arm_sha256':digest(sp),'source_muzzle':[smx,smy],'target_muzzle':[tmx,tmy],'arm_translation':[dx,dy],'arm_polygon':poly,'old_arm_pixels_used':0,'original_case_pixels':int((bar>0).sum()),'alpha_components_8':label(target>0,np.ones((3,3)))[1],'result_leftmost':int(lx.min()-160),'body_pixels_changed':int(np.count_nonzero(body!=target)),'indexed_sha256':sha(target.tobytes()),'art_review_pending':True})
  rows.append((f'fire {n}',[('fixed new body',a.rgba(body,16)),('new arm full source',a.rgba(src,16)),('rigid arm / original gun candidate',a.rgba(target,16))]))
 for i in range(0,len(rows),4):helper.grid(rows[i:i+4],out/f'comparison_{i//4+1}.png',6)
 write(out/'registration.json',{'frames':records,'native_packed':False,'runtime_verified':False,'no_horizontal_arm_stretch':True,'scope':'Rigid whole new-arm placement trial; shoulder seam/source region and folded hand removal still require review.'});print(json.dumps(records))
if __name__=='__main__':main()
