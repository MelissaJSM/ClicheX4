"""선택 사본 8개의 실제 열람과 독립 reader 입력을 별도 결속한다."""
from pathlib import Path
import hashlib,json
D=Path(__file__).resolve().parent;ROOT=D.parents[2];O=D/'nana_selection8_spares_independent01'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
r=json.loads((O/'report.json').read_text('utf8'))
assert sha(O/'report.json')=='a33f6e30a12e252fdb4415dab8ceca47a7244bbda689fc6a82be62925c10ffb2'
for q in r['readback_sheets']:assert sha(ROOT/q['path'])==q['sha256']
for p,h in r['inputs'].items():assert sha(ROOT/p)==h,p
v={'candidate_sha256':r['candidate_sha256'],'independent_report_sha256':sha(O/'report.json'),'actually_viewed_sheets':r['readback_sheets'],'observations':['비교판 01/03/05/07의 여덟 자세를 실제 열람했다. 새 선택 사본과 새 게임 그림 열은 같은 원점에서 동일하게 보인다.','새 머릿결·베레모·재킷 커프·부츠의 상세가 선택 사본에도 유지된다. 손/총/발 연결에 새로 확정할 절단이나 고립점을 찾지 못했다.','UI4/게임88의 밝은 83픽셀 효과는 같은 위치와 앞그림 순서를 유지한다. 새 머리가 그 뒤에 가려지는 모습도 게임 그림과 같다.','UI1/2의 작아진 정본 권총은 이미 수용된 게임85/86의 그대로인 사본이다. 선택 동기화에서 새로 총의 크기나 자세를 바꾼 것으로 해석하지 않는다.'],'new_art_requiring_change_found':False,'limits':['이번 실제 열람은 재추출 정적 네 판이다. 새 BIN 부팅/선택 애니메이션/실제 GPU 표시를 실행한 결과는 아니다.','별도 용량 감사의 원래 loader/14종 initializer 실행과 이번 58파트의 UV·반전 읽기 대조를 결합했다. 이번 후보에서 새 원 MIPS 실행을 했다는 주장은 하지 않는다.'],'runtime_verified':False}
p=O/'visual_review.json';assert not p.exists();p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n','utf8')
reader=D/'verify_nana_selection8_spares_independent.py'
lock={'reader':{'path':reader.relative_to(ROOT).as_posix(),'sha256':sha(reader)},'finalizer':{'path':Path(__file__).relative_to(ROOT).as_posix(),'sha256':sha(Path(__file__))},'input_hashes':r['inputs'],'outputs':{q.name:sha(q) for q in O.iterdir() if q.is_file()},'immutable_paths':True}
p=O/'READER_LOCK.json';assert not p.exists();p.write_text(json.dumps(lock,ensure_ascii=False,indent=2)+'\n','utf8')
print(json.dumps({'report':sha(O/'report.json'),'visual':sha(O/'visual_review.json'),'lock':sha(p)}))
