"""Record the visually checked original art intent for Nana arrival138."""
from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parents[3]
D=Path(__file__).parent;O=D/'nana_ultimate_ceremony_sources03';O.mkdir(exist_ok=True)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
rel=lambda p:p.relative_to(ROOT).as_posix()
images=[ROOT/'work/ver_rin_nana/nana_art/arrival_v1/generated.png',
        ROOT/'work/ver_rin_nana/nana_ultimate_armor/ceremony_v1/generated_first.png',
        D.parent/'nana_audit/ultimate_ceremony_repaint/settle_registered_v1/comparison.png']
paths=images+[
 ROOT/'work/ver_rin_nana/nana_art/arrival_v1/prompt.txt',
 ROOT/'scripts/normalize_nana_arrival.py',ROOT/'scripts/prepare_nana_fourth_ceremony_reference.py',
 ROOT/'scripts/prepare_nana_fourth_ceremony_art.py',ROOT/'scripts/prepare_nana_ultimate_ceremony.py',
 D.parent/'nana_audit/ultimate_ceremony_repaint/settle_registered_v1/registration.json']
report={
 'scope':'새 Nana Ultimate138의 화면 왼쪽 팔 의미를 과거 생성 원화·프롬프트·실제 등록 좌표와 대조한 읽기 기록. 새 원화/ARC/게임 수정 없음.',
 'sources':[{'path':rel(p),'sha256':sha(p)}for p in paths],
 'actual_images_viewed':[rel(p)for p in images],
 'historical_sources':[
  {'source':rel(images[0]),'layout':[3,2],'frame138_cell':4,'indexing':'row-major,0-based',
   'code_evidence':'normalize_nana_arrival.py는 첫5그림을133/135/136/137/138로 대응시킨다. 여섯째 낮춘양팔 대기는 보정용이고138이 아니다.',
   'prompt_meaning':'138은 권총팔을 머리 위로 수직으로 들고 총은 위를 향한다. 반대팔은 어깨/가슴 근처로 굽힌다.',
   'visual_observation':'아래가운데138은 화면왼쪽 팔/권총을 위로 올리고 반대팔을 가슴 옆으로 굽힌 모습이다.'},
  {'source':rel(images[1]),'layout':[3,2],'frame138_cell':0,
   'order':[138,156,204,205,206,207],
   'visual_observation':'첫셀138도 화면왼쪽 권총팔을 머리보다 높게 뻗은 모습이다. 밝은 가슴면만으로 팔 의미를 추측할 필요가 없다.',
   'pistol_contact_world_rect':[-15,-35,0,-23],
   'adjacent_hand_contact_world_rect':[-11,-23,-2,-20],
   'coordinate_rule':'과거160×160등록 CONTACTS138에서 원점80을 뺐다. 사각형 끝은 exclusive.'}
 ],
 'new_candidate':{
  'art_direction_observation':'새 머릿결/재킷·수영복 세부는 선명해졌지만 화면왼쪽 권총팔을 내려 낮춘 대기 자세로 바뀌었다.',
  'pose_issue':'역사138의 올라간 권총팔을 복원한 자세로 볼 수 없다.133→135→136→137→138의 팔올림 흐름에서138을 낮춘팔로 바꾸면 기존 제작 동작을 바꾼다.',
  'recommendation':'현재 낮춘팔138의 채택은 보류하고, 새 세밀한 머리/몸/발을 유지한 채 위로 든 팔·손·권총만 별도 원화로 보완한다. 기존 거친 몸체로 덮지 않는다.',
  'not_a_gameplay_test':True},
 'limits':['원US138 원몸체와 Nana의 승인된 권총 해석은 별개다. 이 보고서는 Nana 역사 원화의 의도와 현재 등록을 대조했다.',
           '136/137의46px 흰 선은 별도효과다. 해당 선을 권총 발사점에 강제로 연결할 근거는 없다.',
           '최종 새팔의 원점·게임 효과·순서 접점은 보완 후 별도 확인이 필요하다.']}
(O/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf8')
print(sha(O/'report.json'))
