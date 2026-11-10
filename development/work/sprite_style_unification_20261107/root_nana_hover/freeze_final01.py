from pathlib import Path
import json,hashlib
D=Path(__file__).resolve().parent;W=D.parent;ROOT=W.parents[1];P=D/'packed_hover_final01';I=W/'nana_audit/base_hover_final_independent01';J=W/'zero_audit/nana_base_hover229_rearfoot_read01'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();read=lambda p:json.loads(p.read_text('utf8'));bound=lambda p:{'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)}
FINAL='9c1ff453a2308ddc40f39e5790de0aa6a5cf41dda43165b0fa16808f8c3a643c';out=P/'FROZEN.json';assert not out.exists();assert sha(P/'PL00_U.ARC')==FINAL
assert sha(P/'INPUT_LOCK.json')=='7238a32bc08ebd7abdb17d82b09381f4ac08d8660c8d02fc772025ccc681c56d'
for p,expected in[(I/'report.json','df56d6f10038434ccfea0eb776b1c95bcf13b6b9d07bc8310d620364d4c51e2a'),(I/'visual_review.json','f1dc457eb9c3651282bc758c405d439706e523bd93bdbea96f464650c11e6a58'),(I/'READER_LOCK.json','059bb8c4fe9b8075d7d01a61ae80aa1e5bf202848ca852010f2d43eac628036a'),(W/'root_review_checkpoint151.json','737229b6ac3dc0f01741d0111cfeb94f7e2f5cee2168d9539ee94418ff34d557'),(J/'report.json','3dc6d72eba9c8bc96bf720ed767b358107da1e98765dd0e0f40c0b04d9884e08')]:assert sha(p)==expected,p
for lock in(P/'INPUT_LOCK.json',I/'READER_LOCK.json'):
 for q in read(lock)['files']:assert sha(ROOT/q['path'])==q['sha256'],q['path']
for name,digest in read(J/'READER_LOCK.json')['files'].items():assert sha(ROOT/name)==digest,name
review=read(W/'root_review_checkpoint151.json');assert review['candidate_sha256']==FINAL
for q in review['actually_viewed_files']:assert q['actually_viewed']and sha(ROOT/q['path'])==q['sha256']
proofs=[P/'verification.json',P/'reproduction.json',I/'report.json',D/'native_components01_native_checks.json',D/'native_cycle01/verification.json']
for p in proofs:assert read(p)['passed'],p
assert read(D/'native_components01_native_checks.json')['resources']['PL00_U.ARC']['candidate_sha256']==FINAL
assert read(D/'native_cycle01/verification.json')['candidate_arc_sha256']==FINAL
assert read(I/'report.json')['candidate_sha256']==read(P/'reproduction.json')['candidate_sha256']==FINAL
proposal={'resource':'PL00_U.ARC','path':(P/'PL00_U.ARC').relative_to(ROOT).as_posix(),'before':read(P/'verification.json')['before'],'after':FINAL,'refs':list(range(221,231)),'new_body_refs':[221,223,225,227,229],'new_firing_arms':[222,224,226,228,230],'forms':['base_with_leg_part','fourth','partial_masks_with_bit8'],'runtime_verified':False,'user_accepted':False}
(P/'proposal.json').write_text(json.dumps(proposal,ensure_ascii=False,indent=2)+'\n','utf8')
files=[P/'PL00_U.ARC',P/'proposal.json',P/'INPUT_LOCK.json',*proofs,I/'visual_review.json',I/'READER_LOCK.json',I/'native_binding.json',J/'report.json',J/'visual_review.json',J/'READER_LOCK.json',W/'root_review_checkpoint151.json',D/'native_components01.json',D/'native_cycle01/manifest.json',D/'native_cycle01/REVIEW.html',D/'record_root_review151.py',Path(__file__).resolve()]
r={'frozen':True,'character':'nana','candidate_sha256':FINAL,'parent_arc_sha256':proposal['before'],'refs':proposal['refs'],'files':[bound(p)for p in files],'input_files_verified':446,'source_lock_sha256':sha(P/'INPUT_LOCK.json'),'independent_counts':read(I/'report.json')['counts'],'root_art_review_checkpoints':[str((W/'root_review_checkpoint151.json').relative_to(ROOT))],'root_static_art_direction_accepted':True,'status':'기본/포스 호버10의 새50층 및229/230 신발20px 국소수정 검증. 전체미술완료와 별개.','storage_policy':'고정은행/원5공유스트림. 대상 저장타일20/22/21→32는 기존4096B 버퍼 이내. 투명 head5참조128/129/132/140/159의1파트→0파트로20B절약. 비대상1732기록 exact와 구분한다.','verified':'7296RGBA,50층,498비대상raw,1090비대상층,원MIPS decode/upload15참조,동일재현1회/11거부,12원표/84canvas 재생정지,독립12판 및 Root23판 직접검토. 원총구/15추진/7탄환 보존.','limits':['최초등록 고정12셀 재양자화는 제작자가 수행했다. 독립검사는 등록후몸/팔부터 재구성했고 새97ba 신발2셀만 직접 재양자화했다.','기본 아머없는 상태의 불완전 mask0를 실제 호버로 취급하지 않으며 유효부분은bit8 포함이다.','실제불꽃CLUT·60Hz입력·새호버 실기는 별도다. 원표 오프라인 재생을 인게임검증으로 부르지 않는다.'],'runtime_verified':False,'final_user_accepted':False,'all_nana_style_complete':False}
out.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps({'candidate':FINAL,'frozen_sha256':sha(out),'files':len(files)}))
