from pathlib import Path
import json,hashlib
W=Path(__file__).resolve().parent;ROOT=W.parents[1];S=W/'nana_audit/ultimate_standing_repaint'
paths=[S/'packed_standing_candidate_v1'/n for n in ('readback_1.png','readback_2.png')]+[S/'native_cycle_v2'/f'timeline_{i}.png' for i in (91,104,105)]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
r={'root_actually_viewed':[{'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)}for p in paths],
'candidate_sha256':'0e69e9e3823c95bfce5b10746f77c587cd6f9e177cdd69b04938e868f3b77331',
'findings':['88/89/97 전후 의상의 새 머릿결과 얼굴·소매 명암이 이전 단색 덩어리보다 대기 기준에 가깝다.','손과 총의 접점, 다리 바닥 위치를 확인했다. 추가 확정된 몸체 분리나 크기 급변을 찾지 못했다.','88 원래 효과와 새 몸체의 정지 합성, 원표91/104/105 순서판을 직접 검토했다.'],
'limits':['원표는 정지 순서판 검토이며 연속 직접 시청이나 실기 검증이 아니다.','90/91은 이 후보에서 보존되며 별도 수정 진행 중이다.','전체 캐릭터 완료나 최종 사용자 수용이 아니다.'],
'runtime_verified':False,'final_user_accepted':False}
p=W/'root_review_checkpoint128.json';assert not p.exists();p.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n','utf8');print(sha(p))
