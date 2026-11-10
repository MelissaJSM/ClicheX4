"""Record the actual latest residual normal-color sheet review; no art approval by count."""
from pathlib import Path
import json,hashlib
D=Path(__file__).parent/'rin_extension';O=D/'remaining154_review';p=O/'manifest.json';j=json.loads(p.read_text('utf8'));ROOT=Path(__file__).resolve().parents[3]
notes={
 'air_saber':'213/215의 얼굴·커프와217..229의 앞치마·접힌 부츠에 큰 단색 면이 남는다.230..246의 대응 지상 자세도 목·어깨와 손 크기가 거칠다.공중·지상18개는 같은 대기 몸을 붙이지 않고 원래 손/짧은 자루와 검기 위치를 보존해 새 묘사가 필요하다.다음 우선4키는213/215/217/219다.',
 'air_spin':'160의 준비 자세와161..175의 구른9각도에 흰 머리·장갑·부츠가 뭉친다.회전 자체의 축소 투영은 유지하되 머릿결·소매와 접힌 다리 안쪽 면을 분리할 필요가 있다.검기 회전의 원점은 보호한다.',
 'arrival_body':'249/250의 곧은 몸통은 허리·치맛단·부츠가 지나치게 단순하고251..253은 수용 대기와 명암 연결이 약하다.247/248은 원래 섬광이므로 단색 자체를 결함으로 세지 않고 새몸 실루엣 동기화 대상으로 분리한다.',
 'hyouretsuzan':'132..139 여섯 고유 몸체에서 커프, 들린 겨드랑이와 앞치마의 면 분리가 약하다.135 머리·치마는 넓은 흰/파랑 면이며139 착지 뒤팔과 부츠도 단순하다.동일 표시12참조로 확장 가능하지만 별도 얼음무기 객체의 가림은 이 시트에 없다.',
 'idle':'0/1/2/146·147·148은 수용 기준인 호흡과 깜박임이다.고칠 대상으로 세지 않는다.',
 'ladder':'197/199/202의 손 높이와 몸 기울기는 각각 달라 유지해야 한다.옆머리·커프의 흰 면과 치맛단/긴 부츠 안쪽 명암이 단순하므로3키를 보완하고 exact사본9참조로 확장한다.',
 'raijingeki_shared':'101/103은 입·코가 앞으로 튀어 대기와 다른 둔한 얼굴로 보인다.87/91/93/105와낮은108/110/112/119/128도 큰 커프·치마·부츠 면을 정리해야 한다.86대기는 보존,88섬광은 몸체와 동기화로 분리한다.',
 'rakuhouha':'새182..185 양옆의177..181 준비 동작과186..189 회복은 다시 거친 얼굴·치마로 돌아간다.소매의 흰색 덩어리,186/188의 긴 단순 검은 팔을 보완해야 한다.177..181의 원구체와 방출 에너지는 보호하며 외부 생성에는 분리한 교체 몸체만 쓴다.',
 'rakuhouha_static_body':'정적23/24는 이미 새182/185 몸체와 동기화했고154까지 보존했다.새 미제작2그림으로 세지 않는다.',
 'ride_armor_head':'66..85 중19개 표시 머리는 눈 주변의 회색 면이 적고 후면75..77이 흰 원형으로 뭉친다.본체 없는 머리 표시는 정상이다.각도/표정별 마스터와 원점 변형을 먼저 분리해 조종석 안의 동일 크기를 유지한다.',
 'ride_chaser':'14..41의28참조는 기울기별 머리, 장식 펄럭임, 발·소매를 가진다.특히14..21의 넓은 머리/커프와22..29의 얼굴/앞치마가 단순하다.기울기3~4종 몸체를 먼저 구분하고 같은 몸체 위 펄럭임만 확장 가능한지 조사한다.차량에 가려지는 접점 실기는 별도다.',
 'run':'5/6은 현재 대기147과 같은 상세한 그림이다.새3/4와7..20 사이에서 보존한다.',
 'ryuenjin':'144/146의 낮은 시작 자세와156/158 회복의 흰 머리·커프·부츠가 새148..154와 다르다.146의 접힌 뒷다리가 뭉쳐 읽힌다.4키를 원손잡이·불꽃 시작점 고정으로 보완한다.',
 'shippuuga':'155/156/158의 접힌 하체와160..172의회전은 각도별 묘사가 여전히 단순하다.162/164후두부,166/168정면,170옆얼굴을 같은 머리로 대체해서는 안 된다.원상완/무릎과 이동 높이는 보존하고 머릿결·커프·치마를 보완한다.',
 'victory_return_body':'b1_0은 대기147 exact이므로 새 승리1..8과 함께 보존한다.'}
seen=0
for g in j['groups']:
 g['visual_findings']=notes[g['group']]
 for s in g['sheets']:
  assert hashlib.sha256((ROOT/s['path']).read_bytes()).hexdigest()==s['sha256'];s['actually_viewed']=True;seen+=1
assert seen==28
total=sum(len(g['remaining_body_or_head_refs'])for g in j['groups']);unique=sum(g['exact_display_unique']for g in j['groups']);assert total==161 and unique==129
j.update(normal_residual_sheets_actually_viewed=28,normal_residual_group_unique_displays=129,remaining_ledger_refs=161,normal_residual_visual_review_complete=True,black_residual_full_review_complete=False,full_visual_review_complete=False,user_accepted=False,runtime_verified=False)
j['limits']=['일반색 잔여28장만 이번 최신 ARC에서 실제 전수 열람했다.레드 잔여 전수 및 모든 게임 동작 실기는 미실행이다.','잔여161에는 대기/동일사본·섬광·정적2·탑승 머리가 포함되어161개 새전신 원화가 필요하다는 뜻은 아니다.','마지막 새13의 원래 그림과 잔여 전신의 exact/평행이동 동일 사본은0이다.유사한 각도만으로 새원화를 무작위 복제하지 않는다.','시트 idle0 라벨은 공통 함수의 표시이며 비교 데이터는 실제b0_147이다.']
p.write_text(json.dumps(j,ensure_ascii=False,indent=2)+'\n','utf8')
lines=['# 린154 이후 잔여 미술 검토','',f"작업 ARC `{j['source_sha256']}`의 일반색28장,그룹 내 고유표시129개를 직접 열람했다.장부상161참조는 재작화 개수가 아니며 전체 통일이나 전수실기 완료가 아니다.",'','공중검격213/215/217/219부터 순차 보완한다.모든검격은 짧은 자루·손·원래 검기 접점을 유지한다.그후남은공중검격/회전,뇌신격·질풍아,사다리·용염인회복,등장·낙봉파준비·차량 순으로 남은 단순 면을 줄인다.순서는 공유 구조와 원화 슬롯에 따라 조정한다.','']
for g in j['groups']:lines.append(f"- **{g['group']}**: {g['visual_findings']}")
lines+=['','현재 기준154와 전체 원표의실기준비는 별개다.이번에는 새그림 후보가 명확히남았으므로 완료보고로 대체하지 않는다.']
(O/'REVIEW.md').write_text('\n'.join(lines)+'\n','utf8');print({'viewed':seen,'remaining':total,'unique':unique})
