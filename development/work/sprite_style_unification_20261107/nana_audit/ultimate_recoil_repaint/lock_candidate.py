"""반동2의 원화·의미등록·정본권총·10목표층을 고정한다."""
from pathlib import Path
import json,hashlib
D=Path(__file__).resolve().parent;N=D.parent;ROOT=N.parents[2];P=D/'packed_recoil_candidate_v1'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 out=P/'INPUT_FROZEN.json';assert not out.exists();asset=P/'PL02_U.ARC';v=json.loads((P/'verification.json').read_text('utf8'));assert v['passed']and sha(asset)==v['after']
 names=['a_inputs_v1','a_v1','first_registered_v1','common_probe_v2','targets_v1'];files=[p for name in names for p in(D/name).rglob('*')if p.is_file()]
 files += [D/p for p in('prepare_inputs.py','register_first.py','prepare_common.py','prepare_targets.py','verify_sources.py','pack_native.py','lock_candidate.py')]
 files += [N/'base_run_repaint/register_page.py',N/'base_run_repaint/pack_cycle.py',N/'native_restore/preview_restore.py',N/'ultimate_victory_repaint/register_page.py',N/'ultimate_standing_repaint/packed_standing_candidate_v1/PL02_U.ARC',ROOT/'scripts/export_x_consistency.py',ROOT/'scripts/overhaul_sprites_costume_pack.py',ROOT/'scripts/prepare_shibuki_ultimate_production.py',ROOT/'scripts/prepare_riko_ui.py',ROOT/'src/psx_player.py']
 files += [N/'ultimate_standing_repaint/prepare_common.py',N.parent/'root_nana_recoil/prepare_targets.py',N.parent/'root_nana_recoil/packed_recoil03/FROZEN.json',N.parent/'zero_audit/nana_ultimate_recoil_visual01/report.json']
 files=sorted(set(files));d={'candidate_sha256':sha(asset),'parent_sha256':v['before'],'target_manifest_sha256':sha(D/'targets_v1/manifest.json'),'files':[{'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)}for p in files],'scope':'새90/91 네전신·홍채/얼굴표본·의상경계19셀·정본91총/공통손→10층 입력잠금.91은수용모듈위치정책이며 실제새발사점증명이아님. 최종독립/root미술/실기 동결은별도.','frozen_asset_final':False};out.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps({'files':len(files),'sha256':sha(out)}))
if __name__=='__main__':main()
