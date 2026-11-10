"""라이징 새 기본/포스 전신을 실제 파츠 소유에 분리하는 검토본."""
from pathlib import Path
import sys,json,argparse
import numpy as np
from PIL import Image
from scipy.ndimage import label
D=Path(__file__).resolve().parent;N=D.parent;ROOT=N.parents[2]
sys.path[:0]=[str(ROOT),str(N/'native_restore')]
from preview_restore import Archive,sha,digest,need,write,helper
Y,X=np.indices((384,384));Y-=160;X-=160
EYES={100:(-4,-16),101:(-4,-20),102:(-4,-13),103:(-4,-14),104:(-4,-17),231:(-4,-12)}
PALM={100:(-12,-11),101:(-10,-31),102:(-10,-25),103:(9,-19),104:(7,-27),231:(-10,-22)}
LOWER={100:3,101:4,102:6,103:6,104:5,231:7}

def composite(a,layers,mask,arm=2):
 im=a.rgba(layers[0])
 for bit,pb in((8,8),(1,5),(4,7),(2,6)):
  if mask&bit:im.alpha_composite(a.rgba(layers[pb],32 if pb==7 and arm==2 else 16))
 return im

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--v2',action='store_true');args=ap.parse_args();out=D/('joint_layers_probe_v2'if args.v2 else'joint_layers_probe_v1');out.mkdir(exist_ok=False);parent=N/'dash_repaint/packed_dash_candidate_v1/PL00_U.ARC';a=Archive(parent.read_bytes());need(sha(a.data)=='cbe6996784a901363abab2d93c81dca49ade8574ac0d5c378af398651f2f6cfa','Parent');source=D/'common_legs_probe_v3';records=[];rows=[];parts=[]
 for n,(ex,ey)in EYES.items():
  b=np.array(Image.open(source/f'base_{n:03}_indices.png'));f=np.array(Image.open(source/f'fourth_authored_contacts_{n:03}_indices.png'));full=np.where(f,f,b).astype(np.uint8)
  # The veil has historically belonged to the leg costume, while its upper
  # attachment belongs to the head. Both are newly authored in this candidate.
  head=(Y<ey+4)&((X>=ex-3)|(Y<ey))
  leg=(Y>=LOWER[n])|((X>=ex+14)&(Y>=ey+4))
  front=(X<ex+3)&(Y>=ey)&(Y<ey+17)&~head
  owner=np.full(b.shape,6,np.uint8);owner[leg]=8;owner[head]=5;owner[front]=7
  shoulder=np.array([2 if n in(103,104)else-4,ey+6],float);palm=np.array(PALM[n],float);v=palm-shoulder;t=np.clip(((X-shoulder[0])*v[0]+(Y-shoulder[1])*v[1])/float(v@v),0,1);dist=(X-shoulder[0]-t*v[0])**2+(Y-shoulder[1]-t*v[1])**2
  arm=(dist<=12)&((X>=1)if n in(103,104)else(X<=-6))
  owner[arm]=7
  # The isolated new fingers/weapon above each hand are part of the arm, even
  # when the arm rises above the hat. The canonical case itself is identical.
  cx,cy=PALM[n];owner[(X>=cx-4)&(X<=cx+4)&(Y<cy+2)]=7
  # The right low palm belongs to arms, not the rear-veil leg costume.
  right_hand=np.isin(full,(10,11,12,13))&(X>=ex+5)&(Y>=ey+7)&(Y<ey+16)
  owner[right_hand]=7
  semantic_boundary=[]
  if args.v2:
   # The actual authored veil tips attach through leg8 in the full costume.
   # Keep their pixels and change only their owner; otherwise head-only/body-
   # only creates an isolated dot at the straight preliminary partition.
   for tx,ty in {101:[(17,-17)],103:[(9,5)]}.get(n,[]):
    semantic_boundary.append({'world':[tx,ty],'index':int(full[ty+160,tx+160]),'before_owner':int(owner[ty+160,tx+160]),'after_owner':8,'meaning':'rear veil terminal texel'});owner[ty+160,tx+160]=8
  paldiff=np.array([a.words[i]!=a.words[16+i]for i in range(16)])[full]
  change=((full!=b)|((f>0)&paldiff))&(full>0)
  ls={0:b,**{pb:np.where(change&(owner==pb),full,0).astype(np.uint8)for pb in(5,6,7,8)}}
  rebuilt=b.copy()
  for pb in(8,5,7,6):rebuilt=np.where(ls[pb],ls[pb],rebuilt)
  need(np.array_equal(rebuilt,full),'Index reconstruction')
  actual=composite(a,ls,15);expected=a.rgba(b);expected.alpha_composite(a.rgba(f,16))
  # Arm2 may deliberately use its distinct row; record and inspect it separately.
  need(np.array_equal(np.array(composite(a,ls,15,1)),np.array(expected)),'Native CLUT1 reconstruction')
  for ref in((231,232)if n==231 else(n,)):
   for pb,z in ls.items():Image.fromarray(z).save(out/f'layer{pb}_{ref:03}.png')
   Image.fromarray(owner).save(out/f'owner_{ref:03}.png');actual.save(out/f'full_{ref:03}.png')
   records.append({'ref':ref,'source_ref':n,'base_sha256':sha(b.tobytes()),'full_rgba_sha256':sha(actual.tobytes()),'layers':{str(pb):sha(ls[pb].tobytes())for pb in(5,6,7,8)},'owner_counts':{str(pb):int((ls[pb]>0).sum())for pb in(5,6,7,8)},'base_components':int(label(b>0,np.ones((3,3)))[1]),'full_components':int(label(full>0,np.ones((3,3)))[1]),'new_base_visible_outside_fourth':int(((b>0)&(f==0)).sum()),'semantic_owner_corrections':semantic_boundary,'old_bitmap_reused':False})
  rows.append((f'Rising {n}',[('basic idle',a.composite(0)[0]),('new base',a.rgba(b)),('Fourth idle',a.composite(0,15)[0]),('new full arm2',actual),('new full arm1',composite(a,ls,15,1))]))
  parts.append((f'partial {n}',[('head only',composite(a,ls,1)),('body only',composite(a,ls,2)),('arm only',composite(a,ls,4)),('leg only',composite(a,ls,8)),('body+leg',composite(a,ls,10))]))
 for i in range(0,len(rows),2):
  helper.grid(rows[i:i+2],out/f'comparison_{i//2+1}.png',6);helper.grid(parts[i:i+2],out/f'partial_{i//2+1}.png',6)
 write(out/'manifest.json',{'source_arc':parent.relative_to(ROOT).as_posix(),'source_arc_sha256':sha(a.data),'source_common_manifest_sha256':digest(source/'manifest.json'),'frames':records,'scope':'새 라이징7참조의5층 후보. 큰 뒤베일 leg8/상단접점 head5의 기존 정책 유지, 고정총과 새손은arm7. 기본 새머릿결이 포스 베일 바깥에 보이는 부분은 신규원화이며 옛bitmap 재사용 없음. 부분조합의 미술검토/패킹/실기 전.','native_packed':False,'runtime_verified':False});print(json.dumps(records))
if __name__=='__main__':main()
