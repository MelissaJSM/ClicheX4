from pathlib import Path
import json,hashlib
W=Path(__file__).resolve().parent;ROOT=W.parents[1];H=W/'shibuki_audit';out=W/'root_review_checkpoint147.json';assert not out.exists()
files=[H/f'nova_base_pack02/{form}_readback_{i:02}.png'for form in('base','fourth')for i in(0,1)]+[H/f'nova_base_pack02/partial_{i}.png'for i in(213,215)]+[H/f'nova_base_sequence01/{form}_preparation_order.png'for form in('base','fourth')]
out.write_text(json.dumps({'checkpoint':147,'candidate_sha256':'619032d0b81ffc50e5f5664ff1e3d0c077f226a7d5a8ccfac081be6a2126c6c5','actually_viewed_files':[{'path':p.relative_to(ROOT).as_posix(),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'actually_viewed':True}for p in files],'observations':['기본/포스 준비213..216 재추출4판, 부분조합2판, 원순서2판 총8판을 직접 열람했다.','대기 기준 머리·귀·헤어 세부와 의상별 소매/허리 장식을 확인했다. 부분조합의 추가 확정 몸 분리를 찾지 못했다.','원순서의217 돌진은 기존 그림이며 이번 준비4의 완료로 확대하지 않는다.'],'limits':['정적/오프라인 순서 검토이며 실제 노바·60Hz 전수·부분아머 실기 검증은 아니다.','입출력/저장순열/원코드 기술 검사는 별도 근거이며 이 보고서 자체가 대체하지 않는다.'],'stage':'정적 미술검토; 독립검사 및 동결 후 시험본 통합 가능','whole_project_complete':False},ensure_ascii=False,indent=2)+'\n','utf8')
print(hashlib.sha256(out.read_bytes()).hexdigest())
