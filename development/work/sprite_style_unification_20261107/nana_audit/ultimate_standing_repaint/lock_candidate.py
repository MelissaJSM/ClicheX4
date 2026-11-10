"""특수3의 허용 원화·의미등록·15목표층을 진단 후 고정한다."""
from pathlib import Path
import json,hashlib
D=Path(__file__).resolve().parent;N=D.parent;ROOT=N.parents[2];P=D/'packed_standing_candidate_v1'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 out=P/'INPUT_FROZEN.json';assert not out.exists();asset=P/'PL02_U.ARC';v=json.loads((P/'verification.json').read_text('utf8'));assert v['passed']and sha(asset)==v['after']
 names=['a_inputs_v1','a_v1','first_registered_v1','common_probe_v3','targets_probe_v2'];files=[p for name in names for p in(D/name).rglob('*')if p.is_file()]
 files += [D/p for p in('prepare_inputs.py','register_first.py','prepare_common.py','prepare_targets.py','verify_sources.py','pack_native.py','lock_candidate.py')]
 files += [N/'base_run_repaint/register_page.py',N/'base_run_repaint/pack_cycle.py',N/'native_restore/preview_restore.py',N/'ultimate_victory_repaint/register_page.py',N/'ultimate_ladder_repaint/packed_first7_diagnostic_v1/PL02_U.ARC',ROOT/'scripts/export_x_consistency.py',ROOT/'scripts/overhaul_sprites_costume_pack.py',ROOT/'scripts/prepare_shibuki_ultimate_production.py',ROOT/'scripts/prepare_riko_ui.py',ROOT/'src/psx_player.py']
 aud=N.parent/'zero_audit/nana_ultimate_special_relations01';files += [aud/p for p in('report.json','conclusions.json','effect_088_original.npy')]
 files=sorted(set(files));d={'candidate_sha256':sha(asset),'parent_sha256':v['before'],'target_manifest_sha256':sha(D/'targets_probe_v2/manifest.json'),'files':[{'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)}for p in files],'scope':'새89/97 네 전신과 원83효과의88만 입력잠금. 이전789ed 진단은89 맨팔 커프 의미경계8셀/권총음영1셀 후속으로 미채택. 이번 고정은 최종 독립·root미술·실기 동결과 다름. 사다리 보류자료는 사용하지 않음.','frozen_asset_final':False};out.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps({'files':len(files),'sha256':sha(out)}))
if __name__=='__main__':main()
