from pathlib import Path
import json,hashlib
W=Path(__file__).resolve().parent;ROOT=W.parents[1]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def record(n,paths,arc,findings,limits):
 p=W/f'root_review_checkpoint{n}.json';assert not p.exists()
 p.write_text(json.dumps({'root_actually_viewed':[{'path':q.relative_to(ROOT).as_posix(),'sha256':sha(q)} for q in paths],'arc_sha256':sha(arc),'findings':findings,'limits':limits,'runtime_verified':False,'final_user_accepted':False},ensure_ascii=False,indent=2)+'\n','utf8');print(n,sha(p))
H=W/'shibuki_audit';D=H/'prepared_ultimate_hurt02'
paths=[D/f'{form}_readback_{i:02}.png' for i in range(4) for form in ('before','after')]+[H/'ultimate_hurt_sequence01'/f'{form}_id{i}_ordered.png' for i in (33,34,35) for form in ('before','after')]
record(109,paths,D/'PL02_U.ARC',['최종 재추출8판과 원순서6판 모두 루트가 직접 열람했다. 전후 의상 피격에서 귀·머릿결·얼굴과 소매/수영복의 경계가 이어지며 새234 맨팔과 몸 연결에서 추가 확정 단절을 찾지 못했다.','106 감전·110 후퇴·233/234 피격의 포즈별 높이와 팔 이동을 대기 기준에서 비교했다. 실루엣/전기 효과는 같은 새 몸체 흐름으로 재생된다. 112..114의 양폼 공통 재킷 실루엣은 기존 구현 정책을 보존한 것이므로 두 의상 독립 효과로 주장하지 않는다.'],['정적 순서도 직접 열람이며 실기 피격 전수 완료가 아니다.','모든 방향·피해원·부분파츠와 전체 미술 완료는 별도다.'])
D=W/'nana_audit/ultimate_ceremony_repaint'
paths=[D/'packed_arrival_candidate_v1'/f'readback_{i}.png' for i in range(1,6)]+[D/'native_cycle_v1'/f'timeline_{i}.png' for i in (2,95,96)]
record(110,paths,D/'packed_arrival_candidate_v1/PL02_U.ARC',['최종 재추출5판과 원EXE 등장/차지 연결 순서3판을 루트가 직접 열람했다. 새로운 얼굴·머릿결·옷 가장자리와 손에 연결된 사랑이를 양 의상에서 확인했다.','138 국소 보완의 종아리 외곽이 재삽입 뒤에도 유지되며139와 발 위치가 연속된다. 130/131/134 효과 및141 대기+먼지는 새 몸체와 연결된다. 원래부터 순수 효과인132/140을 새 몸체 원화로 집계하지 않는다.'],['원순서 시뮬레이션과 재추출 정지판이며 실제 등장 전환/캡슐/차지 실기 증거가 아니다.','모든 순간의 시각적 무결점·사용자 수용·전체 완료를 주장하지 않는다.'])
