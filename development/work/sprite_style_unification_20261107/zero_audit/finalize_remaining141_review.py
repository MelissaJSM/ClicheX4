"""Record the actually viewed residual sheets, without treating counts as art approval."""
from pathlib import Path
import json,hashlib
D=Path(__file__).parent/'rin_extension';O=D/'remaining141_review';p=O/'manifest.json';j=json.loads(p.read_text('utf8'))
notes={
 'ground_saber':'83/85/87/89/91(93동일)/105/107/130/133/134의 볼·앞머리와 큰 흰 커프, 치마·부츠의 내부 면이 수용 대기 및 새 첫타보다 단순하다. 원래 손·무릎·발 위치를 유지하며 전신 상세를 보완할 우선군이다.91/93 외 전신 동일/평행이동 공유 근거는 없다.',
 'run':'3/4의 얼굴·커프·치마가 새7..20과 다르다. 각각 별도 진입 자세를 유지하여 제작한다.5/6은 대기147 exact 사본이므로 보존한다.',
 'air_saber':'213..246의18몸체는 큰 흰 머리 면·두꺼운 커프·단순 치마가 남아 있다.213/215의 접힌 다리와219..229의 공중 회전 자세,230..246의 지상 대응 자세를 구분해야 한다.팔/손/원검기 접점이 서로 달라 idle 전신 붙이기로 대체하지 않는다.',
 'air_spin':'9각도에서 허리·소매·접힌 부츠가 검정/흰 면으로 뭉쳐 읽힌다. 작은 실루엣만으로 실패를 판정하지 않고 원래 구른 각도와 체형을 유지하며 내부 묘사를 보완한다.',
 'arrival_body':'249/250의 곧게 선 자세와251..253의 대기 전환은 얼굴·치맛단이 단순하다.247/248은 원래 섬광 실루엣이라 세부 부족 결함으로 세지 않으며 새 몸체와 동기화해야 한다.',
 'hyouretsuzan':'6개 고유 몸체(12참조)의 들어 올린 손과 웅크린 착지 자세에서 앞머리·커프·치마 상세가 단순하다.별도 무기 객체의 VRAM은 이 몸체 시트에 포함되지 않는다.',
 'idle':'0/1/2/146과147/148은 현재 스타일 기준의 호흡·깜박임이다.잔여 장부에 있어도 새 원화로 바꿀 필요가 있다는 뜻은 아니다.',
 'ladder':'197/199/202의3키(9참조)는 손잡기/공격 각도가 다르고 치맛단·부츠 명암이 단순하다.후면 새 사다리의 몸을 돌려 붙이지 않고3개 기존 자세를 보존하여 보완한다.',
 'raijingeki_shared':'정상 대기86과 섬광88을 분리한다.87/91/93/101/105 및 낮은 돌진108/110/112/119/128의 얼굴·커프·앞치마가 넓은 단색 면이다.101의 옆얼굴은 볼/턱이 앞으로 튀는 형태로 읽혀 다른 옆면 머리와 광학 비교가 필요하다.',
 'rakuhouha':'새182..185와 앞뒤177..181/186..189의 상세 차이가 크다.기존 에너지 구체·방출부를 그대로 분리 보존하고 손/손목·몸체를 새로 묘사해야 한다.원래 효과를 포함한 전체 PNG를 외부 원화 입력으로 쓰지 않는다.',
 'rakuhouha_static_body':'정적23/24는 이전52에서 갱신되어141까지 보존했다.메인 새 원화 참조 집계와 분리되어 남은 칸에 보일 뿐 미작업으로 세지 않는다.',
 'ride_armor_head':'19개 머리의 옆면과 피격/돌림 표정은 머릿결·눈 주변 명암이 적다.몸 없는 표시가 정상이며 차량 조종석 가림을 포함하지 않은 시트이므로 크기만으로 잘림을 단정하지 않는다.같은 각도/표정/원점 공유를 먼저 조사한다.',
 'ride_chaser':'28개의 기울기·머리·장식 변형이 모두 큰 흰 머리 면과 단순 소매/부츠를 공유한다.방향·기울기별 본체와 펄럭임을 분리해 원화 수를 줄일 가능성이 있으나 아직 정확 부분 공유를 입증하지 않았다.차량·승차 접점 실기는 별도다.',
 'ryuenjin':'새148/150/152/154 앞뒤의144/146/156/158에 단순 옆머리·커프·하체가 남는다.원불꽃과 손잡이 시작점이 핵심 보존 조건이다.',
 'shippuuga':'155/156/158의 낮은 돌진과160..172의 몸 회전은 서로 다른 각도다.뒤통수162/164,정면166/168,옆면170/172를 같은 머리로 대체하지 않는다.치마·소매·부츠 명암은 전반적으로 새 대기보다 단순하다.',
 'victory_return_body':'b1_0은 대기147과 정확히 같은 현재 그림이다.새 승리1..8과 구분하여 보존한다.'}
