from pathlib import Path
import json,hashlib,html
D=Path(__file__).parent;ROOT=D.parents[2];O=D/'nana_base_return3_independent01'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
r=json.loads((O/'report.json').read_text('utf8'))
notes={
 'full_156.png':'새 모자/머릿결·소매·치맛단 명암이 늘었고 두 의상에 접힌 다리와 발끝이 이어진다. 기존과 같은 전체 원점에서 눈과 바닥을 비교했으며 새 확정 신체 절단은 찾지 못했다.',
 'full_157.png':'새156의 머리/몸체 외곽을 따르는 흰 안쪽·분홍 바깥 오라가 이어진다. 옛 오라 윤곽을 새 머리에 억지로 복사한 모습은 보이지 않는다.',
 'full_158.png':'원래 전송광과 새몸의 상승 위치를 함께 확인했다. 몸 바깥 빛무늬가 유지되고 새 머리/다리 표현이 에너지색으로 이어진다.',
 'partial_156.png':'머리/몸/팔/다리 및 몸+다리 5부분을 직접 보았다. body-only의 뒤 베일 조각이 따로 떠 보이지 않으며 다리 선택 시 뒤 베일과 포스 다리가 함께 이어진다.',
 'partial_157.png':'같은5부분에서 오라·모자·소매와 뒤 베일이 이어진다. 추가로 확정할 떨어진 조각은 찾지 못했다.',
 'partial_158.png':'5부분의 전송광을 확인했다. 빛의 여러 작은 성분은 원효과이며 전체 그림을 단일 연결성분으로 강제하지 않는다.'}
seen=[]
for q in r['readback_sheets']:
 p=ROOT/q['path'];assert sha(p)==q['sha256'];seen.append({**q,'actually_viewed':True,'finding':notes[p.name]})
assert len(seen)==6
for p,h in r['inputs'].items():assert sha(ROOT/p)==h,p
v={'candidate_sha256':r['candidate_sha256'],'technical_report_sha256':sha(O/'report.json'),'sheets':seen,'new_confirmed_art_defect_found':False,'scope':'독립 재추출6판 정적 미술검토. 실제 게임/새 MIPS/원순서 전수 실기 아님.','limits':['부츠와 맨다리의 차이는 수용된 의상 표현으로 구분했다. 몸/알파가 전부 같아야 한다는 기준은 적용하지 않았다.','96부분RGBA는 기술검사로 대조했고 실제 육안은 기록한 5부분×3 및 완성3판이다.','최종 사용자 수용 및 전체 작업 완료를 주장하지 않는다.']}
(O/'visual_review.json').write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n','utf8')
page=['<!doctype html><meta charset="utf-8"><title>나나 기본/포스 귀환3 독립 읽기</title><style>body{font:16px sans-serif;background:#182333;color:#eee;margin:24px}img{max-width:100%}a{color:#9cddff}</style><h1>나나 기본/포스 귀환3 독립 읽기</h1><p>후보6823c51: 새 원화2셀·Manhattan 오라·원159 빛·부분파츠를 별도 읽기로 검사했습니다. 제작함수/게임을 실행하지 않았습니다.</p><p><a href="report.json">기술 보고</a> · <a href="visual_review.json">실제 열람6판 기록</a></p>']
for q in seen:page.append(f'<p>{html.escape(q["finding"])}</p><img src="{Path(q["path"]).name}">')
(O/'INDEX.html').write_text('\n'.join(page),'utf8')
print(json.dumps({'technical':sha(O/'report.json'),'visual':sha(O/'visual_review.json'),'pages':6}))
