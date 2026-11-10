"""네 새 탑승 몸체와 원Y 별칭9개를 양폼 65층으로 만든다."""
from pathlib import Path
import json,sys
import numpy as np
from PIL import Image
D=Path(__file__).resolve().parent;N=D.parent;ROOT=N.parents[2];sys.path[:0]=[str(ROOT),str(N/'native_restore')]
from preview_restore import Archive,digest,sha,write,need,helper
PBS=(0,5,6,7,8);KEYS=(162,166,170,174)
DY={162:0,163:1,164:3,165:-1,166:0,167:1,168:3,169:-1,170:0,171:1,172:2,173:-1,174:0}
PARENT=N/'ultimate_special_finish_repaint/packed_special_candidate_v1/PL02_U.ARC'
BEFORE='56a3aeb489229d85bb72205bd14f866b4444ff5daa8e1bc7f91c82e9b3c46fc0'
def comp(a,l,mask,arm=2):
 z=a.rgba(l[0])
 for pb,bit in((8,8),(5,1),(7,4),(6,2)):
  if mask&bit:z.alpha_composite(a.rgba(l[pb],32 if pb==7 and arm==2 else 16))
 return z
def main():
 need(digest(PARENT)==BEFORE,'동결 부모');fp=PARENT.parent/'FROZEN.json';need(json.loads(fp.read_text('utf8'))['frozen'],'부모 동결');a=Archive(PARENT.read_bytes());oldmeta=json.loads((D/'a_inputs_v1/manifest.json').read_text('utf8'));old=Archive((ROOT/oldmeta['parent_arc']).read_bytes())
 for n in DY:
  for pb in PBS:need(np.array_equal(a.layer(n,pb)[0],old.layer(n,pb)[0]),'입력 부모 이후 탑승그림 불변')
 src=D/'common_probe_v2';out=D/'targets_v1';out.mkdir(exist_ok=False);rows=[];targets={};frames=[]
 for key in KEYS:
  b=np.array(Image.open(src/f'before_{key:03}_indices.png'));v=np.array(Image.open(src/f'after_{key:03}_indices.png'));need(not np.any((v>0)&(b==0)),'후폼 알파 포함');pc=np.array([a.words[i]!=a.words[i+16]for i in range(16)])[b];ls={0:v,5:np.where((b!=v)|pc,b,0).astype(np.uint8),6:np.zeros_like(v),7:np.zeros_like(v),8:np.zeros_like(v)}
  for n in ([key]if key==174 else range(key,key+4)):
   dy=DY[n];layers={pb:np.roll(z,dy,0)for pb,z in ls.items()};targets[str(n)]={str(pb):sha(z.tobytes())for pb,z in layers.items()}
   for pb,z in layers.items():Image.fromarray(z).save(out/f'layer{pb}_{n:03}.png')
   for mask in range(32):
    for arm in(1,2):need(comp(a,layers,mask,arm).tobytes()==a.rgba(np.roll(b if mask&1 else v,dy,0),16 if mask&1 else 0).tobytes(),'부분 아머 32/팔2 정확')
   frames.append({'ref':n,'source_key':key,'translation':[0,dy],'layer_hashes':targets[str(n)]});rows.append((str(n),[('old jacket',a.composite(n,15)[0]),('new jacket',comp(a,layers,15)),('old bare',a.composite(n)[0]),('new bare',comp(a,layers,0))]))
 for i in range(0,len(rows),3):helper.grid(rows[i:i+3],out/f'comparison_{i//3+1}.png',5)
 ep=N.parent/'zero_audit/nana_ultimate_vehicle_relations01/conclusions.json';write(out/'manifest.json',{'parent_arc':PARENT.relative_to(ROOT).as_posix(),'parent_arc_sha256':BEFORE,'parent_frozen_sha256':digest(fp),'refs':list(DY),'new_authored_body_refs':list(KEYS),'derived_y_refs':[n for n in DY if n not in KEYS],'frames':frames,'targets':targets,'common_manifest':(src/'manifest.json').relative_to(ROOT).as_posix(),'common_manifest_sha256':digest(src/'manifest.json'),'direct_rgba_combinations':832,'derivation_policy':'원US 양폼/현재 재킷의 Y별칭9개를 새 양폼 공통정책으로 적용한다. 현재 맨팔의 역사 개별등록 차이를 exact 복원한 것은 아니다.','source_relation_evidence':{'path':ep.relative_to(ROOT).as_posix(),'sha256':digest(ep)},'native_packed':False,'runtime_verified':False});print(json.dumps({'layers':65,'RGBA':832,'sha256':digest(out/'manifest.json')}))
if __name__=='__main__':main()
