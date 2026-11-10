"""새95/97 원화·등록·15층 및 무손실 저장 레시피를 읽기 입력으로 고정."""
from pathlib import Path
import sys,json
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write

def main():
    out=H/'standing_special_locked01'
    need(not out.exists(),'Fresh lock required')
    folders=('standing_special_inputs01','standing_special95_chest01','standing_special_native01',
             'standing_special_native02','standing_special_layers01','standing_special_storage03')
    files={p.relative_to(ROOT).as_posix():sha(p.read_bytes()) for folder in folders for p in sorted((H/folder).iterdir()) if p.is_file()}
    for name in ('prepare_standing_special_inputs.py','register_standing_special.py','prepare_special95_chest_edit.py',
                 'register_special95_chest.py','probe_standing_special_layers.py','probe_special_grid_storage.py'):
        p=H/name;files[p.relative_to(ROOT).as_posix()]=sha(p.read_bytes())
    targets={}
    from PIL import Image
    import numpy as np
    for ref in (95,97):
        targets[str(ref)]={str(bank):sha(np.array(Image.open(H/f'standing_special_layers01/{ref:03}_bank{bank}_indices.png')).tobytes()) for bank in (0,5,6,7,8)}
    out.mkdir()
    write(out/'LOCK.json',{'parent_sha256':'87e7d1db40c2380815ca2986bc27382db73f718d9c338d2eaad776372a2e257b',
        'refs':[95,96,97],'targets':targets,'derived96':'새95를 x+1 이동. 원US 및 현PL00 관계와 동일.',
        'files':files,'candidate_arc_written':False,'bank12_tail_reuse_bytes':280,
        'approval_scope':'root가 기존 승인된 가역 내부 패킹 범위에서 판단한 시험. 새 주소의 사용자 직접승인 주장이 아님.'})
    print(json.dumps({'lock_sha256':sha((out/'LOCK.json').read_bytes()),'files':len(files)}))

if __name__=='__main__':main()
