"""귀환3 고정 준비본과 원화 잠금/재현/입력거부 검증."""
from pathlib import Path
import sys,json
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
from pack_ultimate_return import build,P,PARENT,REFS,TD
FINAL='f40f33969d488af9db8c7d99b6bf4a78ad6e5542883bff63116fa26778de4cdc'
MANIFEST='729460a39ac02e48c8552a0f7e4e41033ce5636898207c922fd492995ccf8447'
D=H/'prepared_ultimate_return01'
def ev(p):return {'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p.read_bytes())}
def validate(data,lk,read=lambda p:p.read_bytes()):
 need(sha(data)==PARENT,'Wrong parent');need(lk['parent_sha256']==PARENT and lk['candidate_sha256']==FINAL and lk['refs']==list(REFS),'Lock scope mismatch')
 for name,h in lk['files'].items():
  p=(ROOT/name).resolve();need(p.is_relative_to(ROOT.resolve()),'Outside workspace');need(sha(read(p))==h,'Changed input '+name)
 return True
def main():
 need(not D.exists(),'Fresh prepared');data=P.read_bytes();expected=(H/'ultimate_return_pack02/PL02_U.ARC').read_bytes();need(sha(expected)==FINAL,'Candidate changed');meta=json.loads((TD/'manifest.json').read_text('utf8'));paths={ROOT/n for n in meta['source_files']};paths.update(p for p in TD.iterdir()if p.is_file());paths.update((P,P.parent/'FROZEN.json'))
 paths.update(H/n for n in ('pack_ultimate_return.py','prepare_return_candidate.py','native_pose_pack.py','pack_shibuki_hurt.py','repack_part_records_lossless.py','pack_dash_complete.py','prepare_lowhp_final.py'))
 paths.update(ROOT/'scripts'/n for n in ('prepare_shibuki_ultimate_production.py','overhaul_sprites_costume_pack.py','prepare_shibuki_armor_remaining.py','prepare_riko_ui.py','export_x_consistency.py'));paths.update(ROOT/'src'/n for n in ('psx_player.py','psx_ui_atlas.py'))
 lk={'parent_sha256':PARENT,'candidate_sha256':FINAL,'refs':list(REFS),'files':{p.relative_to(ROOT).as_posix():sha(p.read_bytes())for p in sorted(paths)}};validate(data,lk);D.mkdir();write(D/'SOURCE_LOCK.json',lk);runs=[]
 for i in range(3):
  validate(data,lk);new,proof=build(data,MANIFEST);need(new==expected,'Reproduction differs');runs.append({'run':i+1,'sha256':sha(new),'whole_resource_exact':True});print(json.dumps({'run':i+1,'exact':True}),flush=True)
 rejected=[]
 def test(name,fn):
  try:fn()
  except(ValueError,FileNotFoundError)as e:rejected.append({'case':name,'error':str(e)});return
  raise ValueError('Invalid input accepted '+name)
 test('부모1바이트',lambda:validate(bytes([data[0]^1])+data[1:],lk));test('부모잘림',lambda:validate(data[:-1],lk));test('빈부모',lambda:validate(b'',lk))
 for k,v in (('parent_sha256','0'*64),('candidate_sha256','0'*64),('refs',[159])):test('잠금_'+k,lambda k=k,v=v:validate(data,{**lk,k:v}))
 for target in (H/'ultimate_return_inputs01/generated.png',H/'ultimate_return_arm_edit02/generated.png',H/'ultimate_return_contacts02/before_156_indices.png',TD/'historical159_indices.png',TD/'158_bank5_indices.png',H/'pack_ultimate_return.py'):
  def altered(p,target=target):
   b=p.read_bytes();return bytes([b[0]^1])+b[1:]if p==target.resolve()else b
  test('보호입력_'+target.name,lambda read=altered:validate(data,lk,read))
 need(len(rejected)==12,'Rejection coverage');validate(data,lk);(D/'PL02_U.ARC').write_bytes(expected);proof.update(reproduction_runs=runs,rejection_count=len(rejected),rejections=rejected,source_lock_sha256=sha((D/'SOURCE_LOCK.json').read_bytes()),limitations=['새156 손끝은 수용기본보다 안쪽2px/위2px이며 귀환 물리접점·미술 판단은 별도이다.','새 발목/샌들 앞발x+1/y+1·뒷발y−1 강체등록과 원접속행 보존.전신변형/구형몸 덮기 없음.','157은 새몸 윤곽을 따르는 신규 파생정책이며 옛157 역사 가림예외 복원이 아니다.158은 역사159 전체타일/앞뒤순서를 보존한다.','원화/15층/고정패킹 검증이며 독립/미술/원MIPS/실기와 구분한다.']);write(D/'verification.json',proof)
 write(D/'proposal.json',{'project':'ver_buki_riko','baseline_sha256':'21bee159a1267d56561d4fa15c99ec652780af782fe08a433859c9eb7676099a','files':{'PL02_U.ARC':{'path':(D/'PL02_U.ARC').relative_to(ROOT).as_posix(),'before':'98ab01e8581d6bca15d75d703e7605899f2a871e042f5b09b13c5f2e07cf132e','after':FINAL}},'sequential_parent':ev(P),'targets':ev(TD/'manifest.json'),'target_lock':ev(D/'SOURCE_LOCK.json'),'source_art':lk['files'],'selected_refs':list(REFS),'scope':'Ultimate 귀환156 새원화+157 새윤곽/158 역사빛의3참조. 고정은행/entry/LBA/EXE/팔레트/음향 보존.','frozen':False,'runtime_verified':False})
 write(D/'PREPARED_LOCK.json',{'files':{p.name:sha(p.read_bytes())for p in sorted(D.iterdir())if p.is_file()}})
 write(H/'ultimate_return_components.json',{'project':'ver_buki_riko','source_bin':'out/ver_buki_riko/sprite_style_unification_20261107_v20/shibuki_riko.bin','source_sha256':'9bfd915f5e717781dd433eb291daa1aac1bad424734ad7decad69498d521598b','resources':{'PL02_U.ARC':{'path':(D/'PL02_U.ARC').relative_to(ROOT).as_posix(),'before':PARENT,'after':FINAL}},'checkpoint_only':True,'scope_note':'BR20 대비 새귀환3 원MIPS 정적검사. 부모의동결승리4/등장8/피격/나머지자원은 보존.'})
 print(json.dumps({'proposal':ev(D/'proposal.json'),'candidate':FINAL,'lock':ev(D/'SOURCE_LOCK.json'),'reproduction':3,'rejections':12}))
if __name__=='__main__':main()
