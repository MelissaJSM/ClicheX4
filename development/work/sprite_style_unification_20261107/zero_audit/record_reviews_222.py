"""Record actual image-tool observations; never infer art approval from tests."""
from pathlib import Path
import json,hashlib
D=Path(__file__).parent;ROOT=D.parents[2];H=D.parent/'shibuki_audit';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
p=D/'shibuki_ultimate_air_independent.json';j=json.loads(p.read_text('utf8'))
j.update(visual_review_pending=False,actually_viewed_readback_sheets=[{'path':str((H/'prepared_ultimate_air01'/f'{form}_readback_{i:02}.png').relative_to(ROOT)),'sha256':sha(H/'prepared_ultimate_air01'/f'{form}_readback_{i:02}.png')}for form in('before','after')for i in range(4)],visual_observations=[
 '재독출8판의 전후44표시를 이미지 도구로 실제 열람했다. 대기와 비교해 머리 층·옷깃·소매·옷단 명암이 구형의 큰 단색 면보다 세밀해졌고, 42/44 사격에서 위로 남았던 여분 팔은 보이지 않는다.',
 '51/52와53/54 착지 자세의 목·어깨·손목과 발목은 정지 그림에서 이어진다. 양 의상에서 같은 총열 모양과 발 접점을 확인했다. 회전/장면 배경 속 연속 플레이를 본 결과는 아니며 부분 아머 전체704조합의 육안 수용도 아니다.'
])
p.write_text(json.dumps(j,ensure_ascii=False,indent=2)+'\n','utf8')
O=D/'rin_extension/remaining222_review';p=O/'manifest.json';j=json.loads(p.read_text('utf8'))
viewed=[]
for g in j['groups']:
 for row in g['sheets']:
  actual=ROOT/row['path'];assert sha(actual)==row['sha256'];row['actually_viewed']=True;viewed.append(row)
assert len(viewed)==18
j['full_visual_review_complete']=True
j['scope']='후보222의 잔여 본체·머리를 정확 같은 표시만 묶어18시트 모두 대기와 실제 비교했다. 미완료93참조를 새 원화93장으로 해석하지 않는다. 대기·빈 참조·효과는 보존하며, 정적23/24는 이미 동기화된 별도 자원이다.'
p.write_text(json.dumps(j,ensure_ascii=False,indent=2)+'\n','utf8')
report={'source_arc_sha256':j['source_sha256'],'candidate_reviewed_but_not_integrated':True,'prepared_count':222,'prepared_count_includes_derived_and_candidate8':True,'source_ledger_unchanged':True,'all_remaining_sheets_viewed':18,'actually_viewed':viewed,'full_gameplay_verified':False,'new_art_complete':False,'findings':[
 {'group':'raijingeki_shared','priority':1,'next_keys':['b1_091','b1_093','b1_101','b1_105'],'observation':'검은 몸통과 앞치마가 넓은 단색 면으로 남고, 머리 안쪽 음영·커프·부츠 경계가 대기 및 새 지상검격보다 거칠다. 대기형86은 보존하고 나머지18참조를 정확 표시 기준9고유 자세로 줄여 재작화할 수 있다. 101/103,105/107 등은 정확 공유를 확인한 뒤 새 원화로 함께 확장한다. 묶음 이름만으로 실제 기술명을 확정하지 않는다.'},
 {'group':'rakuhouha','priority':2,'observation':'177~181의 구슬 및 광선은 효과이므로 보존한다. 그 뒤 몸체는 머릿결/등·치마의 명암이 단순하며,186/187 웅크림과188/189 복귀도 새182~185와 스타일 차가 남는다. 같은 표시186/187을 묶되 별도 효과를 새 그림에 합성해 보내지 않는다.'},
 {'group':'arrival_body','priority':3,'observation':'249~253의 닫힌 다리·몸통·머리가 새 승리/대기보다 단순하다. 247/248은 흰 섬광이므로 자체 디테일 추가 대상이 아니며 몸체를 바꿀 때 기존 생성 규칙으로만 동기화한다.'},
 {'group':'ride_chaser','priority':4,'observation':'28참조에 네 기울기의 전신 및 뒤쪽 장식 변화가 보인다.14/22/30/38을 대표 후보로 삼을 수 있지만 손·좌석·발 접점과 장식 차이의 실제 소유를 먼저 검증해야 하므로 아직4장으로 충분하다고 확정하지 않는다.'},
 {'group':'ride_armor_head','priority':5,'observation':'19개는 조종석 위에 표시되는 머리 조각이다. 몸통이 없는 것을 누락 아트로 세지 않는다. 머릿결의 큰 청색 면/간략 얼굴은 보완 후보지만 실제 조종석에 들어가는 크기와 각도를 보존해야 하며 대기 머리를 일괄 붙이지 않는다.'},
 {'group':'idle_and_run','priority':6,'observation':'대기0/1/2/146/147/148은 기준안으로 보존한다.5/6은 대기와 닮은 준비자세여서 전신 또는 하체가 정확히 같은지 추가 비교한다. 단지 남은 목록에 있다는 이유로 이미 세밀한 머리를 다시 그리지 않는다.'},
 {'group':'blank_and_static','priority':None,'observation':'b1_000은 완전 빈 표시라 원화 제작 대상이 아니다. static23/24는 기존52단계에서 새 낙봉파 몸체로 이미 동기화되어 있고 후보222에서도 보존됐다.'}],
 'reuse_audit':'exact_baseline_aliases.json에서 남은 전신을 기존 새 마스터의 단순 평행이동으로 대체할 수 있는 경우는 없었다. 같은 각도라는 시각적 추측만으로 머리나 몸을 재사용하지 않는다.',
 'limitations':['18판은 일반 팔레트 잔여 시트다. 블랙/레드 차이는 별도 새 제작 단계에서 재검수한다.','실제 게임에서 탑승 조종석 가림·효과 좌표를 확인한 결과가 아니며 기술별 원래 순서도 입력 준비 시 다시 연결한다.','루트가 아직 Rin222 새8의 최종 미술 검토를 하지 않았으므로 공식 누적 장부는214 그대로다.']}
(O/'visual_review.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf8')
print(json.dumps({'shibuki_report_sha256':sha(D/'shibuki_ultimate_air_independent.json'),'rin_remaining_sheets':len(viewed)}))
