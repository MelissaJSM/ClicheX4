"""Ultimate90/91의 공동몸과 의상차이를 실제5층으로 분리한다."""
from pathlib import Path
import json,sys
import numpy as np
from PIL import Image
D=Path(__file__).resolve().parent;N=D.parent;ROOT=N.parents[2];sys.path[:0]=[str(ROOT),str(N/'native_restore')]
from preview_restore import Archive,digest,sha,write,need,helper
def comp(a,l,mask,arm=2):
 z=a.rgba(l[0])
 for pb,bit in((8,8),(5,1),(7,4),(6,2)):
  if mask&bit:z.alpha_composite(a.rgba(l[pb],32 if pb==7 and arm==2 else 16))
 return z
def main():
 p=N/'ultimate_standing_repaint/packed_standing_candidate_v1/PL02_U.ARC';need(digest(p)=='0e69e9e3823c95bfce5b10746f77c587cd6f9e177cdd69b04938e868f3b77331','동결부모');fp=p.parent/'FROZEN.json';need(json.loads(fp.read_text('utf8'))['frozen'],'부모동결');a=Archive(p.read_bytes());src=D/'common_probe_v2';meta=json.loads((src/'manifest.json').read_text('utf8'));out=D/'targets_v1';out.mkdir(exist_ok=False);rows=[];targets={}
 for n in(90,91):
  b=np.array(Image.open(src/f'before_{n:03}_indices.png'));v=np.array(Image.open(src/f'after_{n:03}_indices.png'));need(not np.any((v>0)&(b==0)),'재킷밖맨팔없음');pc=np.array([a.words[i]!=a.words[i+16]for i in range(16)])[b];ls={0:v,5:np.where((b!=v)|pc,b,0).astype(np.uint8),6:np.zeros_like(v),7:np.zeros_like(v),8:np.zeros_like(v)}
  for pb,z in ls.items():Image.fromarray(z).save(out/f'layer{pb}_{n:03}.png')
  for mask in range(32):
   for arm in(1,2):need(comp(a,ls,mask,arm).tobytes()==a.rgba(b if mask&1 else v,16 if mask&1 else 0).tobytes(),'32마스크2팔')
  targets[str(n)]={str(pb):sha(z.tobytes())for pb,z in ls.items()};rows.append((str(n),[('old before',a.composite(n,15)[0]),('new before',comp(a,ls,15)),('old after',a.composite(n)[0]),('new after',comp(a,ls,0))]))
 helper.grid(rows,out/'comparison.png',6);write(out/'manifest.json',{'parent_arc':p.relative_to(ROOT).as_posix(),'parent_arc_sha256':digest(p),'parent_frozen_sha256':digest(fp),'refs':[90,91],'new_authored_body_refs':[90,91],'targets':targets,'common_manifest':(src/'manifest.json').relative_to(ROOT).as_posix(),'common_manifest_sha256':digest(src/'manifest.json'),'direct_rgba_combinations':128,'weapon_policy':'90 새 사선권총/손 원화 공유.91 정본85의20texel을X−2한기존기본/포스수용모듈위치.88..91은차지발사후총을올렸다내리는연결동작이며91의새탄환발사점검증으로부르지않음.','source_policy_clarification':'common_probe_v2/manifest의 실제원91수평총구 문구는 위치정책을과대해석한표현이다. 원US발사점수치/단독91발사증명없고 이번최종명세로범위를정정한다.','native_packed':False,'runtime_verified':False});print(json.dumps({'layers':10,'RGBA':128,'sha256':digest(out/'manifest.json')}))
if __name__=='__main__':main()
