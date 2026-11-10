from pathlib import Path
import json,hashlib
W=Path(__file__).resolve().parent;ROOT=W.parents[1];D=W/'nana_audit/ultimate_recoil_repaint';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
paths=[D/'packed_recoil_candidate_v1/readback_1.png',D/'native_cycle_v1/timeline_91.png']
r={'root_actually_viewed':[{'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)}for p in paths],'candidate_sha256':'ce61617f541fd59a5a3ab0b26bba6ce88cc7740bf5f9d4719c9acb129783c8d0','findings':['90/91의 머릿결·소매 접힘과 팔 경계를 새89와 이어 확인했다. 추가 확정 절단이나 얼굴/몸 크기 급변을 찾지 못했다.','91 수평 권총은 수용된85 모듈의X−2 정책을 따른다. 미술상 옛 두꺼운 총보다 정본 크기와 이어진다.'],'limits':['91 단독 새발사 발생 또는 실제 총구 좌표를 새로 검증했다는 주장이 아니다.','원표 정지 순서판이며 게임 실기와 연속 직접 시청은 별도다.','전체 미술 완료나 최종 사용자 수용이 아니다.'],'runtime_verified':False,'final_user_accepted':False}
p=W/'root_review_checkpoint130.json';assert not p.exists();p.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n','utf8');print(sha(p))
