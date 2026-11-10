from pathlib import Path
import json,hashlib
W=Path(__file__).resolve().parent;ROOT=W.parents[1];H=W/'shibuki_audit';D=H/'prepared_vehicle_head_base01';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
files=[H/'vehicle_head_base_native02/comparison.png']+[D/n for n in('base_readback_00.png','base_readback_01.png','fourth_readback_00.png','fourth_readback_01.png','ownership_184.png','ownership_196.png')]
arc=D/'PL00_U.ARC';assert sha(arc)=='4ceab054c4fa9170a0e785fb00baa01f05afaceb4d2dfc2dcc4e80eab30ee36f'
data={'checkpoint':163,'candidate':arc.relative_to(ROOT).as_posix(),'candidate_sha256':sha(arc),'actually_viewed_files':[{'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p),'actually_viewed':True}for p in files],'observations':['기본/포스 작은머리19개에서 대기 기준의 머릿결과 포스 검보라/금색 옆장식을 확인했다.','크기13×15·기존144알파·눈 기준점을 유지하며 새 원화의3/5개 외부 픽셀은 내부 상세화 범위에서 제외한 후보다.','전체 재추출4판과 부분 조합2판에서 추가 확정 절단이나 고립점은 찾지 못했다.'],'limits':['조종석 실제 플레이는 아직 미실행이다.','현재 수용된19동형 작은머리 정책을 유지하며 원US의5/6개 크롭 복원 작업이라고 세지 않는다.'],'runtime_verified':False,'all_character_work_complete':False}
p=W/'root_review_checkpoint163.json';assert not p.exists();p.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n','utf8');print(sha(p))
