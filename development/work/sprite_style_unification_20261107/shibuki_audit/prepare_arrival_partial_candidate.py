"""등장8 후보 입력 고정·재현·거부검사. 게임/활성 포인터를 쓰지 않는다."""
from pathlib import Path
import sys,json,shutil
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
from pack_ultimate_arrival_partial import build,P,PARENT,REFS,TD,SOURCE,MANIFEST
FINAL='3e55b972c007731a8446c8478336c6def303e0dc5ed4ab5d6a52856471327138'
D=H/'prepared_ultimate_arrival_partial01'
def ev(p):return {'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p.read_bytes())}
def validate(data,lk,read=lambda p:p.read_bytes()):
 need(sha(data)==PARENT,'Wrong parent');need(lk['parent_sha256']==PARENT and lk['candidate_sha256']==FINAL and lk['refs']==list(REFS),'Lock scope mismatch')
 for name,h in lk['files'].items():
  p=(ROOT/name).resolve();need(p.is_relative_to(ROOT.resolve()),'Input outside workspace');need(sha(read(p))==h,'Changed input '+name)
 return True
def main():
 need(not D.exists(),'Fresh prepared folder');data=P.read_bytes();expected=(H/'ultimate_arrival_pack02/PL02_U.ARC').read_bytes();need(sha(expected)==FINAL,'Candidate changed')
 paths=set();dirs=('ultimate_arrival_inputs01/page01','ultimate_arrival_inputs01/page02','ultimate_arrival_native01','ultimate_arrival_native02','ultimate_arrival_separate_inputs02','ultimate_arrival_separate_native01','ultimate_arrival_overhead_arms01','ultimate_arrival_overhead_arms_native01','ultimate_arrival_overhead_arm_inspection01','ultimate_arrival_overhead_arm_composed02','ultimate_arrival136_foot_contacts01','ultimate_arrival_common_probe03','ultimate_arrival_targets01')
 for folder in dirs:
  paths.update(p for p in(H/folder).iterdir()if p.is_file()and p.suffix in('.png','.json','.txt'))
 scripts=('prepare_ultimate_arrival_partial.py','pack_ultimate_arrival_partial.py','prepare_arrival_partial_candidate.py','register_ultimate_arrival.py','register_ultimate_arrival_separate.py','compose_arrival_overhead_arms.py','probe_ultimate_arrival_common.py','register_arrival136_feet.py','native_pose_pack.py','pack_shibuki_hurt.py','pack_air_targets_probe.py','repack_part_records_lossless.py')
 paths.update(H/n for n in scripts);paths.update((ROOT/'scripts'/n)for n in('prepare_shibuki_ultimate_production.py','overhaul_sprites_costume_pack.py','prepare_shibuki_armor_remaining.py'))
 meta=json.loads((TD/'manifest.json').read_text('utf8'));paths.update(ROOT/n for n in meta['source_files']);paths.update((P,P.parent/'FROZEN.json',H.parent/'zero_audit/shibuki_ultimate_arrival_relations01/report.json',H/'ultimate_arrival135_arms01/generation_failure.json'))
 need(all(p.exists()for p in paths),'Missing source file');lk={'parent_sha256':PARENT,'candidate_sha256':FINAL,'refs':list(REFS),'files':{p.relative_to(ROOT).as_posix():sha(p.read_bytes())for p in sorted(paths)}}
 validate(data,lk);D.mkdir();write(D/'SOURCE_LOCK.json',lk);runs=[]
 for i in range(3):
  validate(data,lk);new,report=build(data,lambda v:None);need(new==expected,'Reproduction differs');runs.append({'run':i+1,'sha256':sha(new),'whole_resource_exact':True});print(json.dumps({'reproduction':i+1,'sha256':sha(new)}),flush=True)
 rejected=[]
 def test(label,fn):
  try:fn()
  except (ValueError,FileNotFoundError)as e:rejected.append({'case':label,'error':str(e)});return
  raise ValueError('Invalid input accepted '+label)
 test('부모1바이트변조',lambda:validate(bytes([data[0]^1])+data[1:],lk));test('부모잘림',lambda:validate(data[:-1],lk));test('빈부모',lambda:validate(b'',lk))
 for k,v in(('parent_sha256','0'*64),('candidate_sha256','0'*64),('refs',[135])):test('입력잠금_'+k,lambda k=k,v=v:validate(data,{**lk,k:v}))
 chosen=[SOURCE/'after_138_indices.png',TD/'130_background_indices.png',TD/'136_effect_indices.png',H/'ultimate_arrival_overhead_arms01/generated.png',H/'pack_ultimate_arrival_partial.py',P.parent/'FROZEN.json']
 for target in chosen:
  def altered(p,target=target):
   b=p.read_bytes();return bytes([b[0]^1])+b[1:]if p==target.resolve()else b
  test('보호입력_'+target.name,lambda read=altered:validate(data,lk,read))
 validate(data,lk);need(len(rejected)==12,'Rejection coverage');(D/'PL02_U.ARC').write_bytes(expected)
 limitations=['135 국소편집은 도구 거부 이후 재시도하지 않았으며 부모 원시/조립/5층을 그대로 유지한 미완료 참조다.','136 발 모듈만 y+1 강체 등록했다. 눈/무릎/상부 종아리는 동일하며 실제 게임 바닥 접촉은 아직 미검증이다.','130/131은 기존 공통 실루엣 정책을 유지한다. 136/139는 단순 별칭이 아닌 별도 원화다.','원MIPS/독립검사/루트 최종미술/실기는 이 초기 준비 보고에 포함하지 않는다.']
 report.update(source_lock_sha256=sha((D/'SOURCE_LOCK.json').read_bytes()),reproduction_runs=runs,rejection_count=len(rejected),rejections=rejected,limitations=limitations)
 write(D/'verification.json',report)
 proposal={'project':'ver_buki_riko','baseline_sha256':'21bee159a1267d56561d4fa15c99ec652780af782fe08a433859c9eb7676099a','files':{'PL02_U.ARC':{'path':(D/'PL02_U.ARC').relative_to(ROOT).as_posix(),'before':'98ab01e8581d6bca15d75d703e7605899f2a871e042f5b09b13c5f2e07cf132e','after':FINAL}},'sequential_parent':ev(P),'targets':ev(TD/'manifest.json'),'target_lock':ev(D/'SOURCE_LOCK.json'),'source_art':lk['files'],'selected_refs':list(REFS),'preserved_ref135':True,'scope':'Ultimate 등장8 부분 준비본. 미완료135 제외. 기존 은행/entry/LBA/EXE/음향/팔레트 경계 보존.','frozen':False,'runtime_verified':False}
 write(D/'proposal.json',proposal)
 write(D/'PREPARED_LOCK.json',{'files':{p.name:sha(p.read_bytes())for p in sorted(D.iterdir())if p.is_file()}})
 write(H/'ultimate_arrival_partial_components.json',{'project':'ver_buki_riko','source_bin':'out/ver_buki_riko/sprite_style_unification_20261107_v18/shibuki_riko.bin','source_sha256':'b0bc7e3105966fbca46bb28b6dd8e2ae5daf4b785cd1ffb203b0bdfde6bfcc88','resources':{'PL02_U.ARC':{'path':(D/'PL02_U.ARC').relative_to(ROOT).as_posix(),'before':PARENT,'after':FINAL}},'checkpoint_only':True})
 print(json.dumps({'prepared':ev(D/'proposal.json'),'candidate':FINAL,'source_lock':ev(D/'SOURCE_LOCK.json'),'reproduction':3,'rejections':12}))
if __name__=='__main__':main()
