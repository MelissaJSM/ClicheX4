"""Record the actually viewed 58 boards; never infer art acceptance from metrics."""
from pathlib import Path
import json, hashlib, collections

D = Path(__file__).resolve().parent
O = D / 'rin_extension/all_unique_review52'
load = lambda p: json.loads(p.read_text('utf8'))
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
inventory = load(O / 'inventory.json')
assert inventory['source_sha256'] == '10f1cc28662a8ceae3b3e00c305fdbeeb0e7e16bc21c13d65a05fadc19e19ca3'
progress = load(D / 'rin_extension/progress_ledger.json')
new = set(progress['new_art_prepared_refs'])

# These are visual classifications of each representative on the viewed sheets.
# Exact cropped-index aliases inherit the same kind, not an art-quality verdict.
effects = {
3: [53,54,55], 4: [56,57,58,59,60,64,66],
5: [68,70,72,74,76,78,80], 6: [84,86,88,90,92,94],
7: [96,98,100,102,103,104,106,108], 8: [110,112,114,116,118,120],
9: [122,124,126,128,129], 11: [157,159,161,163],
12: [165,167,169,171,173], 14: [198,200,203,205,207,209,211],
15: [214,216,218,220,222], 16: [224,226,228], 17: [245],
18: [9,10], 19: [11], 20: [52,55], 21: [58,60,62,64],
22: [89,90,92,94,97,100,102], 23: [104,106,109,111,113,115,117],
24: [118,120,121,123,124,126,127], 25: [145,147,149,151],
26: [153,155,157,159,162,164], 27: [166,168,170,172,174], 28: [176],
}
head_only = {66,75,77,78,80,81}
flash_only = {'b0_138','b0_142','b0_143','b0_247','b0_248','b1_008','b1_088'}
notes = [
'대기와 초기 이동 3/4/5, 새 달리기 7..13 비교. 새 원화의 눈·커프·치맛단 묘사가 분명하다. 구형4는 볼의 흰 면과 어두운 몸통이 단순하다. 3/5는 대기와 가까워 일괄 재작화 대상으로 강제하지 않는다.',
'새 달리기14..20와 새 공중21..25를 대기와 비교했다. 세부 표현이 이어진다. 17/18의 좁은 옆모습과 보폭은 자세 차이이므로 전체 면적만으로 마른 결함이라 하지 않는다. 실제 연결 재생 검증과 별개다.',
'새 공중26..33·35와 구형34/36/37/38의 얼굴·소매 대비를 확인했다. 구형34의 얼굴과 가슴,36/38의 흰 머리 면과 커프가 단순하다. 착지·벽 진입의 나머지 키를 같은 품질로 이어야 한다.',
'새39/40·44·46..52에 비해 구형41..43의 머리·목,45의 작은 평면 얼굴과 커프가 덜 세밀하다. 53..55는 순수 빛기둥이며 몸체 디테일 부족과 구분한다.',
'56..60은 등장 에너지. 새61에 비해62/63/65는 흰 얼굴 면, 가는 목과 팔, 단색 몸통이 남는다. 첫 지상 공격 계열의 후속 원화가 필요하다.',
'67/69·71·73/75/77/79/81·82는 얼굴과 어깨의 면 분리가 약하고 부츠 내부 주름이 적다. 곡선 검기68/70/72 등은 별도 이펙트로 보존한다.',
'83/85/87/89/91/93은 얼굴 흰 면, 가늘고 어두운 팔·허리, 단순한 흰 부츠 명암이 대기와 다르다. 잔여 검기 파편에는 같은 미술 기준을 강제하지 않는다.',
'새95/97/99/101은 이번 세부 표현 기준에 가깝다. 구형105/107은 얼굴·커프·가슴 구조가 다시 단순해진다. 96..104와106/108은 검기다.',
'109..127 홀수의 3타 몸체가 우선 수정 대상이다. 넓은 흰 얼굴, 가는 상완·허리, 내부 음영이 적은 부츠가 보인다. 검기110..120은 몸체와 분리해야 한다.',
'130..134의 전환 몸체와135/136 피격 몸체에서 얼굴·가슴·부츠의 단순함을 확인했다.136의 전기 선은 의도된 효과이며 몸체 외곽 결함으로 세지 않는다.',
'137/139/140/141 피격은 얼굴과 어깨·허리·정강이가 단순하다.138/142/143은 섬광/실루엣,144/145는 색/외곽 효과를 포함한 몸체다.149..151 저체력은 웅크린 높이 자체보다 얼굴·커프·다리 명암을 보완해야 한다.',
'152..154 저체력,155/156/158 낮은 공격,160/162/164 회전 전환을 확인했다.156은 얼굴과 몸통,162는 후두부 흰 덩어리와 어두운 등 면이 특히 단순하다.157/159/161/163은 효과다.',
'166/168 정면 전환은 얼굴·허리·치마가 평면적이다. 새174..177은 머릿결과 의상 표현이 개선됐다. 반대 방향에는 대기 머리를 그대로 붙이지 않고 해당 시점을 재작화해야 한다.',
'178..194 후면 몸체에서 반복되는 큰 흰 머리 면과 톱니 모양 끝, 단색 등·치마가 새174와 강하게 대비된다.191 등의 좁고 긴 지지 다리는 자세 차이를 고려하되 부츠 구조가 약한 점은 개선 대상이다.',
'195/196 후면,197/199/201/202/204/206/208/210/212 공중 공격을 확인했다. 후면 머리와 앞모습의 볼·전완·부츠가 단순하다. 손과 짧은 도구 연결점을 유지하며 자세별 그림이 필요하다.',
'213/215/217/219/221/223 공중 공격의 몸통·팔이 대기보다 가늘고 얼굴이 작은 흰 덩어리로 읽힌다. 원래 손 위치와 몸의 기울기를 유지하며 목·상완·의상 면을 다시 그리는 대상이다.',
'225/227/229의 올린 팔·허리,230..238 지상 몸체를 확인했다. 특히229는 팔과 허리가 가는 선처럼 읽힌다. 발 간격이나 공격 자세 자체를 일괄 확대하지 말고 해당 부위를 대기 체형과 맞춰야 한다.',
'240/242/244/246과249..252 등장 몸체의 옛 얼굴·커프·다리 묘사를 확인했다.247/248의 흰 실루엣은 정상 효과다.249/250은 옆모습이지만 긴 목과 단순한 몸통이 남아 등장 원화 보완과 효과 동기화가 필요하다.',
'새 승리 b1_5와 구형1/2/3/4/6의 차이가 뚜렷하다. 이웃 프레임은 긴 목과 가는 팔·지지 다리, 평면 부츠가 남는다. 귀환7의 몸체와8의 섬광도 후속 동기화 대상이다.9/10은 에너지다.',
'탑승14..31은 얼굴의 흰 면, 소매·앞치마·부츠 접힘이 단순하다. 앉은 높이는 정상 자세 차이이며 차량 손잡이·좌석·발 접점은 그대로 보존해야 한다.11은 빛기둥이다.',
'탑승32..41과 벽 공격50/51/53/54/56을 확인했다. 벽의 얼굴·목·전완·커프는 새39보다 묘사가 약하다. 벽 손과 도구 연결점을 유지한 새 원화가 필요하다.',
'벽 공격57/59/61/63/65도 머리·커프·몸통 표현이 단순하다.66..85는 탑승용 머리 조각이며 몸체 누락으로 오인하면 안 된다. 머리 조각 자체의 흰 면·턱·눈 묘사는 같은 방향의 세밀한 새 머리와 정합할 후보이다.',
'88은 섬광,89/90/92/94/97/100/102는 효과.91/93/101/103 몸체는 넓은 흰 얼굴과 단순한 커프·다리 명암이 남는다. 효과와 몸체를 따로 제작 범위로 분리한다.',
'105/107·108/114/116/125·110·112/122 뻗는 공격에서 손과 팔의 연결점은 보이나 얼굴·옷·종아리의 면 분리가 약하다. 긴 검기와 전기 구는 별도 효과다.',
'119·128..131·133..137 몸체를 확인했다. 특히133/135의 올린 팔과 허리가 가늘며, 흰 얼굴·커프·부츠 구조가 단순하다. 무기 손/끝점은 유지하며 재작화할 대상이다.',
'138/139..144·146·148/150/152를 확인했다. crouch의 작은 높이는 자세 차이지만 얼굴·가슴·부츠 묘사는 약하다. 상승 후면148/150/152는 큰 흰 머리 면과 가는 팔·몸통이 강하다. 불꽃/검기145/147/149/151은 분리한다.',
'154의 후면 상승,156/158 전환,161/163 회전 몸체를 확인했다. 후면 머릿결과 정면 커프·가슴 명암이 단순하다. 회전은 접힌 자세로 작아지는 것이 정상이나 옷과 팔을 읽을 구조를 새로 보완해야 한다.',
'165/167/169/171/173/175 회전 몸체를 확인했다. 얼굴·앞치마·팔/다리의 경계는 보이지만 대기의 세밀한 머릿결과 내부 명암에 비해 단순하다. 각 회전 각도를 보존하고 연속 키로 작업해야 하며 한 머리를 돌려 붙이는 방식은 피한다.',
'177..181 낙봉파 준비와186..189 복귀는 새182..185의 리본·커프·부츠 묘사와 연결 차이가 남는다.182/184 각 공유쌍의 새 원화는 이번 개선 기준에 맞는다. 준비/복귀 팔에 붙은 흰 구는 분리 이펙트가 합성된 상태다.',
]
assert len(notes) == 29
page_records, refs = [], {}
for page in inventory['pages']:
    i = int(Path(page['file']).stem.split('_')[-1])
    record = {'file': page['file'], 'sha256': sha(O/page['file']), 'actually_viewed': True,
              'method': 'view_image로 대기147과 같은 원점·정수배의 전체 페이지를 직접 열람',
              'note': notes[i], 'variant': page['variant'], 'groups': []}
    for g in page['groups']:
        key = g['representative']; b,n = int(key[1]), int(key[3:])
        kind = 'body'
        if n in effects.get(i, []): kind = 'effect_only'
        if key in flash_only: kind = 'body_flash_or_outline'
        if i == 21 and n in head_only: kind = 'head_fragment'
        if g['metadata']['pixels'] == 0: kind = 'blank'
        record['groups'].append({'representative':key,'aliases':g['aliases'],'visual_kind':kind})
        for alias in g['aliases']:
            row = refs.setdefault(alias, {'visual_kind':kind,'representative':key,'viewed_pages':[],
                                          'new_art_prepared':alias in new})
            assert row['visual_kind'] == kind
            row['viewed_pages'].append(page['file'])
    page_records.append(record)
