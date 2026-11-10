from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parents[4]
D=Path(__file__).parent
N=D.parent.parent/'nana_audit/ultimate_ceremony_repaint'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
rel=lambda p:p.relative_to(ROOT).as_posix()
paths=[N/'first_registered_v2/comparison_1.png',N/'first_registered_v2/comparison_2.png',
       N/'second_registered_v1/comparison_1.png',N/'second_registered_v1/comparison_2.png',D/'current_pair_diff.png']
report={
 'scope':'나나 Ultimate 등장 새 133/135/136/137의 초기 등록 그림과 현재 138/139 관계의 정적 미술 관찰. 원화/ARC/게임 변경 없음.',
 'actual_viewed_images':[{'path':rel(p),'sha256':sha(p)}for p in paths],
 'coordinate_report':{'path':rel(D/'coordinate_report.json'),'sha256':sha(D/'coordinate_report.json')},
 'observations':[
  {'refs':[133], 'note':'두 의상 모두 새 머릿결의 밝은 면/그늘 분리와 재킷 옷깃·신발 명암이 이전 큰 단색 면보다 선명하다. new fixed 열은 원래 바닥과 웅크린 무릎 높이를 유지한다. 마지막 eye registered 열은 몸 전체가 +1y 내려가므로, 눈 한 픽셀만을 위해 발을 내리는 것보다 고정 원화 열을 택하는 방향이 타당하다. 현재 판에서 새 목·무릎·발목의 명백한 절단은 발견하지 못했다.'},
  {'refs':[135], 'note':'새 가슴 의상/허리띠 및 뒤 머리 명암이 대기와 더 가까워졌다. 다리 폭은 낮은 자세 전후와 이어지며 이전보다 지나치게 긴 종아리로 읽히지는 않는다. 양폼 머리와 사지가 아직 독립 원화이므로 공통 몸체와 의상 의미 경계 정합은 별도 단계다.'},
  {'refs':[136,137], 'note':'재킷 지퍼·옷깃/맨팔과 피부 명암이 명확해졌고, 새 머리와 다리의 체형도 이 두 비교판에서 과하게 가늘거나 길어 보이지 않는다. 137은 손·권총이 머리 왼쪽에서 더 세로로 서 보이며 귀 높이와 눈 높이도 구형과 다르다. 전신을 눈에 맞춰 움직이기 전에 원 손·권총과 46px 효과선의 실제 접점을 별도 확인해야 한다. 이 비교판에는 원 효과가 아직 삽입되지 않아 접점 통과로 판정하지 않았다.'},
  {'refs':[138,139], 'note':'같은 원점의 y−1 대조에서 후폼 153px 차이는 얼굴 위치나 고유 다리 자세 차이가 아니다. 얼굴/귀/상부 머리는 왼쪽 머리 끝 2셀을 제외하면 동일하고, 나머지는 상의의 피부/검정 경계·아래 팔·허리띠와 옆으로 내려온 머리 명암에 집중된다. 다리와 신발은 완전히 같다. 알파 차이도 허리/옆팔의 4셀뿐이다. 별도 후폼 몸동작을 보존해야 한다는 근거로 이 153px를 사용하면 안 된다.'}
 ],
 'relation_decision_evidence':{
  'current_after_delta':{'total':153,'head_side':2,'world_y_minus14_to_minus5':57,'world_y_minus5_to_plus5':94,'alpha':4,'legs_y5_and_below':0},
  'historical_nana_baseline_both_forms_shift_exact':True,
  'original_US_shift_exact':False,
  'recommendation':'새 138의 양폼을 제작하고 139를 −1y로 전개하는 것은 과거 수용 Nana 제작정책의 유지로 설명할 수 있다. 원US의 138/139가 같은 그림이었다는 주장과 구분한다.'
 },
 'limits':['후속 common costume probe는 열람하지 않았다.','생성 원화 재양자화·새 GPU/MIPS·실기는 하지 않았다.','새 133~137의 정적 방향 의견이며 최종 패킹/연속 미술 수용을 뜻하지 않는다.']
}
(D/'visual_review.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf8')
print(sha(D/'visual_review.json'))
