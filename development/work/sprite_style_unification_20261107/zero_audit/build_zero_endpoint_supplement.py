"""Make an independent offline UI/HQ supplement; never edit the main album."""
from pathlib import Path
import base64,hashlib,html,json
ROOT=Path(__file__).resolve().parents[3]
D=Path(__file__).parent
O=D/'final_endpoint_audit01'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
p=O/'report.json';r=json.loads(p.read_text('utf8'))
views=[]
for v in r['projects'].values():
    v['preview_actually_viewed_this_audit']=True
    v['preview_viewer']='hud_checkpoint'
    v['preview_art_findings']={
      'hunter_base':'14참조를 모두 실제 열람했다. 큰 전신의 머리 명암·옷깃·소매·부츠 선이 유지되며, 현재 작은 gameplay 원화의 구형 사본으로 보지 않는다. 이번 판에서 새 확정 절단/큰 단순 색면 결함을 찾지 못했다. 보존 판단.',
      'life_item':'9위상을 실제 열람했다. 16px 원화와 축소/거품 단계로서 현재 조종석 머리와 독립이다. 리코 흰/청록 대비와 린 얼굴 단순화는 기존 아이콘 표현이며 이번 몸체 동기화 누락이 아니다. 고해상도 전신 기준으로 자동 재제작하지 않는다. 실제 pickup색/동작의 신규 실기는 미검증.',
      'dialogue_pause':'대사3표정과 메뉴 얼굴을 실제 열람했다. 머리/얼굴/옷깃 상세가 있는 별도 큰 원화다. 입 모양 차이가 유지되고 새 확정 결함은 찾지 못했다. 모든 stage 사본의 실제 사용과 제목/무기획득 그림까지 검토한 것은 아니다.',
      'selection_save':'현재 선택32/저장43 및 색상 사본이 실제 PL01과 일치하여 추가 동기화 필요가 없다.'}
    for f in v['preview_sheets']:
        views.append({'path':f,'sha256':sha(ROOT/f),'actually_viewed':True})
r['actual_visual_review_sheets']=views
r['supplement_scope']='별도 UI·헌터베이스 보충판 8장. 기존 4,510표시 집계와 별도이며 전체 캐릭터/모든 이벤트 완료 선언이 아니다.'
r['recommendation']='현재 비교에서 추가 확정 게임플레이 사본 누락 없음. 별도 HQ/아이템/초상화는 보충판에 보존하며, 실제 사용 장면과 제목·무기획득/반복stage 사본 전수는 미검증 범위로 명시한다.'
p.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n','utf8')
esc=html.escape
sections=[]
titles={'endpoints.png':'대기·저장·별도 HQ·잔기·조종석·메뉴 비교','hq_all14.png':'헌터베이스 전신 14참조','life_all9.png':'잔기 아이템 머리 9위상','dialogue_all3.png':'대사 얼굴 3표정'}
for v in r['projects'].values():
    name='리코' if v['character']=='riko' else '린'
    figures=[]
    for f in v['preview_sheets']:
        q=ROOT/f;data=base64.b64encode(q.read_bytes()).decode()
        scale=2 if q.name=='hq_all14.png' else 5 if q.name=='life_all9.png' else 3
        figures.append(f'<figure><figcaption>{esc(titles[q.name])} · 네이티브 {scale}배, 최근접 확대</figcaption><div class="scroll"><img src="data:image/png;base64,{data}" alt="{esc(name+" "+titles[q.name])}"></div><details><summary>PNG·출처</summary><p><a href="{v["character"]}/{q.name}">{esc(f)}</a></p><code>{sha(q)}</code></details></figure>')
    sections.append(f'<section id="{v["character"]}"><h2>{name}</h2><p>실제 시험 BIN에서 읽은 자료입니다. 저장 일반/블랙은 현재 대기147과 같은 그림이며, HQ·잔기·큰 얼굴은 별도 원화입니다.</p><details><summary>BIN 해시와 검사 근거</summary><p>{esc(v["bin"])}</p><code>{v["bin_sha256"]}</code><p>최종 원화 {v["latest_authored_ref_count"]}참조, 선택32, 저장43, 정적 몸체23/24 연결을 대조했습니다.</p></details>{"".join(figures)}</section>')
