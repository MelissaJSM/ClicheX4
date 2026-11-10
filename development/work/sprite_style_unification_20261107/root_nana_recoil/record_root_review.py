from pathlib import Path
import json,hashlib
D=Path(__file__).resolve().parent;W=D.parent;ROOT=W.parents[1];sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
paths=[D/'joint_layers02/comparison.png',D/'joint_layers02/partial.png',D/'packed_recoil03/readback_1.png',D/'native_sequence01/base_id91_ordered.png',D/'native_sequence01/fourth_id91_ordered.png']
p=W/'root_review_checkpoint121.json';assert not p.exists()
r={'candidate_sha256':sha(D/'packed_recoil03/PL00_U.ARC'),'root_actually_viewed':[{'path':q.relative_to(ROOT).as_posix(),'sha256':sha(q)}for q in paths],'findings':['새90/91 머릿결·소매·옷 주름을 대기와 비교했다. 몸 전체 확대/축소 없이 원래 넓은 접지 자세를 유지한다.','부분파츠02에서01의 윗베일 돌출을 head5로 옮겨 해결했다. 전체포스/기본RGBA를 바꾸지 않고 의미 소유를 바꾼 것이다.','91은 수용85의20texel8px 권총을 x−2 위치에 정합했다.90은 새그림의 대각선 총/손 공유.','원표91 일곱 단계 두폼에서 준비→후속→대기 연결을 정지 순서판으로 검토했다.'], 'limits':['연속 동영상을 직접 시청한 증거가 아니다. 오프라인262canvas 순서/픽셀 검사는 별도이다.','신규90/91은 아직 BIN/RAM/실제 화면에서 검증하지 않았다.','전체 캐릭터 미술 통일 완료가 아니다.'],'runtime_verified':False,'final_user_accepted':False}
p.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n','utf8');print(sha(p))
