from pathlib import Path
import json,hashlib,html
D=Path(__file__).parent;ROOT=D.parents[2];O=D/'nana_selection4_independent01'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();r=json.loads((O/'report.json').read_text('utf8'))
notes={18:'새207의 모자·머릿결·가슴과 다리 상세가 UI에 그대로 옮겨졌다. 원게임과 UI 변환 열의 Y−1 차이를 구분했다.',19:'새156의 접힌 팔·다리와 뒤 베일이 선택창 반대방향으로 이어진다. 원게임 거울반전 열과 UI의 위치가 일치하며 아래로1px 추가 이동하지 않았다.',20:'새157의 얼굴·머리와 오라가 반전된 선택 사본에도 유지된다. 오라가 새머리에 맞고 옛 큰머리 윤곽 잔재는 보이지 않았다.',21:'원전송빛 안의 새158 몸과 다리가 새UI에 동일 방향으로 보인다. 별도 반전이나 위치변경 없이 원래 빛무늬가 유지된다.'}
seen=[]
for q in r['readback_sheets']:
 p=ROOT/q['path'];assert sha(p)==q['sha256'];n=int(p.stem.split('_')[-1]);seen.append({**q,'actually_viewed':True,'finding':notes[n]})
for p,h in r['inputs'].items():assert sha(ROOT/p)==h,p
v={'candidate_sha256':r['candidate_sha256'],'technical_report_sha256':sha(O/'report.json'),'sheets':seen,'new_confirmed_art_defect_found':False,'scope':'독립 선택사본4 재추출과 실제게임 몸체의 정적 비교. 실제 선택창 부팅/전환 미실행.','limits':['다른 선택창 모션 전체를 최신 원화와 다시 비교한 작업은 아니다.','사용자 최종수용과 전체캐릭터 완료를 주장하지 않는다.']}
(O/'visual_review.json').write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n','utf8')
page=['<!doctype html><meta charset="utf-8"><title>RN 나나 선택사본4 독립 읽기</title><style>body{font:16px sans-serif;background:#182333;color:#eee;margin:24px}img{max-width:100%}a{color:#9cddff}</style><h1>RN 나나 선택사본4 독립 읽기</h1><p>a5775669: 원래 RN 거울반전은 Y불변이며 BR Y+1과 구분됩니다. 4사본 원점/RGBA,76비대상,134보호타일을 대조했습니다. 실제 선택창 실기는 별도입니다.</p><p><a href="report.json">기술 보고</a> · <a href="visual_review.json">실제 열람4판 기록</a></p>']
for q in seen:page.append(f'<p>{html.escape(q["finding"])}</p><img src="{Path(q["path"]).name}">')
(O/'INDEX.html').write_text('\n'.join(page),'utf8')
print(json.dumps({'technical':sha(O/'report.json'),'visual':sha(O/'visual_review.json'),'pages':len(seen)}))