doc='''<!doctype html><html lang="ko"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>리코·린 — 별도 UI·헌터베이스 그림 보충판</title>
<style>body{margin:0;background:#141d2a;color:#e9eef6;font:16px/1.65 'Malgun Gothic',sans-serif}main{max-width:1500px;margin:auto;padding:24px}h1{font-size:28px}h2{margin-top:48px}a{color:#9bd9ff}nav{position:sticky;top:0;background:#1d2a3deF;padding:12px 24px;z-index:2;display:flex;gap:24px}p{max-width:1050px}.notice{border-left:4px solid #b3cff0;padding:12px 18px;background:#223044}table{border-collapse:collapse;width:100%;font-size:15px}th,td{border:1px solid #455063;padding:12px;text-align:left;vertical-align:top}figure{margin:24px 0;border:1px solid #455063;padding:12px}figcaption{font-weight:bold;margin-bottom:12px}.scroll{overflow:auto;background:#263345}.scroll img{display:block;max-width:none;image-rendering:pixelated}details{margin-top:8px;color:#c4d0e1}code{overflow-wrap:anywhere;font-size:12px}footer{margin:40px 0;color:#c4d0e1}</style>
<nav><a href="#scope">검토 범위</a><a href="#riko">리코 4판</a><a href="#rin">린 4판</a><a href="#evidence">근거</a></nav><main>
<h1>별도 UI·헌터베이스 그림 보충판</h1>
<p class="notice">현재 4,510표시 플레이어 모음집에 포함되지 않은 별도 그림을 보충했습니다. 기존 모음집·게임 파일은 변경하지 않았습니다. 이미지 8판은 이 HTML에 내장되어 파일 하나로 오프라인 열람할 수 있습니다.</p>
<section id="scope"><h2>이번에 확인한 범위</h2><p>BR v14와 RN v15 실제 BIN에서 추출했습니다. 두 캐릭터의 8판을 직접 열람했으며 아래 판단은 정적 미술 검토입니다. HQ/잔기/대사의 새 게임 실행 확인이나 사용자 최종 수용을 뜻하지 않습니다.</p>
<table><thead><tr><th>그림</th><th>현재 판단</th><th>사용·검증 구분</th></tr></thead><tbody>
<tr><td>선택32·저장43</td><td>최신 플레이 몸체와 색인·원점 일치. 저장 일반/블랙 팔레트도 일치. 추가 사본 동기화 불필요.</td><td>선택 실기는 별도 기존 기록. 이번은 실제 BIN 정적 대조이며 저장 장면 신규 실기 아님.</td></tr>
<tr><td>HQ 전신14 × 2명</td><td>큰 원화의 머리 명암·옷깃·소매·부츠 상세가 유지됨. 추가 확정 결함을 찾지 못하여 보존.</td><td>ST0D_0Z bank2. 기존 헌터베이스 제작 경로로 확인. 현재 시험판의 전14 동작 실제 사용은 미검증.</td></tr>
<tr><td>잔기 머리9 × 2명</td><td>별도16px 머리와 축소/거품 위상. 새 조종석 머리 사본이 아니며 자동 교체 대상 아님.</td><td>PL01 static bank3. stage COL row11로 정적 복원. 실제 pickup 혼합색/동작 신규 실기 미검증.</td></tr>
<tr><td>대사3·메뉴 얼굴</td><td>별도 큰 원화의 얼굴·머리·옷깃 상세와 입 모양이 유지됨. 보존.</td><td>대표 stage 대사3과 PL01 메뉴 얼굴. 반복 stage 사본 전수 및 제목·무기획득 배경은 이번 미열람.</td></tr>
</tbody></table><p>부분 VRAM b1_42..49는 선행 업로드에 의존합니다. 독립 완성 이미지나 미사용 참조로 처리하지 않았습니다. 이미지마다 고정 정수 확대율을 사용하며 화면보다 넓은 판은 가로 스크롤로 봅니다.</p></section>'''+''.join(sections)+f'''
<section id="evidence"><h2>근거와 한계</h2><p><a href="report.json">검사·열람 보고서 JSON</a> · <a href="../audit_final_zero_endpoints.py">실제 BIN 추출·사본 대조 코드</a></p><code>report SHA-256 {sha(p)}</code>
<p>두 BIN의 최종 원화 Riko28/Rin9와 선택·저장 사본에서 불일치0을 확인했습니다. 기존 전체 436표시 미술 장부는 최신 PL01 해시와 결속했으며 같은 전수 검사를 반복하지 않았습니다. 게임플레이 전체, 별도 그림 전체, 모든 실기가 완료되었다는 의미가 아닙니다.</p></section><footer>그림은 현재 프로젝트의 로컬 검토용 추출물입니다. 원본·사용자 저장·게임·공유 도구·통합 모음집 변경 없음.</footer></main></html>'''
(O/'ZERO_UI_HQ_SUPPLEMENT.html').write_text(doc,'utf8')
print(json.dumps({'html':str((O/'ZERO_UI_HQ_SUPPLEMENT.html').relative_to(ROOT)),'html_sha256':sha(O/'ZERO_UI_HQ_SUPPLEMENT.html'),'report_sha256':sha(p),'viewed':len(views),'embedded_pngs':doc.count('data:image/png;base64,')}))
