"""새217/220·원효과 전체타일·기존6참조 저장순열·원count 읽기 잠금."""
from pathlib import Path
import sys,json
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
from prepare_nova_strike_base_targets import TD,PARENT,REFS
def main():
    d=H/'nova_strike_base_locked01';need(not d.exists(),'새 잠금')
    meta=json.loads((TD/'manifest.json').read_text('utf8'));plan=json.loads((H/'nova_strike_storage02/recipe.json').read_text('utf8'));need(plan['memory_candidate_passed'],'메모리 검증')
    countdir=H.parent/'zero_audit/shibuki_nova_part_count_read01';con=countdir/'conclusions.json';need(sha(con.read_bytes())=='5823bfcbdb1facbe12535fcd9b2b143d7daca7d66c5f71605a9022b1ad275c85','원파트 읽기')
    files=dict(meta['source_files'])
    for folder in(TD,H/'nova_strike_storage02',countdir):
        for p in folder.rglob('*'):
            if p.is_file():files[p.relative_to(ROOT).as_posix()]=sha(p.read_bytes())
    for g in plan['storage_only_groups']:
        p=H/g['source_probe'];files[p.relative_to(ROOT).as_posix()]=sha(p.read_bytes())
    for n in('standing_fire_existing_tileorder01/report.json','probe_nova_strike_storage02.py','lock_nova_strike_base.py'):
        p=H/n;files[p.relative_to(ROOT).as_posix()]=sha(p.read_bytes())
    for name,h in files.items():need(sha((ROOT/name).read_bytes())==h,'출처 변경')
    d.mkdir();write(d/'LOCK.json',{'parent_sha256':PARENT,'candidate_sha256':plan['memory_candidate_sha256'],'refs':list(REFS),'storage_only_refs':sorted(n for g in plan['storage_only_groups']for n in g['refs']),'targets':meta['targets'],'files':files,'effect220':meta['effect220'],'part_counts':{'217':[7,1,3,1,2],'220':[31,1,3,1,2]},'part_count_read':{'path':con.relative_to(ROOT).as_posix(),'sha256':sha(con.read_bytes())},'native_renderer_candidate_pending':True,'scope':'새217/220 10층.218/219 원효과는raw exact.220 원18타일 전체/24기록 뒤에새몸7파트.기존6참조는전체texel역순열만.모든은행경계·외부길이 불변.','user_new_approval_claimed':False})
    print(json.dumps({'sha256':sha((d/'LOCK.json').read_bytes()),'files':len(files)}))
if __name__=='__main__':main()
