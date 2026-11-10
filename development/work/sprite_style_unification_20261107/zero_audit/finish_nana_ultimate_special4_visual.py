from pathlib import Path
import json,hashlib,html
D=Path(__file__).parent;ROOT=D.parents[2];O=D/'nana_ultimate_special4_independent01'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
r=json.loads((O/'report.json').read_text('utf8'))
notes={95:'새 머리·재킷·다리 명암이 대기의 상세 방향과 이어진다. 아래로 든 사선 권총과 손이 이어지고 맨팔의 어깨/허리에서 밝은 소매 잔재로 확정할 부분은 찾지 못했다.',96:'95의 새 양폼이 오른쪽으로 이동한 형태를 확인했다. 옛 후폼96의 별도 무릎 변형을 그대로 복원한 그림이라는 뜻은 아니다. 추가 확정 단절은 보이지 않았다.',98:'가로로 든 정본 권총과 새 손·전완이 이어진다. 맨팔은 어두운 아래 경계와 피부 명암이 남고 커다란 U형 검정 덩어리나 공중에 뜬 총으로 읽히지 않았다. 벌린 다리의 무릎/발목 연결도 확인했다.',99:'98에서 이동한 새 양폼과 손·총 연결이 유지된다. 어깨/손목의 새 절단이나 양폼의 갑작스러운 별도 크기 변화는 찾지 못했다.'}
seen=[]
for q in r['readback_sheets']:
 p=ROOT/q['path'];assert sha(p)==q['sha256'];n=int(p.stem.split('_')[-1]);seen.append({**q,'actually_viewed':True,'finding':notes[n]})
assert len(seen)==4
for p,h in r['inputs'].items():assert sha(ROOT/p)==h,p
v={'candidate_sha256':r['candidate_sha256'],'technical_report_sha256':sha(O/'report.json'),'sheets':seen,'new_confirmed_art_defect_found':False,'scope':'최종 ARC 독립 재추출4판의 두 의상과 대기 비교. 실제 게임/발사효과 접점의 실기 증명은 아니다.','limits':['95/96/98/99의 단일 정적 비교를 보았으며 원표 전체 연속 동작을 육안 전수 재검사하지 않았다.','제작자의 원화12셀 재양자화와 원MIPS를 새로 실행한 것으로 세지 않는다.','전체 작업 완료 또는 사용자 최종 수용을 주장하지 않는다.']}
(O/'visual_review.json').write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n','utf8')
page=['<!doctype html><meta charset="utf-8"><title>나나 Ultimate 특수4 독립 읽기</title><style>body{font:16px sans-serif;background:#182333;color:#eee;margin:24px}img{max-width:100%}a{color:#9cddff}</style><h1>나나 Ultimate 특수4 독립 읽기</h1><p>56a3aeb4: 고정등록 이후 의상53셀·공통손1셀·98정본과 피부 가림·새파생을 재구성하고 20층/128부분 및 비대상을 독립 읽기로 확인했습니다. 실제 게임은 미실행입니다.</p><p><a href="report.json">기술 보고</a> · <a href="visual_review.json">실제 열람4판 기록</a></p>']
for q in seen:page.append(f'<p>{html.escape(q["finding"])}</p><img src="{Path(q["path"]).name}">')
(O/'INDEX.html').write_text('\n'.join(page),'utf8')
print(json.dumps({'technical':sha(O/'report.json'),'visual':sha(O/'visual_review.json'),'pages':len(seen)}))
