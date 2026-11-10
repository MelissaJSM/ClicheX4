from pathlib import Path
import json,hashlib
W=Path(__file__).resolve().parent;ROOT=W.parents[1];D=W/'root_nana_lowhp';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
paths=[D/'packed_lowhp01'/f'readback_{i}.png' for i in (1,2)]+[D/'joint_layers03'/f'partial_{i}.png' for i in (1,2,3)]+[D/'native_sequence01'/f'{form}_id6_ordered.png'for form in('base','fourth')]
p=W/'root_review_checkpoint111.json';assert not p.exists()
p.write_text(json.dumps({'root_actually_viewed':[{'path':q.relative_to(ROOT).as_posix(),'sha256':sha(q)}for q in paths],'arc_sha256':sha(D/'packed_lowhp01/PL00_U.ARC'),'findings':['재추출2판·부분파츠3판·원표6 순서2판을 루트가 직접 열람했다. 새 머릿결·검은 옷 음영·무릎/발 윤곽을 대기와 비교했다. 입을 여는6개의 참조는 동일 몸체의 작은 입 변화로 이어지며 상하체 호흡은 함께 움직인다.','초기 joint02는 몸통만 착용할 때 베일의 위 조각이 떠 보였으므로 제외했다. 최종 joint03은 기존 다리 파츠 소유인 뒤 베일을 연속된 영역으로 묶었고 부분파츠 비교에서 그 조각이 남지 않음을 확인했다.','동일한 새 기본형의 권총/손을 두 의상에 등록하고 새 포스 맨다리를 같은 행에서 제한된2px 이내로 정합했다. 이전의 뭉개진 얼굴/다리를 덮어쓴 것이 아니다.'],'limits':['네이티브 원순서 정지판 및 자동재생 검사이며 실제 게임 저체력 발동 증거는 아직 없다.','전신 비례/윤곽 추가 확정 결함을 이번 비교에서 찾지 못했으나 전체 미술 완료·모든실기·사용자수용을 주장하지 않는다.'],'runtime_verified':False,'final_user_accepted':False},ensure_ascii=False,indent=2)+'\n','utf8');print(sha(p))
