from pathlib import Path
import json,hashlib
W=Path(__file__).resolve().parent;ROOT=W.parents[1];D=W/'root_nana_victory';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
paths=[D/'joint_targets01'/f'partial_{i}.png'for i in(1,2)]+[D/'packed_victory02'/f'readback_{i}.png'for i in(1,2)]+[D/'native_sequence01'/f'{form}_id39_ordered.png'for form in('base','fourth')]
r={'root_actually_viewed':[{'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)}for p in paths],'candidate_sha256':'90c614a7996d65ff71381ccc1f673cbfa13b84eccafec83c2e919010310b9239',
'findings':['204/205의 새 머릿결·옷 주름을206/207과 함께 확인했다. 전체에 동일한 굵은 테두리를 덧씌우지 않았다.','다리가 길어지고 발 위치가 내려갔던206 초안 두 종은 반려하고 세 번째 원화로 대체했다.207은 고정셀 원화의 위치만 y−5 등록하여 원래 눈·바닥에 맞췄다.','207의 머리는 원래 승리 자세에서 대기보다 높이 서는 위치를 따른다. 몸체 bbox 전체 축소로 손발을 왜곡하지 않았다.','부분아머 경계와 최종 재추출·원표39 정지 순서판에서 추가 확정 절단·외곽선 급변을 찾지 못했다.'],
'limits':['원표 정지 순서판 및 자동 재생검사이며 실제 게임 스테이지클리어 검증은 아니다.','모든 캐릭터 미술 완료나 사용자 최종 수용을 뜻하지 않는다.'],'runtime_verified':False,'final_user_accepted':False}
p=W/'root_review_checkpoint129.json';assert not p.exists();p.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n','utf8');print(sha(p))
