from pathlib import Path
import json,hashlib,sys
W=Path(__file__).resolve().parent;ROOT=W.parents[1];sys.path.insert(0,str(ROOT))
from scripts.export_x_consistency import Archive
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
D=W/'nana_audit/hurt_repaint/packed_hurt_candidate_v1'
arc=D/'PL00_U.ARC';assert sha(arc)=='978a9fc18e31f221d20568d747078f098f37fb120c303c64afc916442721be9f'
a=Archive(arc.read_bytes());m=json.loads((W/'nana_hurt_partial_review02/manifest.json').read_text('utf8'))
assert all(hashlib.sha256(a.composite(q['ref'],q['mask'],q['arm'])[0].tobytes()).hexdigest()==q['rgba_sha256'] for q in m['frames'])
pages=[D/f'readback_{i}.png' for i in range(1,6)]
r={'root_actually_viewed':[{'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)} for p in pages],
 'candidate_sha256':sha(arc),'previous_root83_partial_rgba_exact':128,
 'findings':['최종 후보978a의 새 피격13/양폼 재추출5판을 직접 보았다. 새 몸체 세부와 실루엣, 국소 정합한235/236 오라를 유지하며 추가 확정 절단을 찾지 못했다.',
 '이미 직접 열람한106/110/233/234×16파츠×팔2유형128RGBA가 최종 후보에서도 정확히 같음을 재확인했다.'],
 'limits':['원래33~37 순서 재생, 재현·거부와 최종 독립검사/동결 및 새 부팅 실기는 진행 중이다.'],
 'final_user_accepted':False}
p=W/'root_review_checkpoint85.json';assert not p.exists();p.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n','utf8');print(sha(p))
