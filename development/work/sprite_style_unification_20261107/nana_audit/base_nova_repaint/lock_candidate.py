"""기본/포스 노바6 최종입력을 고정하고 RN41 원MIPS 계획을 만든다."""
from pack_candidate import *
def validate_inputs(parent,read=lambda p:p.read_bytes()):
 need(sha(parent)==BEFORE,'부모 해시');p=D/'packed_nova_candidate_v1';lock=json.loads(read(p/'INPUT_FROZEN.json'))
 need(lock['candidate_sha256']=='94cf560530c87ac11a03c029a9b6e98be44c06ea6d30d6c5ce66204c8a8e3cb3'and lock['parent_sha256']==BEFORE and lock['refs']==list(REFS),'잠금 범위')
 for q in lock['files']:
  f=(ROOT/q['path']).resolve();need(f.is_relative_to(ROOT),'입력경로');need(sha(read(f))==q['sha256'],'잠긴 입력 변경: '+q['path'])
 need(sha(read(p/'PL00_U.ARC'))==lock['candidate_sha256'],'후보 해시');return lock
def main():
 p=D/'packed_nova_candidate_v1';need(not(p/'INPUT_FROZEN.json').exists(),'새입력잠금');v=json.loads((p/'verification.json').read_text('utf8'))
 dirs=['a_inputs_v1','a_v1','a_registered_v1','b_inputs_v1','b_v1','b_registered_v1','common_layers_probe_v1','preparation_effect_probe_v1','preparation_effect_probe_v2','dash_layers_probe_v1','head_templates_probe_v2']
 files=[f for n in dirs for f in(D/n).rglob('*')if f.is_file()];files+=list(D.glob('*.py'))
 files += [PARENT,PARENT.with_name('FROZEN.json'),N/'base_run_repaint/register_page.py',N/'base_run_repaint/pack_cycle.py',N/'native_restore/preview_restore.py',W/'shibuki_audit/repack_part_records_lossless.py',ROOT/'work/overhaul_20261105/ui/nana_fourth_nova/fourth_217.png']
 for name in ['nana_base_nova214_relations01','nana_remaining_after_hover_read01']:files += [f for f in(W/'zero_audit'/name).rglob('*')if f.is_file()and f.suffix!='.pyc']
 for name in ['scripts/export_x_consistency.py','scripts/overhaul_sprites_costume_pack.py','scripts/prepare_shibuki_ultimate_production.py','scripts/prepare_shibuki_armor_remaining.py','scripts/prepare_riko_ui.py','scripts/overhaul_ui_nova_pack.py','src/psx_player.py','src/psx_ui_atlas.py']:files.append(ROOT/name)
 files=sorted(set(files));write(p/'INPUT_FROZEN.json',{'candidate_sha256':v['after'],'parent_sha256':BEFORE,'refs':list(REFS),'target_layers':30,'files':[{'path':f.relative_to(ROOT).as_posix(),'sha256':digest(f)}for f in files],'scope':'새213/215/217 각두의상6셀→6참조30층.214외부124원효과/216별칭/220몸+1파생;218219불변.뒤베일 소유조정에도 기본/포스전체그림불변.최종검증동결은별도.','frozen_asset_final':False})
 plan={'project':'ver_rin_nana','source_bin':'out/ver_rin_nana/sprite_style_unification_20261107_v41/rin_nana.bin','source_sha256':'e765577ac65cff3348a76ab0d2719ea96471b2c7895a35ac5a3c428db87385b3','resources':{'PL00_U.ARC':{'path':(p/'PL00_U.ARC').relative_to(ROOT).as_posix(),'before':BEFORE,'after':v['after']}},'checkpoint_only':True};write(D/'native_components_v1.json',plan);print(json.dumps({'inputs':len(files),'lock':digest(p/'INPUT_FROZEN.json'),'candidate':v['after']}))
if __name__=='__main__':main()
