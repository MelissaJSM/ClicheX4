"""새95/98 양폼과 X+1 파생96/99의 실제5층을 만든다."""
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
 p=N/'ultimate_recoil_repaint/packed_recoil_candidate_v1/PL02_U.ARC';need(digest(p)=='ce61617f541fd59a5a3ab0b26bba6ce88cc7740bf5f9d4719c9acb129783c8d0','동결부모');fp=p.parent/'FROZEN.json';need(json.loads(fp.read_text('utf8'))['frozen'],'부모동결');a=Archive(p.read_bytes());src=D/'common_probe_v2';out=D/'targets_v1';out.mkdir(exist_ok=False);rows=[];targets={}
 for n in(95,98):
  b=np.array(Image.open(src/f'before_{n:03}_indices.png'));v=np.array(Image.open(src/f'after_{n:03}_indices.png'));need(not np.any((v>0)&(b==0)),'재킷밖맨팔없음');pc=np.array([a.words[i]!=a.words[i+16]for i in range(16)])[b];base={0:v,5:np.where((b!=v)|pc,b,0).astype(np.uint8),6:np.zeros_like(v),7:np.zeros_like(v),8:np.zeros_like(v)}
  for dx in(0,1):
   nn=n+dx;ls={pb:np.roll(z,dx,1)for pb,z in base.items()}
   for pb,z in ls.items():Image.fromarray(z).save(out/f'layer{pb}_{nn:03}.png')
   for mask in range(32):
    for arm in(1,2):need(comp(a,ls,mask,arm).tobytes()==a.rgba(np.roll(b if mask&1 else v,dx,1),16 if mask&1 else 0).tobytes(),'32마스크2팔')
   targets[str(nn)]={str(pb):sha(z.tobytes())for pb,z in ls.items()};rows.append((str(nn),[('old before',a.composite(nn,15)[0]),('new before',comp(a,ls,15)),('old after',a.composite(nn)[0]),('new after',comp(a,ls,0))]))
 for i in range(0,4,2):helper.grid(rows[i:i+2],out/f'comparison_{i//2+1}.png',6)
 ep=N.parent/'zero_audit/nana_ultimate_special_relations01/report.json';write(out/'manifest.json',{'parent_arc':p.relative_to(ROOT).as_posix(),'parent_arc_sha256':digest(p),'parent_frozen_sha256':digest(fp),'refs':[95,96,98,99],'new_authored_body_refs':[95,98],'derived_x_plus1_refs':[96,99],'targets':targets,'common_manifest':(src/'manifest.json').relative_to(ROOT).as_posix(),'common_manifest_sha256':digest(src/'manifest.json'),'direct_rgba_combinations':256,'weapon_policy':'95는 새사선권총의 실제총열/그립.98은 정본85 20texel X−3,Y+1 + 새손 피부가림2셀. 실제 발사코드 추가검증은별도.','derivation_policy':'원US/현재before의95→96,98→99 X+1 관계를 새양폼 공통정책으로 적용. 현재after의118/117셀 차이를 그대로 복원한 것은 아님.','relation_evidence':{'path':ep.relative_to(ROOT).as_posix(),'sha256':digest(ep)},'native_packed':False,'runtime_verified':False});print(json.dumps({'layers':20,'RGBA':256,'sha256':digest(out/'manifest.json')}))
if __name__=='__main__':main()
