from pathlib import Path
import json,hashlib
W=Path(__file__).resolve().parent;ROOT=W.parents[1]
paths=[W/'nana_audit/rising_repaint'/p for p in ['ultimate_ground_feet_probe_v1/comparison.png','ultimate_costume_pair_probe_v6/comparison_1.png','ultimate_neck_audit_v1/source_neck.png']]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
r={'root_actually_viewed':[{'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)} for p in paths],
   'findings':['231의 새 신발/발목을1행 내린 접지판을 대기와 비교했다. 지면22에 맞고 정적 판에서 새 발목 단절은 발견하지 못했다.',
               '100 목~어깨/반대팔의 재킷색 잔여를 후폼 원화 피부와 검은 상의끈으로 연결한 v6를 확인했다. 머리/얼굴과 팔 사이 빈틈을 보존한 방향으로 패킹 진행 가능.'],
   'limits':['등록 후보의 정적 미술 검토이며 패킹 후 픽셀/원코드/실기 검사는 별도.','전 동작 최종 완료나 사용자 수용이 아니다.'],
   'final_user_accepted':False}
p=W/'root_review_checkpoint71.json';assert not p.exists();p.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n','utf8');print(sha(p))
