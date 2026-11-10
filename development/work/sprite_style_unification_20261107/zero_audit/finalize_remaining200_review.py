"""새200 기준 잔여 일반22시트 실제 미술 열람 결과."""
from pathlib import Path
import json,hashlib
D=Path(__file__).parent/'rin_extension/remaining200_review';p=D/'manifest.json';j=json.loads(p.read_text('utf8'));rows=[]
notes={
'arrival_body':'249/250 세워진 다리와251/252/253 준비자세의 부츠·커프가 넓은 흰 면으로 남는다.247/248은 그 몸체의 빛 실루엣이라 본체 확정 후 동기화해야 한다.',
'idle':'0/1/2/146/147/148은 수용 대기 묶음으로 유지한다. 새 원화 수를 늘리기 위한 교체 대상이 아니다.',
'ladder':'197/199/202의 앞치마·양팔 커프·신발 명암이 대기 및 새 공중보다 단순하다. 손 접점과 떠 있는 반대 다리 자세를 유지한3키가 필요하다.',
'raijingeki_shared':'91/93/101/105 준비·회복의 부츠,108/110/112/119/128 검격의 긴 맨팔과 넓은 흰 소매/다리 면이 새3타보다 단조롭다.86은 대기 복제라 보존 가능하다. 원 검기·손 중심을 분리해 후속 원화를 제작한다.',
'rakuhouha':'177..181 본체의 부츠/커프·머리 세부가 구형이며 효과가 합쳐져 있다.186..189의 낮은 준비/회복도 단순하다. 효과를 별도 의미 마스크로 보호한 뒤 본체만 새로 그려야 한다.',
'rakuhouha_static_body':'23/24는 새182/185 몸체와 이미 동기화한 정적 효과이며 새 원화 미작업으로 세지 않는다.',
'ride_armor_head':'66..85의19머리는 차량 가림 전용 소형 자원이다. 단순 크기 확대 대신 동일 방향의 정밀 머리결/눈 명암과 콕핏 가림 접점을 재검토한다. 현 시트는 차량 합성이 없어 최종 체형판정을 보류한다.',
'ride_chaser':'14..41의 기울기3군에서 넓은 흰 무릎/부츠·단순 앞치마와 커프가 남는다.28개 별개 전신보다 몸체 기울기·리본 파생의 실제 공유를 먼저 조사해 정확한 대표키로 새 원화를 제작한다.',
'run':'5/6은 수용 대기에 가까운 정지 전환으로 유지 가능하다. 별도 전신 재제작 우선순위가 아니다.',
'ryuenjin':'146 웅크림과156 공중복귀/158 지상복귀의 커프·치마·다리 흰 면이 새148..154와 차이 난다.다음 첫페이지에 세 키를 넣는다.',
'shippuuga':'155/156/158 낮은 돌진과160..172 방향 회전의 커프/부츠/치맛단이 새 대시에 비해 단조롭다.반대 방향 머리를 정면 대기 복제로 덮지 않고 각도별 새 원화를 제작한다.',
'victory_return_body':'b1_0은 대기 복제이므로 신규 전신 교체보다 유지 대상으로 본다.'}
for g in j['groups']:
 for s in g['sheets']:s['actually_viewed']=True;rows.append(s)
 g['visual_observation']=notes[g['group']]
assert len(rows)==22
j.update(normal_residual_sheets_actually_viewed=22,normal_residual_visual_review_complete=True,black_residual_full_review_complete=False,full_visual_review_complete=False,actual_runtime_verified=False,user_accepted=False,limits=['이번22장은 남은 본체/머리 일반 팔레트의 실제 정적 열람이다.현재200 전체와 효과/부분VRAM 전체를 다시 본 검사라고 주장하지 않는다.','레드는 새200 변경14시트에서 확인했으나 잔여군 전수를 별도로 열람하지 않았다.','기존315 장부에는 수용 대기·효과·차량 일부자원/중복이 포함되어 남은 수가 새 원화 필요 수와 같지 않다.'])
p.write_text(json.dumps(j,ensure_ascii=False,indent=2)+'\n','utf8');print(len(rows))