assert len(refs)==436 and all(len(v['viewed_pages'])==2 for v in refs.values())
counts = dict(collections.Counter(v['visual_kind'] for v in refs.values()))
priorities = [
 {'order':1,'keys':['b0_109','b0_111','b0_113','b0_115','b0_121'],
  'scope':'3타109..127 홀수 몸체 전체. 다음 단계에서 실제 동일 몸체/손 차이를 독립 비교하여 필요한 키 수를 확정한다.',
  'reason':'대기 대비 얼굴과 커프의 묘사가 약하고, 상완·허리·부츠가 단순한 면으로 남는다. 사용 빈도와 시각 차이를 함께 고려한 다음 제작 묶음.'},
 {'order':2,'keys':['b0_178','b0_182','b0_190','b0_195','b1_148'],
  'scope':'후면 사다리/공중/상승의 실제 공유 원형 조사 후 확장.',
  'reason':'새174의 머릿결과 큰 흰 머리 면의 차이가 강하다. 후면 옷과 치마 접힘도 별도 시점 원화로 보완한다.'},
 {'order':3,'keys':['b1_001','b1_003','b1_006','b1_007'],
  'scope':'승리1..7 및 귀환 섬광8 동기화.',
  'reason':'새5와 기존 이웃 프레임의 목·팔·다리 체형과 옷 명암이 다르다.'},
 {'order':4,'keys':['b0_034','b0_036','b0_038','b0_041','b0_045'],
  'scope':'기본 이동/벽/착지의 남은 구형 연결 키.',
  'reason':'새 공중/대시 원화 사이에 평면 얼굴과 단순한 소매가 남는다.'},
 {'order':5,'keys':['b0_135','b0_139','b0_149','b0_152'],
  'scope':'피격·저체력 및 연관 섬광 몸체.',
  'reason':'표정뿐 아니라 목·팔·허리와 부츠 구조가 대기와 다르다. 의도된 효과와 새 몸체를 분리하여 동기화한다.'},
 {'order':6,'keys':['b0_229','b1_054','b1_133','b1_150'],
  'scope':'올려 든 팔/벽/상승 특수기의 가는 체형.',
  'reason':'상완과 허리의 폭이 선처럼 좁고 머리 안쪽 명암이 적다. 원 손·도구·벽 접점 보존이 전제다.'},
 {'order':7,'keys':['b1_017','b1_031','b1_066','b1_077'],
  'scope':'차량 탑승 전신 및 라이드아머 머리 조각.',
  'reason':'옆면 얼굴·머릿결과 소매/앞치마 접힘이 단순하다. 실제 차량 가림까지 따로 실기 확인해야 한다.'},
 {'order':8,'keys':['b1_161','b1_163','b1_167','b1_173'],
  'scope':'회전베기 전 각도.',
  'reason':'대기 대비 세부 부족은 있지만 회전에 따른 축소/접힘을 그대로 유지해야 한다. 각도별 연속 원화가 필요하다.'},
 {'order':9,'keys':['b1_177','b1_179','b1_186','b1_189','b0_249','b0_251'],
  'scope':'낙봉파 준비/복귀와 등장.',
  'reason':'새182..185 몸체 및 세밀한 대기로 연결되는 프레임들의 의상·얼굴 묘사를 맞춘다.'},
]
result = {
 'scope':'린 최신 작업 ARC의 전수 정적 미술 검토. 미술 완성 또는 전수 실기 판정이 아니다.',
 'source':inventory['source'], 'source_sha256':inventory['source_sha256'],
 'review_date':'2026-11-07','reviewer':'hud_checkpoint',
 'raw_reference_count':444,'standalone_references_actually_covered':436,
 'exact_translated_shape_groups':319,'normal_pages_actually_viewed':29,'black_pages_actually_viewed':29,
 'dedup_rule':'잘린 인덱스 픽셀과 크기가 정확히 같은 형태만 묶음. 평행이동만 허용하며 반전·회전·유사 형태는 묶지 않음.',
 'display_rule':'페이지 안 모든 셀은 동일 월드 crop·원점160·최근접4배. 페이지별 crop은 모든 효과와 몸체를 포함한다.',
 'palette_scope':'몸체 팔레트0/13은 현재 ARC. 나머지 세 CLUT는 이전 실제 캡처의 미리보기 값이므로 현재 실기 효과색 검증이 아니다.',
 'visual_kind_counts':counts,'references':refs,'pages':page_records,'next_art_groups':priorities,
 'limitations':[
  'b1_42..49의 8참조는 한 타일 부분 VRAM 갱신이다. 직전 VRAM 문맥 없이 완성 몸체를 독립 복원할 수 없어 전수 그림 판단에서 제외했다.',
  '정적 전수 열람은 실제 타이밍·원근에 따른 연속 움직임·반전 GPU 경계·차량/벽/효과 가림 검사를 대신하지 않는다.',
  '319개 중복 형태를 봤다는 뜻이지 319개 새 원화가 필요하다는 뜻은 아니다. 공유 손·머리·의상을 조사한 뒤 키 수를 줄인다.',
  '신규52참조의 기술 검사와 root 미술 검토가 있지만 사용자 수용이나 실제 게임 전수 완료로 기록하지 않는다.',
  '이 자료는 PL01 본체/효과 참조의 범위다. 별도 선택/저장 UI ARC 전체와 다른 캐릭터까지 전수 완료했다는 주장은 하지 않는다.',
 ],
 'root_rin185_art_review':{'accepted_for_working_candidate':True,'source':'부모 메시지: old/new/idle 및 effect_comparison 직접 열람 후 수용','user_accepted':False,'runtime_verified':False,'frozen_files_modified':False},
 'new_art_prepared_refs_count':len(new), 'full_art_unification_complete':False,
 'full_runtime_verified':False,'user_accepted':False,'game_or_original_files_changed':False,
}
(O/'visual_review.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n','utf8')
inventory['crop_rule'] = result['display_rule']
inventory['palette_scope'] = result['palette_scope']
inventory['all_visually_reviewed'] = True
inventory['visual_review_record'] = 'visual_review.json'
for page in inventory['pages']:
    page['viewed'] = True
