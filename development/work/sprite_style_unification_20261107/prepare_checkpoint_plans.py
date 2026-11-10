"""검증된 작업 ARC 목록만 새 체크포인트 계획에 묶는다. 디스크 쓰기는 하지 않는다."""
from pathlib import Path
import json
W=Path(__file__).resolve().parent
def read(name): return json.loads((W/name).read_text('utf8'))
def save(name, data): (W/name).write_text(json.dumps(data, ensure_ascii=False, indent=2)+'\n', 'utf8')
br=read('checkpoint_br_components.json')
br['resources'].update(read('shibuki_audit/prepared_lowhp_return01/proposal.json')['files'])
p=read('zero_audit/riko_restore/prepared_cloth_v1/proposal.json')
br['resources']['PL01_U.ARC'].update(path=p['resource'],after=p['after_sha256'])
save('checkpoint_br_lowhp_components.json',br)
rn=read('checkpoint_rn_components.json')
p=read('zero_audit/rin_extension/prepared_run_v1/proposal.json')
rn['resources']['PL01_U.ARC'].update(path=p['resource'],after=p['after_sha256'])
save('checkpoint_rn_run_components.json',rn)
