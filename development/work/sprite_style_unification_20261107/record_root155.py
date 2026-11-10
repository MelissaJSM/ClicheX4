from pathlib import Path
import json,hashlib
W=Path(__file__).resolve().parent;ROOT=W.parents[1];H=W/'shibuki_audit'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
arc=H/'prepared_nova_strike_ultimate01/PL02_U.ARC';assert sha(arc)=='01997c949968d5a1a12d89e09c5eb46448bbcf245009feb9953e3d9e9356efd7'
paths=[H/'nova_strike_ultimate_pack03'/f'{n}.png'for n in('actual_readback_00','actual_readback_01','ownership_218','ownership_220')]+[H/'nova_strike_ultimate_sequence01'/f'{f}_{n}_order.png'for f in('after','before')for n in('preparation','strike')]
out=W/'root_review_checkpoint155.json';assert not out.exists()
data={'checkpoint':155,'candidate':arc.relative_to(ROOT).as_posix(),'candidate_sha256':sha(arc),'actually_viewed_files':[{'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p),'actually_viewed':True}for p in paths],'observations':['최종 재추출217..220, 몸/효과 소유2판과 원표 준비·돌진4판을 직접 열람했다.','수용한 획득 후 대기와 새217의 안경·귀·머릿결·맨팔·종아리/신발이 연결되며 추가 확정 몸 분리/효과에 의한 머리 절단을 찾지 못했다.','218의 기존3점,219 새 몸 실루엣,220 몸 가림 보완이 각각 분리되어 있다. 큰 외부 돌진 효과를 대기 몸 크기 변화로 오인하지 않는다.','획득 전 진단판의217..230은 실제 강제15 표시 정책대로 후폼이며 정상 캡슐 전 발동 가능성이나 새 재킷 원화 완료를 뜻하지 않는다.'],'decision':'정적 최종 후보 적합. 독립 검사/동결 후 새 시험 BIN에 통합하고 실제 동작 검증한다.','limits':['원표 순서를 배치한 정적 시트를 직접 본 것이며 실제 게임 실행/모든60Hz 관측 완료가 아니다.','모든 다른 모션과 호버까지 전체 미술 수용한 것이 아니다.'],'runtime_verified':False,'whole_project_complete':False}
out.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n','utf8');print(sha(out))