seen=0
for g in j['groups']:
 g['visual_findings']=notes[g['group']]
 for s in g['sheets']:
  f=D.parents[3]/s['path'] if False else Path(__file__).resolve().parents[3]/s['path']
  assert hashlib.sha256(f.read_bytes()).hexdigest()==s['sha256'];s['actually_viewed']=True;seen+=1
assert seen==30
j.update(normal_residual_sheets_actually_viewed=30,normal_residual_group_unique_displays=141,remaining_ledger_refs=174,normal_residual_visual_review_complete=True,black_residual_full_review_complete=False,full_visual_review_complete=False,idle_reference=147,user_accepted=False,runtime_verified=False)
j['limits']=['일반색 잔여30장만 전수 재열람했다.레드 전수 재열람·게임 실기 전체 완료는 아니다.','정적2와 대기·빛 형상·머리만 표시되는 탑승 자원도 잔여174에 포함되므로174개 새 전신 원화가 필요하다는 뜻이 아니다.','정확 같은 표시만 묶었다.원점이 다른 비슷한 자세나 손/효과가 다른 자세는 같은 것으로 계산하지 않았다.','시트 내부 idle0 라벨은 공통 보기 함수의 고정문구이며 실제 비교 기준은 b0_147이다.']
p.write_text(json.dumps(j,ensure_ascii=False,indent=2)+'\n','utf8')
lines=['# 린141 이후 잔여 미술 재검토','',f"기준 작업 ARC `{j['source_sha256']}`. 일반색 잔여30장(그룹 내 정확 표시141종)을 실제로 열람했다. 잔여174 장부 참조에는 정적2·대기·섬광·탑승 머리가 포함된다. 새 원화174장 필요 또는 전수 게임 검증 완료를 의미하지 않는다.",'','원본 전신의 정확/평행이동 관계를 현재 준비141과 대조했지만 새 원화를 그대로 확장할 남은 전신 사본은 없었다. 지상·회복·이동13참조 중91/93만 완전동일하다. 분석은 `sharing_analysis.json`에 있다.','','다음3페이지는83/85/87/89 →91/105/107/130 →133/134/3/4이다.12원화로13참조를 다루며 입력·프롬프트를 `next_after141.json`에 기록했다. 원화 생성 결과는 별도 후보이며 이 감사의 통과 범위로 선승인하지 않는다.','']
for g in j['groups']:lines.append(f"- **{g['group']}**: {g['visual_findings']}")
lines+=['','레드 전수 재열람, 차량/무기 객체의 동적 가림·좌표, 전체 게임 실기는 미실행이다. 수용 대기의 상세도를 맞추려는 후속 작업은 계속 남아 있다.']
(O/'REVIEW.md').write_text('\n'.join(lines)+'\n','utf8');print({'actually_viewed':seen,'remaining':174})
