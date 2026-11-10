"""첫7후보의 생성/등록/의미영역/목표35층 입력만 잠근다."""
from pathlib import Path
import json,hashlib
D=Path(__file__).resolve().parent;N=D.parent;ROOT=N.parents[2];P=D/'packed_first7_diagnostic_v1'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 out=P/'INPUT_FROZEN.json';assert not out.exists();asset=P/'PL02_U.ARC';assert sha(asset)=='dcaf1343747fabeab3054c59fc384c3bbd598209eccb6c5a37ac84c1d340d339'
 dirs=['a_inputs_v1','a_v1','a_registered_v1','a_arm_inputs_v1','a_arm_v1','a_arm_registered_v1','a_common_probe_v1','a_grip_probe_v1','a_layers_probe_v1','a_mirror_probe_v1','c_inputs_v1','c_v1','c_registered_v1','c_common_probe_v2','first7_targets_v1']
 files=[p for name in dirs for p in(D/name).rglob('*')if p.is_file()]
 files += [D/p for p in('register_page.py','register_bare_arm.py','prepare_common_a.py','share_grips_a.py','prepare_a_layers.py','prepare_a_mirrors.py','register_last.py','prepare_common_c.py','prepare_first7_targets.py','verify_a_sources.py','verify_first7_sources.py','pack_first7.py','lock_first7.py')]
 files += [N/'base_run_repaint/register_page.py',N/'native_restore/preview_restore.py',N/'ultimate_return_repaint/packed_return_candidate_v1/PL02_U.ARC',ROOT/'scripts/export_x_consistency.py',ROOT/'scripts/overhaul_sprites_costume_pack.py',ROOT/'scripts/prepare_shibuki_ultimate_production.py',ROOT/'src/psx_player.py',ROOT/'work/sprite_style_unification_20261107/zero_audit/nana_ultimate_ladder_relations01/report.json',ROOT/'work/sprite_style_unification_20261107/zero_audit/nana_ultimate_ladder_relations01/conclusions.json']
 files=sorted(set(files));d={'candidate_sha256':sha(asset),'parent_sha256':'493bf2706aae33b64c4ffe70be1576a7ed63b0a4f62c54e89ca5876131392e29','target_manifest_sha256':sha(D/'first7_targets_v1/manifest.json'),'files':[{'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)}for p in files],'scope':'사다리7후보 입력잠금. 아트최종/독립/실기 동결 아님. B교정거부 후보는입력에도포함하지 않고관련7참조 원바이트를그대로보존.','frozen_asset_final':False};out.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps({'files':len(files),'sha256':sha(out)}))
if __name__=='__main__':main()
