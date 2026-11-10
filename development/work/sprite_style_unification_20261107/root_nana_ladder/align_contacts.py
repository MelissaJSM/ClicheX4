"""Register only the new art's limb regions; do not paint or restore old pixels."""
from pathlib import Path
import sys,json,hashlib,argparse
import numpy as np
from PIL import Image
from scipy.ndimage import label
D=Path(__file__).resolve().parent;W=D.parent;ROOT=W.parents[1];N=W/'nana_audit';sys.path[:0]=[str(ROOT),str(N/'native_restore')]
from preview_restore import Archive,helper
sha=lambda b:hashlib.sha256(b).hexdigest();read=lambda p:json.loads(p.read_text('utf8'))
m=read(D/'first_inputs01/manifest.json');a=Archive((ROOT/m['source_arc']).read_bytes());assert sha(a.data)==m['source_arc_sha256']
ap=argparse.ArgumentParser();ap.add_argument('--out',default='contact_registration01');ap.add_argument('--keep-grips',action='store_true');args=ap.parse_args()
out=(D/args.out).resolve();assert out.is_relative_to(D) and not out.exists();out.mkdir();rows=[];records=[]
for ref,page in ((143,1),(146,1),(144,2),(149,2),(151,3),(153,3),(154,4),(183,4)):
 for form,mask in (('base',0),('fourth',15)):
  src=D/('first_registered01' if page==1 else f'registered_page{page:02}')/f'{form}_{ref:03}_indices.png';z=np.array(Image.open(src));initial=z.copy();ops=[]
  def move(box,dx,dy,reason):
   x0,y0,x1,y1=box;patch=z[y0:y1,x0:x1].copy();n=int(np.count_nonzero(patch));z[y0:y1,x0:x1]=0
   target=z[y0+dy:y1+dy,x0+dx:x1+dx];occupied=(patch>0)&(target>0);under=int(np.count_nonzero(occupied));target[patch>0]=patch[patch>0]
   ops.append({'source_box':box,'translation':[dx,dy],'nonzero_source_pixels':n,'destination_overlap_pixels':under,'reason':reason})
  # Foot-tip registration uses complete new shoes, overlapping only the ankle.
  dy={143:-1,146:-1,144:-2,149:-3,151:-3,153:-2,154:0,183:(-1 if form=='base' else 0)}[ref]
  if dy:
   if ref==153:box=(154,164,165,174)
   elif ref==183:box=(160,184,167,193)
   else:box=(154,177,173,187)
   move(box,0,dy,'새 원화 신발의 발끝을 부모와 맞추는 국소 강체 등록. 몸체/머리 축척 없음.')
  if ref==143 and form=='fourth':move((144,132,153,142),0,1,'올린 손이1픽셀 높은 등록차 보정.')
  if ref==144 and not args.keep_grips:move((147,130,156,140),1,-1,'올린 손 위치의좌우/상하1픽셀 등록차 보정.')
  if ref==149 and form=='base' and not args.keep_grips:move((161,128,168,139),0,-1,'올린 손이1픽셀 낮은 등록차 보정.')
  if ref==153:
   move((143,159,153,169),2,-1,'왼쪽 손·소매를 기존 가로대 접점에 강체 등록.')
   move((167,159,177,169),-2,-1,'오른쪽 손·소매를 기존 가로대 접점에 강체 등록.')
  Image.fromarray(z).save(out/f'{form}_{ref:03}_indices.png');im=a.rgba(z,16 if mask else 0);im.save(out/f'{form}_{ref:03}_rgba.png')
  old=a.composite(ref,mask,2)[0];rows.append((f'{form} {ref}',[('old pose',old),('new fixed cell',a.rgba(initial,16 if mask else 0)),('new contact registered',im)]))
  records.append({'form':form,'ref':ref,'source':src.relative_to(ROOT).as_posix(),'source_sha256':sha(src.read_bytes()),'operations':ops,'old_bbox':old.getbbox(),'before_bbox':a.rgba(initial,16 if mask else 0).getbbox(),'after_bbox':im.getbbox(),'components8':int(label(z>0,np.ones((3,3)))[1]),'indices_sha256':sha(z.tobytes()),'rgba_sha256':sha(im.tobytes()),'old_art_pixels_copied':0,'whole_body_rescale':False})
for i in range(0,len(rows),4):helper.grid(rows[i:i+4],out/f'comparison_{i//4+1}.png',6)
(out/'registration.json').write_text(json.dumps({'source_arc_sha256':sha(a.data),'method':'새 원화 손발 영역의 정수 강체 이동. 그림 새로칠하기/옛 픽셀 복원/전신축척 없음.','frames':records,'visual_reviewed':False,'packed':False},ensure_ascii=False,indent=2)+'\n','utf8')
print(json.dumps([{'ref':r['ref'],'form':r['form'],'components':r['components8'],'bbox':r['after_bbox']}for r in records]))
