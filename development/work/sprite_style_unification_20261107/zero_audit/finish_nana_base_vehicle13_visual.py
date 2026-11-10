from pathlib import Path
import json,hashlib,html
D=Path(__file__).parent;ROOT=D.parents[2];O=D/'nana_base_vehicle13_independent01'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
r=json.loads((O/'report.json').read_text('utf8'))
native=D/'nana_vehicle_composition_native01/report.json'
assert sha(native)=='4bd59dcb6c8c422690982f7161b5591ae7dae3a26a4a2d47fc05f98d518d925f'
notes={
'full_162.png':'머릿결과 모자·소매·접힌 다리 명암이 기존보다 세분되었다. 손목과 두 무릎에서 새 확정 단절은 보이지 않았다.',
'full_166.png':'새 앞머리·뒤 베일·무릎 아래가 이어지고 기본 부츠와 포스 맨다리의 재질이 구별된다. 기존 손 위치에서 팔이 끊겨 보이지 않았다.',
'full_170.png':'앞으로 내민 손에서 소매가 이어지고 접힌 허벅지와 아래로 뻗은 다리가 연결된다. 머리카락의 밝은 면과 그늘이 구분된다.',
'full_174.png':'새 눈·모자·머릿결이 선명하고 세운 몸의 허리·무릎·발목 연결을 확인했다. 양폼의 접힌 자세와 낮은 발 위치가 유지된다.',
'partial_162.png':'머리/몸/팔/다리/몸+다리 5부분을 실제 보았다. 베일과 치마 아래가 독립적으로 떠 있는 새 조각은 찾지 못했다.',
'partial_166.png':'5부분에서 머리 장식·상의·맨다리의 전환을 확인했다. 낮게 접힌 무릎과 뒤 베일 연결에 추가 확정 단절은 보이지 않았다.',
'partial_170.png':'5부분에서 아래로 뻗은 다리와 신발이 이어진다. body-only와 legs-only에 옛 부츠 조각이 따로 남는 모습은 보이지 않았다.',
'partial_174.png':'5부분에서 얼굴·어깨·허리·무릎의 연결을 보았다. 다리 선택 시 베일 하단이 함께 바뀌며 떠 있는 조각은 찾지 못했다.',
'alias_162.png':'162~165 양폼 8표시의 상하 이동을 같은 원점으로 비교했다. 이동 외에 머리/팔/다리 형태가 변하는 모습은 없었다.',
'alias_166.png':'166~169 양폼 8표시에서 같은 그림의 원래 상하 위상이 유지된다. 시간표 재생이나 실제 차량 접점의 실기 판정은 아니다.',
'alias_170.png':'170~173 양폼 8표시에서 머리·손·무릎이 함께 이동한다. 이 정적 배열에서 부분만 어긋나는 새 변화는 보이지 않았다.'}
seen=[]
for q in r['readback_sheets']:
 p=ROOT/q['path'];assert sha(p)==q['sha256'];seen.append({**q,'actually_viewed':True,'finding':notes[p.name]})
assert len(seen)==11
for p,h in r['inputs'].items():assert sha(ROOT/p)==h,p
# Preserve the originally delivered technical report. Its Korean explanatory
# strings were damaged by a previous shell encoding; numerical results are unchanged.
clarified={**r,'scope':'나나 기본/포스 차량 4키×2폼 원화96셀, 새 얼굴/손 공유, 다리 표본, 원래 Y별칭9와 목표65층을 후보 ARC에서 독립 읽기 대조',
 'metadata_clarification_of':{'path':str((O/'report.json').relative_to(ROOT)),'sha256':sha(O/'report.json'),'reason':'초기 보고의 한국어 설명 문자열 인코딩 손실만 정정. 검사 결과·입력·수치·그림은 불변.'},
 'limits':['독립 전수 범위는 대상416부분RGBA·508raw·1140층이다. 제작자7296RGBA 전수 실행을 대신 주장하지 않는다.',
 'bank6 후미40B에는 27개의 비영 바이트가 있다. 0패딩이라고 부르지 않으며 모든 헤더/레코드의 미소비 범위임을 대조했다.',
 '이 static 보고 이후 수행한 원MIPS 검사는 별도 native 보고에 결합한다. 실제 게임·차량 접점 실기는 미실행이다.',
 '다리 정합의 최대 가로3/세로1은 새 원화 표본 등록 정책이다. 원작 픽셀과 동일하다는 뜻이 아니다.']}
(O/'report_clarified.json').write_text(json.dumps(clarified,ensure_ascii=False,indent=2)+'\n','utf8')
v={'candidate_sha256':r['candidate_sha256'],'technical_report_sha256':sha(O/'report.json'),'clarified_report_sha256':sha(O/'report_clarified.json'),'native_report_path':str(native.relative_to(ROOT)),'native_report_sha256':sha(native),'sheets':seen,'new_confirmed_art_defect_found':False,'scope':'독립 재추출11판 정적 미술검토. 차량 없이 몸체·부분·원래Y별칭을 비교한 판이며 실제 게임 탑승 접점 검증은 아니다.','limits':['기계대조416부분 중 실제 육안은 기록한5부분×4판과 완성4판·별칭3판이다.','원MIPS는 loader와 pointer 초기화·decode/upload 및 부분아머 renderer의 directory/header/record 조회 구간이다. 전체 renderer GPU 명령 작성이나 실제 게임 실행으로 확대하지 않는다.','최종 사용자 수용 및 전체 작업 완료를 주장하지 않는다.']}
(O/'visual_review.json').write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n','utf8')
page=['<!doctype html><meta charset="utf-8"><title>나나 기본/포스 차량13 독립 읽기</title><style>body{font:16px sans-serif;background:#182333;color:#eee;margin:24px}img{max-width:100%}a{color:#9cddff}</style><h1>나나 기본/포스 차량13 독립 읽기</h1><p>후보29f7b9a0. 원화8셀·13표시·416부분과 비대상 보존을 독립 대조하고 원MIPS의 디렉터리 조회를 확인했습니다. 실제 차량 실기는 별도입니다.</p><p><a href="report_clarified.json">기술 보고와 설명 정정</a> · <a href="visual_review.json">실제 열람11판 기록</a> · <a href="../nana_vehicle_composition_native01/report.json">원MIPS 조회/디코드 보고</a></p>']
for q in seen:page.append(f'<p>{html.escape(q["finding"])}</p><img src="{Path(q["path"]).name}">')
(O/'INDEX.html').write_text('\n'.join(page),'utf8')
print(json.dumps({'technical':sha(O/'report.json'),'clarified':sha(O/'report_clarified.json'),'visual':sha(O/'visual_review.json'),'native':sha(native),'pages':11}))
