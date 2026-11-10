"""호버10의 실제 원화·등록·원발사점·50층 입력을 고정한다."""
from pathlib import Path
import json,hashlib
D=Path(__file__).resolve().parent;N=D.parent;ROOT=N.parents[2];P=D/'packed_hover_candidate_v1'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 out=P/'INPUT_FROZEN.json';assert not out.exists();assert sha(P/'PL02_U.ARC')=='e630d04286c1dbcbb65a5a301dd984f23cdecf13a1759dbaaf52ad8ae103efff'
 names=['a_inputs_v1','a_v1','b_inputs_v1','b_v1','first_registered_v1','last_registered_v1','semantic_samples_v1','semantic_last_v1','canonical_cases_probe_v4','muzzle_arm_a_inputs_v1','muzzle_arm_a_v1','muzzle_arm_a_registered_v1','muzzle_arm_b_inputs_v1','muzzle_arm_b_v1','muzzle_arm_b_registered_v1','muzzle_joint_probe_v1','muzzle_contacts_probe_v1','targets_preview_v3','shot_joint_probe_v2']
 files=[p for name in names for p in(D/name).rglob('*')if p.is_file()]
 files += [p for p in D.glob('*.py')if p.name not in('make_native_cycle.py','verify_native_cycle.py','freeze_candidate.py','record_review.py','verify_reproduction.py')]
 files += [N/'base_run_repaint/register_page.py',N/'base_run_repaint/pack_cycle.py',N/'native_restore/preview_restore.py',N/'ultimate_standing_repaint/prepare_common.py',N/'ultimate_vehicle_repaint/packed_vehicle_candidate_v1/PL02_U.ARC',N/'ultimate_vehicle_repaint/packed_vehicle_candidate_v1/FROZEN.json']
 for name in ('nana_ultimate_hover_relations01','nana_ultimate_hover_muzzle01'):files += [p for p in(N.parent/'zero_audit'/name).rglob('*')if p.is_file()]
 files += [ROOT/p for p in('scripts/export_x_consistency.py','scripts/overhaul_sprites_costume_pack.py','scripts/prepare_shibuki_ultimate_production.py','scripts/prepare_riko_ui.py','src/psx_player.py','src/psx_static_effect.py','src/psx_ui_atlas.py')]
 files += [D/'packed_hover_diagnostic_v2/verification.json']
 files=sorted(set(files));v=json.loads((P/'verification.json').read_text('utf8'));lock={'candidate_sha256':sha(P/'PL02_U.ARC'),'parent_sha256':v['before'],'target_manifest_sha256':sha(D/'targets_preview_v3/manifest.json'),'files':[{'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)}for p in files],'scope':'5고유몸체/새5발사팔→원총구표에 정합한 정본20·새피부손→상체0/하체5의50층. 최초8열 고정안은 진단 출처만 보존하고 미채택. 실제217..230 mask15 유지.','frozen_asset_final':False};out.write_text(json.dumps(lock,ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps({'candidate':v['after'],'files':len(files),'lock':sha(out)}))
 plan={'project':'ver_rin_nana','source_bin':'out/ver_rin_nana/sprite_style_unification_20261107_v36/rin_nana.bin','source_sha256':'3715c4f50c0adcceeeed435f3e59bdccc51c5bf79b4f7fa8fdb961b88fd1a3ea','resources':{'PL02_U.ARC':{'path':(P/'PL02_U.ARC').relative_to(ROOT).as_posix(),'before':v['before'],'after':v['after']}},'checkpoint_only':True}
 (D/'native_components_v1.json').write_text(json.dumps(plan,ensure_ascii=False,indent=2)+'\n','utf8')
if __name__=='__main__':main()