(O/'inventory.json').write_text(json.dumps(inventory,ensure_ascii=False,indent=2)+'\n','utf8')
lines=['# 린 52참조 작업본 전수 미술 재검토','',
 '일반/블랙 각각29장, 총58장을 실제 열람했다. 444참조 중 독립 복원 가능한436개를319개 정확한 중복 형태로 묶어 대기147과 같은 원점에서 비교했다. **전체 미술 통일은 아직 완료되지 않았다.**','',
 f"작업 ARC SHA-256: `{result['source_sha256']}`. 현재 게임 BIN을 수정한 결과가 아니라 동결된 Rin52 작업본 검토다.",'',
 '대기와 새 원화의 머릿결·볼/턱·커프·치마 주름에 비해 남은 지상 공격, 후면, 승리/귀환, 탑승, 피격과 일부 공중 특수기는 여전히 큰 단색 면으로 읽힌다. 특히 가늘어진 목·상완·허리·부츠를 자세 차이만으로 모두 보류하지 않고 재작화 대상으로 기록했다.','',
 '## 다음 제작 순서','',
 '| 순서 | 대표 키 | 범위와 근거 |','|---|---|---|']
for p in priorities: lines.append(f"| {p['order']} | {', '.join(p['keys'])} | {p['scope']} {p['reason']} |")
lines += ['', '## 실제 열람 장부','', '각 페이지의 정확한 동형 참조와 파일 해시는 [visual_review.json](visual_review.json)에 있다. 아래 일반/블랙 링크 모두 실제 열람했으며 색만 보고 일반색 미열람분을 대신 처리한 것이 아니다.','', '| 페이지 | 일반 | 블랙 | 관찰 |','|---|---|---|---|']
for i,note in enumerate(notes): lines.append(f'| {i:02} | [일반](normal_{i:02}.png) | [블랙](black_{i:02}.png) | {note} |')
lines += ['', '## 검토 한계','']+[f'- {s}' for s in result['limitations']]+['', 'Rin185에 대한 root의 후속 미술 검토 수용은 이 기록에만 추가했다. 이미 동결한 ARC·proposal·recipe·FROZEN 파일은 변경하지 않았다.','']
(O/'REPORT.md').write_text('\n'.join(lines),'utf8')
print(json.dumps({'count':counts,'sheets':58,'review_sha256':sha(O/'visual_review.json')},ensure_ascii=False))
