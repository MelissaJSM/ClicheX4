from pathlib import Path
import hashlib,json
W=Path(__file__).resolve().parent;ROOT=W.parents[1];D=W/'nana_audit/rising_repaint'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
pages=[D/f'{folder}/comparison_{i}.png' for folder in ('air_registered_v1','charge_registered_v1','recovery_ground_registered_v1') for i in (1,2)]+[D/'air_registered_v1/effect_contact.png']
r={'art_review_images':[{'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p),'root_actually_viewed':True} for p in pages],
 'findings':['기본/포스 라이징 후보6판과 효과 접점판1개 실제 열람. 새 머릿결과 의상 세부는 개선 방향이다.','포스101/102/231의 맨다리 바깥선이 대기보다 회색/옅다. 특히102 종아리 뒤선과231 오른다리 바깥선은 추가 검토/수정 필요.'],
 'decision':'아직 동결하지 않는다. 새 세부를 보존하면서 다리 윤곽의 색 등록과 고정 권총 모듈·발 접점을 보완한 후 재검토한다.',
 'limits':['후보 원화 등록 단계이며 게임 적용/실기 완료가 아니다.'],'final_user_accepted':False}
p=W/'root_review_checkpoint54.json';assert not p.exists();p.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n','utf8');print(sha(p))
