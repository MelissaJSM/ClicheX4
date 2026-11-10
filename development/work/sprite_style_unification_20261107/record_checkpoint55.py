from pathlib import Path
import hashlib,json
W=Path(__file__).resolve().parent; ROOT=W.parents[1]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
pages=[W/'shibuki_audit/base_run_common01'/f'comparison_{i:02}.png' for i in range(5)]+[W/'nana_audit/rising_repaint/leg_edges_registered_v1/comparison.png']
r={'art_review_images':[{'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p),'root_actually_viewed':True} for p in pages],
 'findings':['시부키 공통 새머리와 포스 의상 합성5판 직접 열람. 머리 윤곽·눈·의상 연결이 유지된 방향이다.','나나 포스 다리 국소 재작화 등록1판 직접 열람.102 뒤 종아리·다리사이와231 그늘선 식별이 개선되었고 방향을 수용한다.'],
 'limits':['후보 단계로 최종 사격/권총/접점 및 재추출 검토가 남아 있다.','현재 통합 BIN 적용이나 실제 게임 검증을 뜻하지 않는다.'],'final_user_accepted':False}
p=W/'root_review_checkpoint55.json';assert not p.exists();p.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n','utf8');print(sha(p))
