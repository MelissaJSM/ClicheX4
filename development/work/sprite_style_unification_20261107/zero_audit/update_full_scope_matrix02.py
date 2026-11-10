"""Append a read-only scope snapshot; preserve the linked matrix01 evidence."""
from pathlib import Path
import collections,copy,hashlib,html,json,os,re

ROOT=Path(__file__).resolve().parents[3]
B=ROOT/'work/sprite_style_unification_20261107';D=Path(__file__).parent
PREV=D/'full_scope_matrix01/coverage.json';OUT=D/'full_scope_matrix02';OUT.mkdir(exist_ok=True)
read=lambda p:json.loads(p.read_text('utf8'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
j=read(PREV);j['previous_snapshot']={'path':PREV.relative_to(ROOT).as_posix(),'sha256':sha(PREV)}
for e in j['evidence'].values():assert sha(ROOT/e['path'])==e['sha256'],e['path']
def ev(key,p,purpose):
 p=ROOT/p if isinstance(p,str)else p
 assert p.is_file(),p
 j['evidence'][key]={'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p),'purpose':purpose}
ev('shibuki_ledger',B/'shibuki_audit/fullform_ledger16.json','최신 네 폼 참조 분류. 원화·통합·실기는 별도 구분')
ev('nana_ledger',B/'nana_audit/scope_summary_v9/manifest.json','최신 네 폼 분류. Ultimate 라이징7 동결 포함')
for key,path,purpose in [
 ('br15','staging_br_v15.json','381d83 이동32 통합 시험 계획. 실기 완료 증거 아님'),
 ('rn17','staging_rn_v17.json','413273 Ultimate 라이징7 통합 시험 계획'),
 ('shibuki_run_frozen','shibuki_audit/prepared_base_run01/FROZEN.json','이동32 최종 동결·root75 미술·독립reader·실제로더MIPS 결속'),
 ('shibuki_run_reader','zero_audit/shibuki_run32_independent01/report.json','508raw/160목표층/비대상476raw·980층/은행후미 보존'),
 ('shibuki_run_loader','zero_audit/shibuki_run32_directory_native01/report.json','실제로더→scratchpad→directory→객체→decode/upload 508×2'),
 ('shibuki_ladder_source','shibuki_audit/ultimate_ladder_native03/report.json','143/144/146 전후6표시 초기 등록. 접점·공통층·패킹 전'),
 ('nana_hurt_source','nana_audit/hurt_repaint/first_registered_v1/registration.json','기본/포스106/110 새 원화 초기 등록. 표정·접점·파생 미완료'),
 ('nana_hurt_relations','zero_audit/nana_hurt_relations01/report.json','기존 몸체·CLUT2 실루엣·수용 오라 독립 읽기'),
 ('nana_ultimate_rising_frozen','nana_audit/rising_repaint/packed_ultimate_candidate_v1/FROZEN.json','413273 최종 동결, RN17 통합'),
 ('nana_ultimate_rising_reader','zero_audit/nana_ultimate_rising7_independent01/report.json','독립35층/비대상/권총·효과 대조 및3판 실제 열람'),
 ('nana_ultimate_rising_runtime','runtime/nana_ultimate_rising17_summary.json','획득 후 폼 실기351창/새7전부/27고유참조. root12판 열람, 미확정0')]:
 ev(key,B/path,purpose)
# Korean explanations are explicit source text, not shell-encoded strings.
purposes={
 'shibuki_ledger':'최신 네 폼 참조 분류. 새 원화·통합·실기는 별도 구분',
 'nana_ledger':'최신 네 폼 분류. Ultimate 라이징7 동결 포함',
 'br15':'381d83 이동32 통합 시험 계획. 실기 완료 근거 아님',
 'rn17':'413273 Ultimate 라이징7 통합 시험 계획',
 'shibuki_run_frozen':'이동32 최종 동결, root75 미술·독립 reader·실제로더 MIPS 결속',
 'shibuki_run_reader':'508raw·160목표층·비대상476raw/980층·은행후미 보존',
 'shibuki_run_loader':'실제로더→scratchpad→directory→객체→decode/upload 508×2',
 'shibuki_ladder_source':'143/144/146 전후6표시 초기 등록. 접점·공통층·패킹 전',
 'nana_hurt_source':'기본/포스106/110 새 원화 초기 등록. 표정·접점·파생 미완료',
 'nana_hurt_relations':'기존 몸체·CLUT2 실루엣·수용 오라 독립 읽기',
 'nana_ultimate_rising_frozen':'413273 최종 동결, RN17 통합',
 'nana_ultimate_rising_reader':'독립35층·비대상·권총/효과 대조와3판 실제 열람',
 'nana_ultimate_rising_runtime':'획득 후 폼 실기351창/새7전부/27고유참조. root12판 열람, 미확정0'}
for key,purpose in purposes.items():j['evidence'][key]['purpose']=purpose
for key,mode,version in [('br15','ver_buki_riko',15),('rn17','ver_rin_nana',17)]:
 ev(key+'_disc',ROOT/f'out/{mode}/sprite_style_unification_20261107_v{version}/manifest.json','통합 디스크 생성·재추출·보존 기록. 이 집계에서 디스크 검사를 반복하지 않음')
j['integration']={}
for key in ('br15','rn17'):
 plan=read(ROOT/j['evidence'][key]['path']);disc=read(ROOT/j['evidence'][key+'_disc']['path'])
 j['integration'][key]={'output':plan['output'],'resources':plan['resources'],'bin_sha256':disc['modified_bin']['sha256']}
def parse(s):
 out=[]
 for token in s.split(', '):
  if '..'in token:
   a,b=map(int,token.split('..'));out.extend(range(a,b+1))
  elif token:out.append(int(token))
 return out
def compact(ns):
 ns=sorted(set(ns));chunks=[]
 if not ns:return ''
 start=last=ns[0]
 for n in ns[1:]+[ns[-1]+2]:
  if n!=last+1:chunks.append(str(start)if start==last else f'{start}..{last}');start=n
  last=n
 return ', '.join(chunks)
def override(c,refs,status,label):
 refs=set(refs);before=set()
 for state in c['states']:
  old=set(parse(state['refs']));before|=old;state['refs']=compact(old-refs)
 assert refs<=before,(c['character'],c['form'],c['category'],refs-before)
 c['states']=[s for s in c['states']if s['refs']]
 same=next((s for s in c['states']if s['status']==status),None)
 if same:same['refs']=compact(parse(same['refs'])+list(refs))
 else:c['states'].append({'status':status,'label':label,'refs':compact(refs)})
for c in j['cells']:
 char,form,cat=c['character'],c['form'],c['category']
 c['evidence']=[('br15'if k=='br14'else'rn17'if k in('rn15','rn16')else k)for k in c['evidence']]
 if char=='shibuki'and cat=='run':
  c['note']='기본/포스1..32는381d83 동결 및 BR15 통합.1은 수용 대기0 재사용이며64장 신규 생성 뜻 아님. Ultimate3..32는 기존 새 원화 통합,1/2 수용 세부 보존. BR15 새 이동 실기는 별도 진행 중.'
  if form in('base','fourth'):
   override(c,range(1,33),'integrated_new_art','새 원화 동결·현재 통합')
   c['evidence']+=['shibuki_run_frozen','shibuki_run_reader','shibuki_run_loader','br15_disc']
   c['art_review']='최종 제작자/root 재추출12판 및 독립8판 실제 열람. 기술검사와 새 부팅 실기를 분리하며 이번 표에서 미술 재검사는 반복하지 않음.'
 if char=='shibuki'and cat=='ladder'and form.startswith('ultimate'):
  override(c,[143,144,146],'source_only','새 원화·초기 등록, 접점/패킹 검증 전')
  c['note']='143/144/146 두 의상 첫6표시 원화와 뒤통수 안경 국소 편집 등록. 접점·공통층·패킹 전이며 다른 사다리/사격 참조는 별도 잔여.'
  c['evidence'].append('shibuki_ladder_source')
 if char=='nana'and cat=='special':
  override(c,[100,101,102,103,104,231,232],'integrated_new_art','새 원화 동결·현재 통합')
  c['note']='라이징7은 기본/포스3bd 및 Ultimate413273 동결·RN17 통합. 기본/포스 RN16 대표실기와 Ultimate 획득후 RN17 새7전부 실기가 있음. 재킷·모든부분조합·60Hz 전수는 별도.95..99·정지사격·213..230 분류/미술 잔여 유지;217/218/220은 머리만 복원.'
  c['evidence']=[k for k in c['evidence']if k not in('nana_ultimate_rising_source','nana_ultimate_rising_registered')]
  c['evidence']+=['nana_ultimate_rising_frozen','nana_ultimate_rising_reader','nana_ultimate_rising_runtime','rn17_disc']
 if char=='nana'and cat=='hurt'and form in('base','fourth'):
  override(c,[106,110],'source_only','새 원화·초기 등록, 접점/패킹 검증 전')
  c['note']='106/110 양의상 첫4몸체 초기등록. 원 감긴눈→새 열린눈 표정, 손발 접점과 부분층은 검토 중.107/108/111 공유몸·원효과와109/112..114 실루엣 파생이 필요.233/234 및235/236의 나나용 오라·저체력은 후속.'
  c['evidence']+=['nana_hurt_source','nana_hurt_relations']
 if char=='shibuki'and cat=='ui':c['note']='선택18..21 새몸 및23 빛기둥 사본을 보존. 저장은 수용 대기 사본. BR15 이동32는0대기/선택참조와별개이며 기존ST0E자원 그대로 통합.'
 if cat=='hq':c['note']+=' 현재 통합의 별도 UI 자원은 이전 근거와 동일하며 새 전수 열람을 주장하지 않는다.'
 c['evidence']=list(dict.fromkeys(c['evidence']))
j['next_work']=[
 {'owner':'root','character':'shibuki','scope':'BR15 기본/포스 이동32','stage':'동결·통합 완료, 새 부팅 실기 진행 중. 완료보고 전','evidence':['shibuki_run_frozen','br15_disc']},
 {'owner':'overhaul_ui','character':'shibuki','scope':'Ultimate 사다리143..155/183','stage':'143/144/146 첫6표시 초기등록; 사격/나머지/공통층/패킹 잔여','evidence':['shibuki_ladder_source','shibuki_ledger']},
 {'owner':'overhaul_audio','character':'nana','scope':'기본/포스 피격106..114/233..236 및 저체력','stage':'106/110 첫4몸체 초기등록, 공유몸·CLUT2·수용오라 의존규칙 조사완료. 그 외 미제작','evidence':['nana_hurt_source','nana_hurt_relations','nana_ledger']},
 {'owner':'overhaul_ui','character':'shibuki','scope':'네 폼 피격, Ultimate 등장·승리·귀환','stage':'기존 세부와 대기 대비 후속 재작화·별도 효과 의존 확인','evidence':['shibuki_ledger']},
 {'owner':'overhaul_audio','character':'nana','scope':'사다리·등장·승리·귀환 및 특수95..99/85..92','stage':'재작화 필요와 기존 양호/추가판단을 참조별 구분. 라이징 완료로 이 범위를 덮지 않음','evidence':['nana_ledger','nana_arrival']},
 {'owner':'overhaul_ui + overhaul_audio','character':'shibuki,nana','scope':'체이서162..174, 호버213..230, 208..212','stage':'몸체/효과·능력 사용 경로 구분 및 세부후보 유지. 라이드아머184..203은작은머리/빈198별도','evidence':['shibuki_ledger','nana_ledger']},
 {'owner':'root','character':'riko,rin','scope':'기존 전체미술·대표실기 근거 유지','stage':'현재 추가확정 미술후보 없음. 전모션/전팔레트 실기완료 뜻아님. 새로운 우려 없이 통과검사 반복하지 않음','evidence':['riko_views','rin_views','rin_normal_runtime','rin_red_runtime']},
 {'owner':'root','character':'all','scope':'HQ·대사·잔기·선택/저장 별도 사본','stage':'용도별 디자인 보존,Zero8판+X8판기존루트열람계승. 메인4510표시에임의합산하지않음','evidence':['zero_endpoint_views','x_endpoint_views']}]
j['coverage_limits']=[x for x in j['coverage_limits']if not x.startswith(('Shibuki ledger14','Nana v5'))]+[
 '새 Shibuki 이동32는 고정길이entry2 내부 재배치672B와 캡슐은행10/11 미소비꼬리재사용을 독립검사했다. 로더검사가 실제새부팅/전상태 게임검증을 대신하지 않는다.',
 '원래 플레이어144표 초기화에 없는105/161/190은 별도참조시험이다. 특히161/190을 미사용·예약으로 확대해석하지 않는다.',
 'Nana Ultimate RN17 실기는 획득 후 폼만. 새7전부관측을 재킷/부분전조합 실기로 확대하지 않는다.',
 '신규 첫원화/국소정합은 제작중후보이며 숫자상변경표시를 품질완료율로 쓰지 않는다.']
j['snapshot_summary']='BR15/RN17 통합 기준. Zero 재검사 없이 기존근거 계승, 새Shibuki 이동동결·Nana Ultimate라이징 실기·초기피격/사다리후보 갱신.'
assert len(j['cells'])==144
for c in j['cells']:
 for key in c['evidence']:assert key in j['evidence'],key
for e in j['evidence'].values():assert (ROOT/e['path']).is_file()
(OUT/'coverage.json').write_text(json.dumps(j,ensure_ascii=False,indent=2)+'\n','utf8')
def link(key):
 e=j['evidence'][key];href=os.path.relpath(ROOT/e['path'],OUT).replace('\\','/')
 return '<a href="'+html.escape(href)+'">'+html.escape(key)+'</a>'
H=html.escape
page=['<!doctype html><meta charset="utf-8"><title>전체 폼·모션 범위 BR15 RN17</title><style>body{background:#111820;color:#e9edf2;font:15px system-ui;margin:24px}a{color:#9dcfff}table{border-collapse:collapse;width:100%;margin:18px 0 35px}th,td{border:1px solid #405164;padding:10px;text-align:left;vertical-align:top}th{background:#233547;position:sticky;top:0}summary{cursor:pointer}small{color:#b7c5d4}.notice{padding:16px;background:#263547}</style>',
 '<h1>네 캐릭터 · 폼별 모션 범위</h1><p>BR15 / RN17 · 12폼 × 12범주. <b>수정 수는 미술 완료율이 아닙니다.</b></p>',
 '<p class="notice">시부키 이동32 동결·BR15 통합, 실기는 진행 중. 나나 Ultimate 라이징7은 RN17 획득 후 폼 대표 실기 완료. 새 사다리·피격은 초기 제작 중이며 나머지 미술 작업도 계속합니다.</p>',
 '<p><a href="coverage.json">전체 JSON</a> · <a href="../full_scope_matrix01/COVERAGE.html">이전 스냅샷</a> · <a href="../final_endpoint_audit01/ZERO_UI_HQ_SUPPLEMENT.html">Zero UI/HQ 보충판</a> · <a href="../x_endpoint_supplement01/X_UI_HQ_SUPPLEMENT.html">X UI/HQ 보충판</a></p><h2>다음 작업</h2><table><tr><th>담당</th><th>범위</th><th>상태</th></tr>']
for p in j['next_work']:page.append('<tr>'+''.join('<td>'+H(p[k])+'</td>'for k in('owner','scope','stage'))+'</tr>')
page.append('</table>')
names={'shibuki':'시부키','nana':'나나','riko':'리코','rin':'린'}
for char in names:
 for form in j['forms']:
  cells=[c for c in j['cells']if c['character']==char and c['form']==form]
  if not cells:continue
  page.append(f'<h2>{names[char]} · {j["forms"][form]}</h2><table><tr><th>범주</th><th>상태·참조</th><th>판단·남은 범위</th><th>실제 열람·근거</th></tr>')
  for c in cells:
   states='<br>'.join(H(s['label']+': '+s['refs'])for s in c['states'])or'별도 사본 범위'
   page.append('<tr><td>'+H(j['categories'][c['category']])+'</td><td>'+states+'</td><td>'+H(c['note'])+'</td><td><small>'+H(c['art_review'])+'</small><details><summary>근거</summary>'+'<br>'.join(link(k)for k in c['evidence'])+'</details></td></tr>')
  page.append('</table>')
page.append('<h2>한계</h2><ul>'+''.join('<li>'+H(s)+'</li>'for s in j['coverage_limits'])+'</ul>')
(OUT/'COVERAGE.html').write_text('\n'.join(page),'utf8')
targets=re.findall(r'href="([^"]+)"',(OUT/'COVERAGE.html').read_text('utf8'))
assert all((OUT/html.unescape(p)).resolve().is_file()for p in targets)
verification={'passed':True,'cells':144,'evidence_files':len(j['evidence']),'checked_local_links':len(targets),'broken_links':0,'prior_snapshot_preserved_sha256':sha(PREV),'new_art_or_runtime_test':False,'all_art_complete':False}
(OUT/'verification.json').write_text(json.dumps(verification,ensure_ascii=False,indent=2)+'\n','utf8')
print(json.dumps({'json_sha256':sha(OUT/'coverage.json'),'html_sha256':sha(OUT/'COVERAGE.html'),**verification}))
