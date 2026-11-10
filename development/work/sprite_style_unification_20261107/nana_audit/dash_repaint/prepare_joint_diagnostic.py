"""Unapproved art diagnostic for packing/parts; never an integration proposal."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image
from scipy.ndimage import label
D=Path(__file__).resolve().parent; ROOT=D.parents[3]
sys.path[:0]=[str(D),str(D.parent/'native_restore')]
from preview_restore import Archive,sha,need,write,helper
from prepare_next_guides import body_path
from register_arm_reach_joint import OLD_HAND_BOXES
REFS=(67,69,71,75,77,79,81,83,93,94)
START={67:10,69:13,71:16,75:16,77:12,79:12,81:7,83:8,93:9,94:3}
def load(p):return np.array(Image.open(p))
def main():
 plan=json.loads((D/'inputs.json').read_text('utf8'));a=Archive((ROOT/plan['parent_arc']).read_bytes());out=D/'joint_layers_diagnostic_v2';need(not out.exists(),'Fresh diagnostic');out.mkdir();Y,X=np.indices((384,384));x=X-160;y=Y-160;reports=[];rows=[];alllayers={}
 for n in REFS:
  original=load(body_path(n));bd=D/('common_contact_refine_v1'if n in(79,93)else'common_silhouette_probe_v4');b=original.copy()if n in(71,75)else load(bd/f'base_{n:03}.png');fd=D/('fourth_folded_registered_v2'if n in(71,75)else'common_contact_refine_v1'if n in(79,93)else'fourth_contacts_probe_v2');f=load(fd/f'fourth_{n:03}.png');changed=b!=original;q=next(q for q in plan['frames']if q['ref']==n);ex,ey=[int(np.floor(v))for v in q['eye']];display={}
  for ref in((n,n+1)if n<93 else(n,)):
   body=b.copy();costume=f.copy();arm=None
   if ref%2==0 and ref<93:
    sd=D/'firing_reach_joint_v3';body=load(sd/f'merged_{ref:03}.png');body[changed]=b[changed];arm=load(sd/f'new_sleeve_{ref:03}.png');head=(x>=ex-2)&(y<=ey+5)
    remove=(((x<=ex+2)&(y>=ey+8)&(y<ey+15))|((x<=ex-2)&(y>=ey+3)&(y<ey+8)))&~head
    if ref in OLD_HAND_BOXES:
     x0,y0,x1,y1=OLD_HAND_BOXES[ref];remove|=(x>=x0)&(x<x1)&(y>=y0)&(y<y1)&~head
    costume[remove]=0;costume[arm>0]=arm[arm>0]
    gun=load(D/'fire_constraints'/f'barrel_{ref:03}.png');gy,gx=np.nonzero(gun);win=(X>=gx.min())&(X<=gx.min()+7)&(Y>=gy.min())&(Y<=gy.max());costume[win]=gun[win];body[win]=gun[win]
   full=np.where(costume,costume,body).astype(np.uint8);head=(y<ey+4)&((x>=ex-3)|(y<ey));leg=(y>=START[n])|((x>=ex+14)&(y>=ey+4));front=(x<ex+3)&(y>=ey)&(y<ey+17)&~head
   owner=np.full((384,384),6,np.uint8);owner[leg]=8;owner[head]=5;owner[front]=7
   if arm is not None:owner[arm>0]=7
   if n in(93,94):
    shoulder=np.array([ex+7,ey+5]);palm=np.array([5,-19]if n==93 else[13,-12]);v=palm-shoulder;t=np.clip(((x-shoulder[0])*v[0]+(y-shoulder[1])*v[1])/float(v@v),0,1);dist=(x-shoulder[0]-t*v[0])**2+(y-shoulder[1]-t*v[1])**2;owner[(dist<8)&(x>ex+5)]=7
   pc=np.array([a.words[i]!=a.words[16+i]for i in range(16)])[full];diff=((full!=body)|((costume>0)&pc))&(full>0);layers={0:body,**{pb:np.where(diff&(owner==pb),full,0).astype(np.uint8)for pb in(5,6,7,8)}}
   merged=body.copy()
   for pb in(8,5,7,6):merged=np.where(layers[pb],layers[pb],merged)
   need(np.array_equal(merged,full),'Layer reconstruction');alllayers[ref]=layers
   for pb,z in layers.items():Image.fromarray(z).save(out/f'layer{pb}_{ref:03}.png')
   reports.append({'ref':ref,'base_sha256':sha(body.tobytes()),'full_sha256':sha(full.tobytes()),'layers':{str(pb):sha(z.tobytes())for pb,z in layers.items()if pb},'unresolved_folded_leg':n in(71,75),'full_components':int(label(full>0,np.ones((3,3)))[1])});display[ref]=[a.rgba(body),a.rgba(merged,16)]
  cols=[('새 기본',display[n][0]),('새 포스',display[n][1])]
  if n<93:cols.extend([('기본 사격',display[n+1][0]),('포스 사격',display[n+1][1])])
  else:cols.extend([('기본 대기',a.composite(0)[0]),('포스 대기',a.composite(0,15)[0])])
  rows.append((str(n),cols))
 for ref,bodyref in((73,71),(74,72)):
  layers={pb:z.copy()for pb,z in alllayers[bodyref].items()};fx=load(D/'effects'/f'effect_{ref:03}.png');layers[0]=np.where(fx,fx,layers[0]).astype(np.uint8);full=layers[0].copy()
  for pb in(8,5,7,6):full=np.where(layers[pb],layers[pb],full)
  for pb,z in layers.items():Image.fromarray(z).save(out/f'layer{pb}_{ref:03}.png')
  reports.append({'ref':ref,'base_sha256':sha(layers[0].tobytes()),'full_sha256':sha(full.tobytes()),'layers':{str(pb):sha(z.tobytes())for pb,z in layers.items()if pb},'effect_source_ref':ref,'unresolved_folded_leg':True})
 for i in range(0,len(rows),3):helper.grid(rows[i:i+3],out/f'comparison_{i//3+1}.png',6)
 write(out/'manifest.json',{'source_arc_sha256':sha(a.data),'frames':reports,'ready_to_apply':False,'reason':'71/75 접점 미완료. 구조 패킹 검사용이며 최종 아트 아님.','native_packed':False,'runtime_verified':False})
 print(str(out))
if __name__=='__main__':main()
