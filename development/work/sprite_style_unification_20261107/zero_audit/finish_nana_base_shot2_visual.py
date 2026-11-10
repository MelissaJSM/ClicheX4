from pathlib import Path
import hashlib,json,html
D=Path(__file__).parent;ROOT=D.parents[2];O=D/'nana_base_shot2_independent01'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
r=json.loads((O/'report.json').read_text('utf8'));assert sha(O/'report.json')=='c9a43669cde78ee2747dd0e467baec410cbb38084226d73dc65dff79f0442a37'
assert sha(ROOT/r['candidate'])==r['candidate_sha256']
notes={
 'full_85.png':'새 머릿결·치마/커프와 부츠 명암이 세분되었다. 정본 총열→새 손→소매가 이어지고 양폼의 머리와 발 배치에서 새 확정 단절은 보이지 않았다.',
 'full_86.png':'반동 자세의 총열과 손목, 기본 부츠·포스 다리가 이어진다. 정본20 중 새 손에 가린1셀을 포함한 접점을 구별하여 보았다.',
 'partial_85.png':'머리/몸/팔/다리/몸+다리 다섯 조합에서 베일·소매·치마 아래의 연결을 확인했다. 몸체만 선택했을 때 새 부유 베일 조각은 보이지 않았다.',
 'partial_86.png':'다섯 조합에서 머리 장식·팔과 신발 연결을 확인했다. 포스 다리 경계에 따로 남는 기본 부츠 조각이나 새 확정 절단은 보이지 않았다.'
}
seen=[]
for q in r['readback_sheets']:
 p=ROOT/q['path'];assert sha(p)==q['sha256'];seen.append({**q,'actually_viewed':True,'finding':notes[p.name]})
assert len(seen)==4
v={'candidate_sha256':r['candidate_sha256'],'technical_report_sha256':sha(O/'report.json'),'sheets':seen,'new_confirmed_art_defect_found':False,'scope':'독립 재추출 완성2판·부분2판 실제 정적 열람','gun_visibility':{'85':{'module_texels':20,'visible':20,'new_skin_occluded':0},'86':{'module_texels':20,'visible':19,'new_skin_occluded':1}},'native_evidence':r['native_existing_evidence'],'limits':['생성4셀 직접 재양자화와 실제10층/64부분 검사는 기술 보고에 있고 이 보고는 실제 본4판만 기록한다.','머리156의 기존6조립레코드로 새85/86의 머리2층을 저장한 관계다. 나머지8층까지 머리라는 뜻이 아니다.','정본총·새피부 접점 정적검사이며 실제 탄환 발생점/게임/최종 사용자 수용을 증명하지 않는다.'],'runtime_verified':False,'user_accepted':False,'overall_complete':False}
(O/'visual_review.json').write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n','utf8')
page=['<!doctype html><meta charset="utf-8"><title>나나 기본/포스85·86 독립 검사</title><style>body{font:16px sans-serif;background:#182333;color:#eee;margin:24px}img{max-width:100%}a{color:#9cddff}</style><h1>나나 기본/포스85·86 독립 검사</h1><p>후보d2566605. 생성4셀, 정본총과새손·10층·64부분·비대상 보존을 독립 대조했습니다. 86은20셀 중19가시/새손1가림이며 실기는 별도입니다.</p><p><a href="report.json">기술 보고</a> · <a href="visual_review.json">실제 열람4판</a></p>']
for q in seen:page.append(f'<p>{html.escape(q["finding"])}</p><img src="{Path(q["path"]).name}">')
(O/'INDEX.html').write_text('\n'.join(page),'utf8')
print(json.dumps({'report':sha(O/'report.json'),'visual':sha(O/'visual_review.json'),'viewed':len(seen)}))
