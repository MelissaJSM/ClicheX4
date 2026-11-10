from pathlib import Path
import json,hashlib
W=Path(__file__).resolve().parent;ROOT=W.parents[1];H=W/'shibuki_audit';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
ps=[H/'ultimate_return_pack02'/n for n in ('before_readback.png','after_readback.png','partial_156.png','partial_157.png','partial_158.png')]+[H/'ultimate_return_sequence01'/f'{form}_id{i}_ordered.png'for form in ('before','after')for i in(3,40)]
p=W/'root_review_checkpoint122.json';assert not p.exists()
p.write_text(json.dumps({'root_actually_viewed':[{'path':q.relative_to(ROOT).as_posix(),'sha256':sha(q)}for q in ps],'candidate_sha256':'f40f33969d488af9db8c7d99b6bf4a78ad6e5542883bff63116fa26778de4cdc','findings':['얼티밋 전후156 새머리·몸통·발 디테일과 두 의상 구분이 대기 기준과 이어진다.','157발광 윤곽,158원래 전송효과와 새몸의 위치를 정지 순서판에서 확인했다.','손끝2px 안쪽/위 차이는 귀환 자세의 외부접점이 없으므로 강제 팔 연장 사유로 삼지 않았다.'],'limits':['원표3/40은 정지 순서판으로 직접 열람했다. 연속 애니메이션 직접 시청이나 게임 스테이지 클리어 검증이 아니다.','전체 캐릭터 미술 완료 및 사용자 최종 수용은 아니다.'],'runtime_verified':False,'final_user_accepted':False},ensure_ascii=False,indent=2)+'\n','utf8');print(sha(p))
