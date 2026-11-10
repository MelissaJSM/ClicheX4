"""새 노바20층과 기존10참조의 저장순열 입력을 고정."""
from pathlib import Path
import sys,json
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
from prepare_nova_base_targets import TD,PARENT,REFS

def main():
    d=H/'nova_locked01';need(not d.exists(),'새 잠금 필요');meta=json.loads((TD/'manifest.json').read_text('utf8'));plan=json.loads((H/'nova_storage_plan01/report.json').read_text('utf8'));files=dict(meta['source_files'])
    for folder in(TD,H/'nova_storage01',H/'nova_storage_plan01'):
        for p in folder.iterdir():
            if p.is_file():files[p.relative_to(ROOT).as_posix()]=sha(p.read_bytes())
    for g in plan['storage_only_groups']:
        p=H/g['source_probe'];files[p.relative_to(ROOT).as_posix()]=sha(p.read_bytes())
    p=H/'standing_fire_existing_tileorder01/report.json';files[p.relative_to(ROOT).as_posix()]=sha(p.read_bytes())
    for name in('probe_nova_storage.py','probe_nova_storage_plan.py','lock_nova_base.py'):
        p=H/name;files[p.relative_to(ROOT).as_posix()]=sha(p.read_bytes())
    d.mkdir();write(d/'LOCK.json',{'parent_sha256':PARENT,'candidate_sha256':plan['memory_candidate_sha256'],'refs':list(REFS),'storage_only_refs':plan['storage_only_refs'],'targets':meta['targets'],'files':files,'scope':'새 노바4참조20층. 기존10참조는 전체texel 역순열 보존하는 저장순서만 변경. graphics/parts 은행경계·외부길이 불변.','user_new_approval_claimed':False})
    print(json.dumps({'sha256':sha((d/'LOCK.json').read_bytes()),'files':len(files)}))
if __name__=='__main__':main()
