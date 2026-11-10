from pathlib import Path
import hashlib,json
D=Path(__file__).parent;N=D.parent/'nana_audit';P=N/'ultimate_standing_repaint/common_probe_v2';O=D/'nana_ultimate_standing89_97_visual01';O.mkdir(exist_ok=True)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
r={'source_comparison_sha256':sha(P/'comparison.png'),'manifest_sha256':sha(P/'manifest.json'),'actually_viewed':[str(P/'comparison.png')],
 'observations':['비교판 두 행의 donor/common candidate/after idle을 직접 보았다. 89는 분홍 허리띠 아래 회백색 중앙 면이 대기보다 넓게 읽히지만 다리를 벌린 각도 및 손이 허리 옆에 놓인 자세도 다르다. 이 정적판만으로 과도한 의상 확대라고 확정하지 않는다.','97은 앞팔과 검정 상의 아래의 분홍 허리띠가 넓게 드러나며, 회색 면이 대기와 전혀 다른 큰 반바지 덩어리처럼 보이는 새 확정 결함은 찾지 못했다.','89/97의 candidate는 donor 의상 방향을 유지하고 새 팔/손목과 상체가 이어진다. 새 머리와 맨팔 사이의 재킷 소매 잔재로 확정할 조각은 이번 판에서 찾지 못했다.'],
 'recommendation':'허리 회백색을 면적 수치만 맞춰 잘라내지 않는다.89 중앙 면의 의상 의미는 source 확대와 원순서88→89→90에서 추가 확인하고 손·총·효과 등록을 진행한다.',
 'new_confirmed_defects':[],'limits':['한 장의 정적 의상 비교 의견이다. 원화 재구성·부분소유·접점·패킹·실기는 검사하지 않았다.','완성 후보 또는 사용자수용 판정이 아니다.'],'files_modified_outside_own_report':False}
(O/'visual_review.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n','utf8');print(sha(O/'visual_review.json'))
