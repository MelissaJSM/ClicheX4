from pathlib import Path
import json,hashlib
W=Path(__file__).resolve().parent;ROOT=W.parents[1];H=W/'shibuki_audit'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
files=sorted((H/'chaser_base_pack03').glob('*readback_*.png'))+sorted((H/'chaser_base_sequence01').glob('*ordered.png'))
assert len(files)==18
arc=H/'chaser_base_pack03/PL00_U.ARC'
assert sha(arc)=='3e11b7e6f6c58e6e175ba8a53278a8329440c160096bf89abdb9df334c3ef52d'
out=W/'root_review_checkpoint144.json';assert not out.exists()
result={'checkpoint':144,'candidate_sha256':sha(arc),'actually_viewed_files':[{'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p),'actually_viewed':True} for p in files],'observations':['기본형·포스아머13참조의 최종 재추출8판과 원순서10판을 직접 열람했다.','대기 기준 머리카락, 귀, 얼굴, 의상 윤곽을 유지하며 원래 Y 파생 이동으로 연결된다.','정적 재생에서 추가 확정 손목·몸통·발목 분리나 불필요한 체격 도약은 찾지 못했다.'],'limits':['실제 차량 지형/물리/효과가 합쳐진 실기 검사는 아니다.','모든 미술작업 또는 전체 프로젝트 완료로 세지 않는다.'],'stage':'최종 정적 미술 검토; 독립검사·동결 후 다음 시험본 통합 가능','whole_project_complete':False}
out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n','utf8')
print(sha(out))
