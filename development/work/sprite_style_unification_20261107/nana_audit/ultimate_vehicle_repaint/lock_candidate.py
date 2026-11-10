"""검증할 차량13의 원화/등록/패킹 입력을 고정한다."""
from pathlib import Path
import json,hashlib
D=Path(__file__).resolve().parent;N=D.parent;ROOT=N.parents[2];P=D/'packed_vehicle_candidate_v1'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 out=P/'INPUT_FROZEN.json';assert not out.exists();assert sha(P/'PL02_U.ARC')=='94326933d0dd62ccd7a5904019cae9fd36fc068a6acde8941d6bf8ff363666ca'
 names=['a_inputs_v1','a_v1','a_registered_v1','b_inputs_v1','b_v1','b_registered_v1','contacts_probe_v1','common_probe_v2','targets_v1'];files=[p for name in names for p in(D/name).rglob('*')if p.is_file()]
 files += [D/name for name in('prepare_inputs.py','save_and_register.py','prepare_contacts.py','prepare_common.py','prepare_targets.py','verify_sources.py','pack_native.py','lock_candidate.py')]
 files += [N/'base_run_repaint/register_page.py',N/'base_run_repaint/pack_cycle.py',N/'native_restore/preview_restore.py',N/'ultimate_victory_repaint/register_page.py',N/'ultimate_standing_repaint/prepare_common.py',N/'ultimate_special_finish_repaint/packed_special_candidate_v1/PL02_U.ARC',N/'ultimate_special_finish_repaint/packed_special_candidate_v1/FROZEN.json',N.parent/'zero_audit/nana_ultimate_vehicle_relations01/report.json',N.parent/'zero_audit/nana_ultimate_vehicle_relations01/conclusions.json',ROOT/'scripts/export_x_consistency.py',ROOT/'scripts/overhaul_sprites_costume_pack.py',ROOT/'scripts/prepare_shibuki_ultimate_production.py',ROOT/'scripts/prepare_riko_ui.py',ROOT/'src/psx_player.py']
 files=sorted(set(files));v=json.loads((P/'verification.json').read_text('utf8'));lock={'candidate_sha256':sha(P/'PL02_U.ARC'),'parent_sha256':v['before'],'target_manifest_sha256':sha(D/'targets_v1/manifest.json'),'files':[{'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)}for p in files],'scope':'162/166/170/174 네자세×두의상8원화→홍채4/손발8강체/의상경계18/공통손→원Y별칭9개의65층 입력고정. 실기·최종FROZEN은 별도.','frozen_asset_final':False};out.write_text(json.dumps(lock,ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps({'candidate':v['after'],'files':len(files),'lock':sha(out)}))
if __name__=='__main__':main()
