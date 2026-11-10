"""승리4 후보를 원화/접점/20층과 묶어 재현 및 잘못된 입력 거부를 검증."""
from pathlib import Path
import sys,json
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
from pack_ultimate_victory import build,P,PARENT,REFS,TD
FINAL='ec7a6847ec8de42a3b25c1d0b87fdc96330bc61488c2296426ab24cbe9cfa9b8'
MANIFEST='cc0ce644964e0651fbe12db73727e1c0f991a491c14ffb10662fca94b96cfd55'
D=H/'prepared_ultimate_victory01'
def ev(p):return {'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p.read_bytes())}
def validate(data,lk,read=lambda p:p.read_bytes()):
 need(sha(data)==PARENT,'Wrong parent');need(lk['parent_sha256']==PARENT and lk['candidate_sha256']==FINAL and lk['refs']==list(REFS),'Lock scope mismatch')
 for name,h in lk['files'].items():
  p=(ROOT/name).resolve();need(p.is_relative_to(ROOT.resolve()),'Outside workspace');need(sha(read(p))==h,'Changed input '+name)
 return True
def main():
 need(not D.exists(),'Fresh prepared');data=P.read_bytes();expected=(H/'ultimate_victory_pack01/PL02_U.ARC').read_bytes();need(sha(expected)==FINAL,'Candidate changed');meta=json.loads((TD/'manifest.json').read_text('utf8'));paths={ROOT/n for n in meta['source_files']};paths.update(p for p in TD.iterdir()if p.is_file());paths.update((P,P.parent/'FROZEN.json'))
 paths.update(H/n for n in('pack_ultimate_victory.py','prepare_victory_candidate.py','native_pose_pack.py','pack_shibuki_hurt.py','repack_part_records_lossless.py','pack_dash_complete.py','prepare_lowhp_final.py'))
 paths.update(ROOT/'scripts'/n for n in('prepare_shibuki_ultimate_production.py','overhaul_sprites_costume_pack.py','prepare_shibuki_armor_remaining.py','prepare_riko_ui.py','export_x_consistency.py'));paths.update(ROOT/'src'/n for n in('psx_player.py','psx_ui_atlas.py'))
 lk={'parent_sha256':PARENT,'candidate_sha256':FINAL,'refs':list(REFS),'files':{p.relative_to(ROOT).as_posix():sha(p.read_bytes())for p in sorted(paths)}};validate(data,lk);D.mkdir();write(D/'SOURCE_LOCK.json',lk);runs=[]
 for i in range(3):
  validate(data,lk);new,proof=build(data,MANIFEST);need(new==expected,'Reproduction differs');runs.append({'run':i+1,'sha256':sha(new),'whole_resource_exact':True});print(json.dumps({'run':i+1,'exact':True}),flush=True)
 rejected=[]
 def test(name,fn):
  try:fn()
  except(ValueError,FileNotFoundError)as e:rejected.append({'case':name,'error':str(e)});return
  raise ValueError('Invalid input accepted '+name)
 test('부모1바이트',lambda:validate(bytes([data[0]^1])+data[1:],lk));test('부모잘림',lambda:validate(data[:-1],lk));test('빈부모',lambda:validate(b'',lk))
 for k,v in(('parent_sha256','0'*64),('candidate_sha256','0'*64),('refs',[135])):test('잠금_'+k,lambda k=k,v=v:validate(data,{**lk,k:v}))
 for target in(H/'ultimate_victory_inputs01/page02/generated.png',H/'ultimate_victory206_arm01/generated.png',H/'ultimate_victory_common_probe02/after_204_indices.png',H/'ultimate_victory_late_common02/after_207_indices.png',TD/'204_bank5_indices.png',H/'pack_ultimate_victory.py'):
  def altered(p,target=target):
   b=p.read_bytes();return bytes([b[0]^1])+b[1:]if p==target.resolve()else b
  test('보호입력_'+target.name,lambda read=altered:validate(data,lk,read))
 need(len(rejected)==12,'Rejection coverage');validate(data,lk);(D/'PL02_U.ARC').write_bytes(expected);proof.update(reproduction_runs=runs,rejection_count=len(rejected),rejections=rejected,source_lock_sha256=sha((D/'SOURCE_LOCK.json').read_bytes()),limitations=['새 원화의 206/207 발목+샌들 y+1,207 최고주먹/손목 y−1 강체 등록 및 접속 원행 보존. 원US 전신자세 복원 주장이 아님.','원화/정합/20층은 정적 후보이며 별도 원MIPS·독립·최종미술·원표검토·실기 구분.','미완료 등장135는 이 후보에서도 부모와 동일. 귀환156..158은 아직 새 제작 범위 밖.']);write(D/'verification.json',proof)
 write(D/'proposal.json',{'project':'ver_buki_riko','baseline_sha256':'21bee159a1267d56561d4fa15c99ec652780af782fe08a433859c9eb7676099a','files':{'PL02_U.ARC':{'path':(D/'PL02_U.ARC').relative_to(ROOT).as_posix(),'before':'98ab01e8581d6bca15d75d703e7605899f2a871e042f5b09b13c5f2e07cf132e','after':FINAL}},'sequential_parent':ev(P),'targets':ev(TD/'manifest.json'),'target_lock':ev(D/'SOURCE_LOCK.json'),'source_art':lk['files'],'selected_refs':list(REFS),'scope':'Ultimate 승리204..207 새4자세/전후8표시. 고정은행/entry/LBA/EXE/팔레트/음향 보존.','frozen':False,'runtime_verified':False})
 write(D/'PREPARED_LOCK.json',{'files':{p.name:sha(p.read_bytes())for p in sorted(D.iterdir())if p.is_file()}})
 write(H/'ultimate_victory_components.json',{'project':'ver_buki_riko','source_bin':'out/ver_buki_riko/sprite_style_unification_20261107_v18/shibuki_riko.bin','source_sha256':'b0bc7e3105966fbca46bb28b6dd8e2ae5daf4b785cd1ffb203b0bdfde6bfcc88','resources':{'PL02_U.ARC':{'path':(D/'PL02_U.ARC').relative_to(ROOT).as_posix(),'before':'b43e021b70c055d142521d1c679bef323d76b0b30bf27b41c9988815330b2e94','after':FINAL}},'checkpoint_only':True,'scope_note':'BR18 대비 선행동결 등장8+새승리4를 포함하는 원MIPS 정적 검사. 실제 제작 직전부모는3e55이며 비대상508raw 검사는 그 부모 기준.'})
 print(json.dumps({'proposal':ev(D/'proposal.json'),'candidate':FINAL,'lock':ev(D/'SOURCE_LOCK.json'),'reproduction':3,'rejections':12}))
if __name__=='__main__':main()
