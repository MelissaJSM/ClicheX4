from pathlib import Path
import json,hashlib
W=Path(__file__).resolve().parent;ROOT=W.parents[1];D=W/'nana_audit/ultimate_nova_repaint'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
files=sorted((D/'packed_nova_candidate_v1').glob('readback_*.png'))+sorted((D/'native_cycle_v1').glob('timeline_*.png'));assert len(files)==8
arc=D/'packed_nova_candidate_v1/PL02_U.ARC';assert sha(arc)=='1ec00de5164827c5dd5322b93b7060e11a1afbddD26bacb23f5b585e63715195'.lower()
out=W/'root_review_checkpoint146.json';assert not out.exists()
result={'checkpoint':146,'candidate_sha256':sha(arc),'actually_viewed_files':[{'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p),'actually_viewed':True}for p in files],'observations':['노바213..220 최종재추출4판과 원표106 순서4판을 직접 열람했다.','213/215 준비의 새 머리/의상 세부,215높은팔,217의 구별되는 신발과 하체를 확인했다.','새몸 외곽에 맞춘218/220가림·219실루엣의 정적 연결에서 추가 확정 잘림이나 몸 분리를 찾지 못했다.'],'limits':['효과색은 고정 팔레트 정적 표시이며 실제CLUT 시간변화/블렌딩/이벤트/물리의 검증이 아니다.','실제 노바 발동과 모든60Hz표시 검증은 미실행이다.'],'stage':'정적 미술검토; 독립검사/동결 후 시험본 통합 가능','whole_project_complete':False}
out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n','utf8');print(sha(out))
