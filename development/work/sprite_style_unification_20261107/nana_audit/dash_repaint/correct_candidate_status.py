"""Correct copied diagnostic status; image/ARC content stays immutable."""
from pathlib import Path
import json,hashlib
D=Path(__file__).resolve().parent
p=D/'joint_layers_candidate_v1/manifest.json';m=json.loads(p.read_text('utf8'));assert all(not q['unresolved_folded_leg']for q in m['frames']);m['reason']='20참조 원화 및 공통 접점 후보 완성. 독립 읽기와 root의 최종 네이티브 검토 대기.';p.write_text(json.dumps(m,ensure_ascii=False,indent=2)+'\n','utf8');h=hashlib.sha256(p.read_bytes()).hexdigest()
for folder in('packed_dash_candidate_v1','packed_dash_reproduction_v1'):
 q=D/folder/'verification.json';v=json.loads(q.read_text('utf8'));v['targets_manifest_sha256']=h;q.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n','utf8')
print(h)
