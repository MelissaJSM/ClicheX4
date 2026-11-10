from pathlib import Path
import json,hashlib
W=Path(__file__).resolve().parent;ROOT=W.parents[1];D=W/'root_shibuki_hover';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
files=[D/f'body_layers_probe04/comparison_{n}.png'for n in(221,223,225,227,229)]
files += [D/f'shot_composed01/comparison_{n}.png'for n in(222,224,226,228,230)]
files += [D/f'shot_composed02/comparison_{n}.png'for n in(224,230)]
proofs=[W/'zero_audit/shibuki_base_hover_layers03_read01/report.json',W/'zero_audit/shibuki_base_hover_shots02_delta01/report.json']
def entry(p):return {'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)}
p=W/'root_review_checkpoint161.json';assert not p.exists()
data={'checkpoint':161,'targets':['root_shibuki_hover/body_layers_probe04','root_shibuki_hover/shot_composed02'],'actually_viewed_files':[dict(entry(p),actually_viewed=True)for p in files],'independent':[entry(p)for p in proofs],'observations':['기본/포스 호버5몸과 사격5의 얼굴·머리·의상 및 공통 다리 크기를 대기 기준과 대조했다.','불필요한 세 번째 팔은 제거되었고, 원래총구가짧은228은 팔을 굽혀 정본 버스터 모듈과 연결한다.','사격01에 남은 포스 손목/칼라의 잘못된 공통 빨강·흰색3셀을 반려하고02에서 포스 원화의 피부색으로 복구한 두 판을 확인했다.','224/230 외의02비교 그림은01과 같고, 기본형·공통 얼굴(원래총 겹침 제외)·하체·총 모듈은 보존한다.'],'limits':['게임 팔레트·고정좌표 조립 후보이며 아직 ARC 패킹/실기 완료가 아니다.','223 오른신발의 한 행 이동에는 겹침8픽셀이 있어 전신 무손실 평행이동이라고 부르지 않는다.','228은 원래 발사점에 놓은 총 모듈이 얼굴 사각형7셀과 겹친다. 원래짧은발사점에따른명시된예외다.'],'runtime_verified':False,'all_character_work_complete':False}
p.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n','utf8');print(sha(p))
