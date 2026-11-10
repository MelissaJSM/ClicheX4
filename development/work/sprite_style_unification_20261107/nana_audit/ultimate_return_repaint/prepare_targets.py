"""새 귀환156과 입증된157 외곽/158 빛 파생을15층으로 준비한다."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image
from scipy.ndimage import binary_dilation
D=Path(__file__).resolve().parent;N=D.parent;ROOT=N.parents[2]
sys.path[:0]=[str(ROOT),str(N/'native_restore')]
from preview_restore import Archive,digest,sha,write,need,helper
PBS=(0,5,6,7,8);REFS=(156,157,158)
ENERGY_MAP=np.array([0,5,6,7,8,5,6,7,8,9,8,9,13,13,9,9],np.uint8)

def shift(z,dy):
 t=np.zeros_like(z);y,x=np.nonzero(z);need(((y+dy>=0)&(y+dy<z.shape[0])).all(),'수직경계');t[y+dy,x]=z[y,x];return t
def full(a,n):
 z=a.layer(n)[0].copy()
 for pb in(8,5,7,6):q=a.layer(n,pb)[0];z[q>0]=q[q>0]
 return z
def aura(body):
 m=body>0;i=binary_dilation(m,np.ones((3,3)),iterations=1);o=binary_dilation(m,np.ones((3,3)),iterations=2)
 return np.where(m,body,np.where(i,7,np.where(o,13,0))).astype(np.uint8)
def composite(a,ls,mask=0,arm=2):
 im=a.rgba(ls[0])
 for pb,bit in((8,8),(5,1),(7,4),(6,2)):
  if mask&bit:im.alpha_composite(a.rgba(ls[pb],32 if pb==7 and arm==2 else 16))
 return im
def split(before,after):
 need(not np.any((after>0)&(before==0)),'후폼알파포함')
 return{0:after,5:np.where((before!=after)|(before==15),before,0).astype(np.uint8),6:np.zeros_like(after),7:np.zeros_like(after),8:np.zeros_like(after)}

def main():
 out=D/'final_targets_v1';out.mkdir(exist_ok=False);p=N/'ultimate_victory_repaint/packed_victory_candidate_v1/PL02_U.ARC';a=Archive(p.read_bytes());need(digest(p)=='b7dcf46dba35084265e8b32529d7a4d072108ed201a60ba4f17fcc71494aa1c5','부모')
 hp=ROOT/'work/overhaul_20261105/sprites/ver_rin_nana/baseline/PL02_U.ARC';h=Archive(hp.read_bytes());energy=h.layer(159)[0];need(int((energy>0).sum())==1875,'역사 에너지1875');need(np.array_equal(a.layer(159)[0],energy),'159원표시보존')
 # 현재 before의 역사 규칙을 새 몸 적용 전에 자체 재현한다.
 need(np.array_equal(aura(shift(full(a,156),-1)),full(a,157)),'부모157재킷규칙')
 expected=np.where(shift(full(a,156),-10)>0,ENERGY_MAP[shift(full(a,156),-10)%16],energy).astype(np.uint8)
 need(np.array_equal(expected,full(a,158)),'부모158재킷규칙')
 src=D/'costume_pair_probe_v2';body={}
 for form in('before','after'):
  z=np.array(Image.open(src/f'{form}_156.png'));body[form,156]=z;body[form,157]=aura(shift(z,-1));moved=shift(z,-10);body[form,158]=np.where(moved>0,ENERGY_MAP[moved%16],energy).astype(np.uint8)
 Image.fromarray(energy).save(out/'original_energy159_indices.png');rows=[];hashes={};rules=[]
 for n in REFS:
  b,v=body['before',n],body['after',n];ls=split(b,v);hashes[str(n)]={}
  for pb,z in ls.items():Image.fromarray(z).save(out/f'layer{pb}_{n:03}.png');hashes[str(n)][str(pb)]=sha(z.tobytes())
  for form,z in(('before',b),('after',v)):Image.fromarray(z).save(out/f'{form}_{n:03}_indices.png')
  need(composite(a,ls,15).tobytes()==a.rgba(b,16).tobytes(),'전폼RGBA');need(composite(a,ls,0).tobytes()==a.rgba(v).tobytes(),'후폼RGBA')
  rows.append((f'return {n}',[('old before',a.composite(n,15)[0]),('new before',composite(a,ls,15)),('old after',a.composite(n)[0]),('new after',composite(a,ls))]))
  if n==157:
   for form in('before','after'):
    z=shift(body[form,156],-1);fx=np.where(z==0,body[form,n],0).astype(np.uint8);Image.fromarray(fx).save(out/f'{form}_aura157.png');need(np.array_equal(body[form,n][z>0],z[z>0]),'157몸체내부exact');rules.append({'ref':157,'form':form,'translation':[0,-1],'aura_pixels':int((fx>0).sum()),'body_interior_exact':True,'old_guard_cell_reapplied':False})
  if n==158:
   for form in('before','after'):
    moved=shift(body[form,156],-10);need(np.array_equal(body[form,n][moved==0],energy[moved==0]),'빛비몸영역exact');rules.append({'ref':158,'form':form,'translation':[0,-10],'mapping':ENERGY_MAP.tolist(),'historical_energy_pixels':1875,'visible_energy_outside_body':int(np.count_nonzero(energy*(moved==0))),'old_body_alpha_clipped':False})
 for i,row in enumerate(rows,1):helper.grid([row],out/f'comparison_{i}.png',7)
 write(out/'manifest.json',{'parent_arc_sha256':digest(p),'refs':list(REFS),'new_art_body_refs':[156],'derived_body_effect_refs':[157,158],'body_source_manifest':(src/'manifest.json').relative_to(ROOT).as_posix(),'body_source_manifest_sha256':digest(src/'manifest.json'),'historical_arc':hp.relative_to(ROOT).as_posix(),'historical_arc_sha256':digest(hp),'historical_energy_sha256':sha(energy.tobytes()),'targets':hashes,'rules':rules,'preserved_related_refs':[159,160,161,0,142,88,89],'source_policy':'157은 각 새156 y−1의Chebyshev1/2 외곽색7/13, 기존 맨팔guard1셀 자동복사하지 않음.158은각새156 y−10·수용에너지맵과역사159빛1875px,옛몸알파로자르지않음.','native_packed':False,'runtime_verified':False});print(json.dumps({'layers':15,'manifest_sha256':digest(out/'manifest.json'),'rules':rules}))
if __name__=='__main__':main()
