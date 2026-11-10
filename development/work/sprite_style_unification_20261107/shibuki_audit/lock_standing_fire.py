"""새85..92 원화40층과 기존18참조 순열의 읽기 입력을 고정한다."""
from pathlib import Path
import sys,json
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
def main():
    d=H/'standing_fire_locked01';need(not d.exists(),'새 잠금 필요')
    folders=('standing_fire_inputs01','standing_fire_inputs02','standing_fire_inputs03','standing_fire_fourth_sleeves01','standing_fire_native01','standing_fire_native02','standing_fire_followthrough_native01','standing_fire_recovery_native01','standing_fire_recovery_native02','standing_fire_modules_probe02','standing_fire_layers_probe01','standing_fire_layers_probe02','standing_fire_targets_probe01','standing_fire_compact01','standing_fire_existing_tileorder01','standing_fire_storage_plan02','standing_fire_contacts_review01')
    files={p.relative_to(ROOT).as_posix():sha(p.read_bytes())for folder in folders for p in sorted((H/folder).iterdir())if p.is_file()}
    scripts=('prepare_standing_fire_inputs.py','prepare_standing_followthrough_inputs.py','prepare_standing_recovery_inputs.py','register_standing_fire.py','register_standing_fire_sleeves.py','register_standing_followthrough.py','register_standing_recovery.py','register_standing_recovery_boot.py','probe_standing_fire_modules.py','probe_standing_fire_layers.py','register_standing_fire_layer_edges.py','prepare_standing_fire_targets_probe.py','probe_standing_fire_compact.py','probe_existing_tile_order_capacity.py','probe_standing_fire_storage_plan.py','review_standing_fire_contacts.py')
    for name in scripts:
        p=H/name;need(p.exists(),'제작코드 없음 '+name);files[p.relative_to(ROOT).as_posix()]=sha(p.read_bytes())
    m=json.loads((H/'standing_fire_targets_probe01/manifest.json').read_text('utf8'));plan=json.loads((H/'standing_fire_storage_plan02/report.json').read_text('utf8'));d.mkdir()
    write(d/'LOCK.json',{'parent_sha256':m['parent']['sha256'],'refs':list(range(85,93)),'targets':m['targets'],'storage_only_refs':plan['permutation_only_refs'],'files':files,'root_contact_direction_review':'root가 contacts_review01 두판 실제열람 후85 왼발1px/90·91폭 현재유지 수용 방향을 메시지로 전달. 최종전체수용 또는 실기아님.','scope':'새8참조40층과 기존18참조의 순열만 적용하는 가역 고정은행 시험. 원화삭제/재색상/은행경계변경 없음.','user_new_approval_claimed':False});print(json.dumps({'files':len(files),'sha256':sha((d/'LOCK.json').read_bytes())}))
if __name__=='__main__':main()
