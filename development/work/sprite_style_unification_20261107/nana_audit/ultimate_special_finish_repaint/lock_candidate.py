"""미술 방향 수용 후 같은 도트를 최종 후보로 복사하고 입력을 잠근다."""
from pathlib import Path
import json,hashlib,shutil
D=Path(__file__).resolve().parent;N=D.parent;ROOT=N.parents[2]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 src=D/'packed_special_diagnostic_v1';out=D/'packed_special_candidate_v1';assert not out.exists();assert sha(src/'PL02_U.ARC')=='56a3aeb489229d85bb72205bd14f866b4444ff5daa8e1bc7f91c82e9b3c46fc0';out.mkdir()
 for name in('PL02_U.ARC','readback_1.png','readback_2.png'):shutil.copyfile(src/name,out/name);assert sha(src/name)==sha(out/name)
 for name in('verification.json','proposal.json'):
  value=json.loads((src/name).read_text('utf8'))
  if name=='verification.json':value['scope']='새95/98 두몸체와96/99 X+1 파생의 최종 고정후보. 진단과 원화/ARC 동일이며 최종독립·원MIPS·원순서·실기는 별도.';value['promoted_from_same_bytes']=str(src.relative_to(ROOT)).replace('\\','/')
  else:value['files']['PL02_U.ARC']['path']=(out/'PL02_U.ARC').relative_to(ROOT).as_posix()
  (out/name).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n','utf8')
 names=['a_inputs_v1','a_v1','first_registered_v1','geometry_inputs_v1','geometry_v1','geometry_registered_v1','head_body95_probe_v1','contacts_probe_v1','torso98_inputs_v1','torso98_v1','torso98_registered_v1','hand98_inputs_v1','hand98_v1','hand98_registered_v1','hand98_local_probe_v1','common_probe_v2','targets_v1'];files=[p for name in names for p in(D/name).rglob('*')if p.is_file()]
 files += [D/name for name in('prepare_inputs.py','register_first.py','prepare_geometry_edit.py','register_geometry.py','probe_head_body.py','probe_contacts.py','prepare98_edit.py','register98.py','prepare98_hand.py','register98hand.py','prepare98_hand_local.py','prepare_common.py','prepare_targets.py','verify_sources.py','pack_native.py','lock_candidate.py')]
 files += [N/'base_run_repaint/register_page.py',N/'base_run_repaint/pack_cycle.py',N/'native_restore/preview_restore.py',N/'ultimate_victory_repaint/register_page.py',N/'ultimate_standing_repaint/prepare_common.py',N/'ultimate_recoil_repaint/packed_recoil_candidate_v1/PL02_U.ARC',N/'ultimate_recoil_repaint/packed_recoil_candidate_v1/FROZEN.json',N.parent/'zero_audit/nana_ultimate_special_relations01/report.json',ROOT/'scripts/export_x_consistency.py',ROOT/'scripts/overhaul_sprites_costume_pack.py',ROOT/'scripts/prepare_shibuki_ultimate_production.py',ROOT/'scripts/prepare_riko_ui.py',ROOT/'src/psx_player.py']
 files=sorted(set(files));v=json.loads((out/'verification.json').read_text('utf8'));lock={'candidate_sha256':sha(out/'PL02_U.ARC'),'parent_sha256':v['before'],'target_manifest_sha256':sha(D/'targets_v1/manifest.json'),'files':[{'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)}for p in files],'scope':'95/98 두자세 전후 네표시와 손/명암 국소 원화 출처,53의상경계와1공통손 표본,98정본85 및96/99 X+1 파생20층 입력잠금. 전체실기/최종동결은 별도.','frozen_asset_final':False};(out/'INPUT_FROZEN.json').write_text(json.dumps(lock,ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps({'candidate':v['after'],'files':len(files),'lock':sha(out/'INPUT_FROZEN.json')}))
if __name__=='__main__':main()
