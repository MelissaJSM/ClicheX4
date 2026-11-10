from pathlib import Path
import json,hashlib
W=Path(__file__).resolve().parent; ROOT=W.parents[1];D=W/'root_nana_ladder'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
paths=[D/'joint_layers05'/f'partial_{i}.png' for i in range(1,6)]+[D/'packed_ladder07'/f'readback_{i}.png' for i in range(1,6)]+[D/'native_sequence01'/f'{form}_id{n}_ordered.png' for form in ('base','fourth') for n in (27,28,29,31,32,92)]
q=W/'root_review_checkpoint105.json';assert not q.exists()
q.write_text(json.dumps({'root_actually_viewed':[{'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)} for p in paths],
 'findings':['나나 기본/포스 사다리14의 재추출5판, 부분착용5판, 원순서12판을 직접 열람했다. 사다리 몸체에도 대기 기준의 머릿결·옷 명암·가느다란 외곽 표현이 남아 있고 완전착용/부분착용에서 추가 확정 손목·허리·베일 분리를 찾지 못했다.',
 '초기 머리 소유를 지나치게 좁게 제한한 joint03/04는 베일 끝이 뜨거나 어색한 조각이 남아 제외했다. 최신 joint05/packed07을 검토 대상으로 선택했다. 사격은 새149 머리·하체와 새 팔을 결합하고 정본 사랑이와 총구를 유지하여 전신 재생성으로 생긴 다리 길이 변화를 피했다.',
 '8개 원표38단계의 원래 호출수/분기를 대조한 시뮬레이터로 올라가기·내려가기·사격을 연결했다. 사다리를 벗어나 이동1로 넘어가는 자세도 비교했다. 각 상태의 방향·웅크림에 따른 높이 변화는 전체 몸체의 일률 축소와 구별했다.'],
 'limits':['직접 열람은 정지된 원순서 비교판이다. 자동 canvas 검증1526은 연속 영상을 모델이 시청했다는 뜻이 아니다.','실제 사다리 물리 이동·손발의 모든 접점·표93의 가변 충전시간·모든 부분파츠 조합의 실기·사용자 최종수용은 별도다.'],
 'arc_sha256':sha(D/'packed_ladder07/PL00_U.ARC'),'final_user_accepted':False},ensure_ascii=False,indent=2)+'\n','utf8');print(q.name,sha(q))
