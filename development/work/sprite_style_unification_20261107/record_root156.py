from pathlib import Path
import json,hashlib
W=Path(__file__).resolve().parent;ROOT=W.parents[1];D=W/'nana_audit/base_nova_repaint'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
arc=D/'packed_nova_candidate_v1/PL00_U.ARC';assert sha(arc)=='94cf560530c87ac11a03c029a9b6e98be44c06ea6d30d6c5ce66204c8a8e3cb3'
paths=[D/'preparation_effect_probe_v2'/f'{n}.png'for n in('comparison','partial')]+[D/'packed_nova_candidate_v1'/f'readback_{n}.png'for n in range(1,4)]+[D/'native_cycle_v1'/f'timeline_106_{n}.png'for n in range(1,5)]
out=W/'root_review_checkpoint156.json';assert not out.exists()
data={'checkpoint':156,'candidate':arc.relative_to(ROOT).as_posix(),'candidate_sha256':sha(arc),'actually_viewed_files':[{'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p),'actually_viewed':True}for p in paths],'observations':['기본/포스 새 준비·돌진213/214/215/216/217/220의 최종 재추출3판과 원표106 순서4판을 직접 확인했다.','기본 곱슬 머릿결·모자·검은 주름/신발과 포스 베일·치맛단·맨다리 표현이 종전 평면 덩어리보다 세밀해졌다. 원효과 속에서도 추가 확정 머리/손발 절단은 보이지 않는다.','head5 원창 범위와 뒤베일 leg8 재분배2판에서 전체 의상은 동일하게 보이며 일부 아머만 착용한 경우에도 추가 확정 분리/옛 머리 중복은 찾지 못했다.','214 외부 효과,216 별칭,218/219 기존 에너지면,220 몸과 외부 효과를 구분했다. 에너지의 전체 크기를 캐릭터 체격으로 평가하지 않는다.'],'decision':'정적 최종 후보 적합. 독립 검사/동결 후 새 RN 시험본에 통합한다.','limits':['정적 원순서판 직접 열람이며 실제 게임/모든60Hz 관측 증거가 아니다.','모든 부분 아머 조합을 직접 눈으로 본 것은 아니며 일부판과 별도 수치 검사를 구분한다.'],'runtime_verified':False,'whole_project_complete':False}
out.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n','utf8');print(sha(out))
