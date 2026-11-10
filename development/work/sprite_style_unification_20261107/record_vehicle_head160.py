from pathlib import Path
import json,hashlib
W=Path(__file__).resolve().parent;ROOT=W.parents[1];H=W/'shibuki_audit';D=H/'prepared_vehicle_head_ultimate01'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
files=[H/'vehicle_head_ultimate_native02/comparison.png']+[D/n for n in('before_readback_00.png','before_readback_01.png','after_readback_00.png','after_readback_01.png','ownership_184.png','ownership_196.png')]
arc=D/'PL02_U.ARC';assert sha(arc)=='a0629d169d6b5a0d88f31faa5dc4866c7fef99245b278caedc92f523acb3f024'
data={'checkpoint':160,'candidate':arc.relative_to(ROOT).as_posix(),'candidate_sha256':sha(arc),'actually_viewed_files':[{'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p),'actually_viewed':True}for p in files],'observations':['작은 차량머리19개에서 대기 기준의 금색 고글과 머릿결 구분을 확인했다.','직접 본 획득 전/후와 부분 조합판에서 새 확정 절단·고립점을 찾지 못했다. 기존13×15 크기와 눈 기준점은 유지하며 윤곽1픽셀 추가/1픽셀 제거는 기록된 차이다.'],'limits':['조종석의 실제 차량 플레이 검증은 미실행이다.','원US의 여러 얼굴 크롭 복원이 아니라 현재 수용된 시부키의19동형 작은 머리를 상세화한 후보다.'],'runtime_verified':False,'all_character_work_complete':False}
p=W/'root_review_checkpoint160.json';assert not p.exists();p.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n','utf8');print(sha(p))
