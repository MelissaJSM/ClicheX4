"""같은 색인 픽셀의 공유 단위를 탐색한다. 그림과 게임 자원은 변경하지 않는다."""
from pathlib import Path
import sys,json,struct,hashlib
import numpy as np
from PIL import Image
D=Path(__file__).resolve().parent;W=D.parent;ROOT=W.parents[1];H=W/'shibuki_audit'
sys.path[:0]=[str(ROOT),str(H),str(W/'nana_audit/native_restore')]
from native_pose_pack import need,Archive
from scripts.prepare_shibuki_armor_remaining import pack_many_patterns
from scripts.prepare_shibuki_ultimate_production import repack_parts
from repack_part_records_lossless import repack as global_parts
from pack_shibuki_hurt import repack_fixed_global
from src.psx_compress import encode_stream
sha=lambda b:hashlib.sha256(b).hexdigest();PBS=(0,5,6,7,8)
def pieces(images,minimum):
 unique=[];lookup=[]
 for a in images:
  k=next((i for i,b in enumerate(unique)if np.array_equal(a,b)),None)
  if k is None:k=len(unique);unique.append(a.copy())
  lookup.append(k)
 residual=[a.copy()for a in unique];result=[];owners=[]
 for _ in range(64):
  candidates=[]
  for i,a in enumerate(residual):
   for j in range(i+1,len(residual)):
    b=residual[j];m=(a==b)&(a>0);area=int(m.sum())
    if area<minimum:continue
    yy,xx=np.nonzero(m)
    if area/((yy.max()-yy.min()+1)*(xx.max()-xx.min()+1))<.25:continue
    candidates.append((area,i,j,m))
  if not candidates:break
  _,i,j,m=max(candidates,key=lambda q:q[:3]);p=np.where(m,residual[i],0).astype(np.uint8)
  use=[k for k,a in enumerate(residual)if np.array_equal(a[m],p[m])];result.append(p);owners.append(use)
  for k in use:residual[k][m]=0
 for k,a in enumerate(residual):
  if a.any():result.append(a);owners.append([k])
 return result,[[i for i,use in enumerate(owners)if k in use]for k in lookup]
def main():
 out=D/'sharing_probe03';out.mkdir(exist_ok=False);parent=H/'prepared_nova_strike_base01/PL00_U.ARC';a=Archive(parent.read_bytes())
 need(sha(parent.read_bytes())=='36d4d0293abc77052c476e0495f4f4542ca75471c7a149f200e4bdb8f4e1bd4e','Parent SHA')
 targets={(n,pb):np.array(Image.open(D/('body_layers_probe04'if n%2 else'shot_composed02')/f'layer{pb}_{n}.png'))[80:240,80:240]for n in range(221,231)for pb in PBS};reports=[]
 for minimum in(96,64,32,16):
  sub=out/f'area{minimum}';sub.mkdir();raws={};counts={};changes={pb:{}for pb in PBS};groups=[];error=None
  try:
   for key in range(221,231,2):
    images=[targets[n,pb]for n in(key,key+1)for pb in PBS];pp,owners=pieces(images,minimum)
    nr,rr=pack_many_patterns(bytes(4096),32,pp,set(range(32))-{0,16},[24]*len(pp));assign=[[r for k in own for r in rr[k]]for own in owners]
    need(max(map(len,assign))<=24,'Part cap24')
    for j,n in enumerate((key,key+1)):
     raws[n]=nr;counts[n]=32
     for pb,parts in zip(PBS,assign[j*5:(j+1)*5]):changes[pb][n]=b''.join(struct.pack('<BBbb',flag,t,x-80,y-80)for t,x,y,flag in parts)
    (sub/f'{key}.raw').write_bytes(nr);groups.append({'refs':[key,key+1],'sha256':sha(nr),'encoded_bytes':len(encode_stream(nr)),'assignments':assign,'parts':list(map(len,assign))})
   nc=a.c;slacks={}
   for pb,q in changes.items():
    try:nc,slacks[pb]=repack_parts(nc,pb,q)
    except ValueError:nc,slacks[pb],_=global_parts(nc,pb,q)
   try:_,capacity=repack_fixed_global(a,raws,counts)
   except ValueError as e:capacity={'fits':False,'reason':str(e)}
  except Exception as e:error=str(e);slacks={};capacity=None
  report={'minimum':minimum,'groups':groups,'total_encoded':sum(g['encoded_bytes']for g in groups),'composition_slack':slacks,'capacity':capacity,'error':error,'game_written':False}
  (sub/'recipe.json').write_text(json.dumps(report,indent=2)+'\n','utf8');reports.append(report)
  print(json.dumps({k:report[k]for k in('minimum','total_encoded','capacity','error','composition_slack')}),flush=True)
 (out/'report.json').write_text(json.dumps({'trials':reports,'parent_sha256':sha(parent.read_bytes()),'game_written':False},indent=2)+'\n','utf8')
if __name__=='__main__':main()
