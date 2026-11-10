"""BR18/RN25 자료 연결 스냅샷. 원화/자원/게임은 변경하거나 다시 검사하지 않는다."""
from pathlib import Path
import copy,hashlib,html,json,os,re
ROOT=Path(__file__).resolve().parents[3];D=Path(__file__).parent;B=D.parent;H=B/'shibuki_audit';N=B/'nana_audit'
P=D/'full_scope_matrix06/coverage.json';O=D/'full_scope_matrix07'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();read=lambda p:json.loads(p.read_text('utf8'))
assert sha(P)=='5ac6923d60ae2165b9475856559007507ff5045fec26cce052f4f708678585bd'
j=read(P);old_ev=copy.deepcopy(j['evidence']);old_zero=copy.deepcopy([c for c in j['cells']if c['character']in('riko','rin')])
j['previous_snapshot']={'path':P.relative_to(ROOT).as_posix(),'sha256':sha(P)}
def ev(k,p,purpose,h=None):
 actual=sha(p)
 if h:assert actual==h,str(p)
 j['evidence'][k]={'path':p.relative_to(ROOT).as_posix(),'sha256':actual,'purpose':purpose}
def state(status,label,refs):return {'status':status,'label':label,'refs':refs}
j['prior_integration']=copy.deepcopy(j['integration']);j['integration']={}
for key,project,version in(('br18','ver_buki_riko',18),('rn25','ver_rin_nana',25)):
 tag='br'if key.startswith('br')else'rn';planp=B/f'staging_{tag}_v{version}.json';mp=ROOT/f'out/{project}/sprite_style_unification_20261107_v{version}/manifest.json';np=B/f'staging_{tag}_v{version}_native_checks.json'
 plan,disc=read(planp),read(mp);assert read(np)['passed']
 assert disc['all_disc_sectors_compared']==251793 and disc['disc_readback_verified']and disc['gameplay_timing_code_palettes_audio_preserved']
 for name,v in plan['resources'].items():assert v['after']==disc['resources'][name]['after']
 # 이전 증거는 불변으로 남긴다. 같은 BR18은 기존 키를 재작성하지 않는다.
 if key not in j['evidence']:
  ev(key,planp,'최신 통합 계획. 집계에서 새 빌드/검사를 실행하지 않았다.')
  ev(key+'_disc',mp,'전섹터·EDC/ECC·재추출 기존 빌드 기록.')
  ev(key+'_native',np,'통합 원MIPS/GPU 기존 검사. 재실행하지 않았다.')
 j['integration'][key]={'output':plan['output'],'resources':plan['resources'],'bin_sha256':disc['modified_bin']['sha256']}
assert j['integration']['br18']['bin_sha256']=='b0bc7e3105966fbca46bb28b6dd8e2ae5daf4b785cd1ffb203b0bdfde6bfcc88'
assert j['integration']['rn25']['bin_sha256']=='5c1bf4af3625fd80271c26bc6bcdf9ed1bf9ab868b6bfc53edb07f2275bc8ec4'
assert sha(B/'staging_rn_v25.json')=='0ad0c5dc63d2f5d6b3ef07fd00ff5e80facef24d8992de974236917a102fe281'
entries={
 'nana_ledger17':(N/'scope_summary_v17/manifest.json','최신 담당 장부.506은 의상 중복 포함 동결참조 수로 완료율이 아니다.'),
 'shibuki_ledger23':(H/'fullform_ledger23.json','등장8 준비/별도미완료135를 구분한 담당 스냅샷. 후속 독립검사와 아래 별도 연결.'),
 'nana_lowhp22_runtime_failed':(B/'runtime/nana_base_lowhp22_summary.json','RN22 기본형 실기에서 저체력120..125 발동 실패.기존33관측참조 성공과 분리.'),
 'nana_victory4_frozen':(N/'ultimate_victory_repaint/packed_victory_candidate_v1/FROZEN.json','Ultimate승리4 동결·RN23 이후 누적통합.실기 미검증.'),
 'nana_victory4_reader':(D/'nana_ultimate_victory4_independent01/report.json','20층/128부분·정본권총·207외부공유 독립 읽기.'),
 'nana_victory4_visual':(D/'nana_ultimate_victory4_independent01/visual_review.json','새 재추출2판 실제열람.'),
 'nana_return3_frozen':(N/'ultimate_return_repaint/packed_return_candidate_v1/FROZEN.json','156/157/158 새귀환3 동결·RN25 통합.실제귀환 미검증.'),
 'nana_return3_reader':(D/'nana_ultimate_return3_independent01/report.json','생성3고정셀 재양자화·허리40셀·역사빛1875px→15층96부분 독립.'),
 'nana_return3_visual':(D/'nana_ultimate_return3_independent01/visual_review.json','새 귀환3판 실제열람.원표/실기는 별도.'),
 'nana_special4_frozen':(B/'root_nana_special/packed_special02/FROZEN.json','기본/포스95/96/98/99 동결·RN24 이후 누적통합.'),
 'nana_special4_reader':(D/'nana_base_special4_independent01/report.json','생성4셀→접점·공통층→20층128부분 독립 재구성.'),
 'nana_special4_visual':(D/'nana_base_special4_independent01/visual_review.json','새 전체2+부분2판 실제열람.'),
 'nana_special95_relations':(D/'nana_special95_98_relations01/conclusions.json','95/96·98/99 x+1·원표95/96/97/104/105 실제공유와호출 조사.'),
 'nana_standing_registered':(B/'root_nana_standing/registered01/manifest.json','89/97 새원화 초기등록.눈/상의하의접점 미완료,88파생은후속.'),
 'nana_settle_registered':(N/'base_settle_repaint/body_registered_v1/registration.json','기본/포스138 새원화 초기등록.139 y-1 연동 예정;최종패킹 부모는루트후속동결.'),
 'shibuki_arrival8_proposal':(H/'prepared_ultimate_arrival_partial01/proposal.json','새5몸체·3효과파생 총8 준비본.135 제외/부모보존.'),
 'shibuki_arrival8_reader':(D/'shibuki_ultimate_arrival8_independent01/report.json','40층256부분·역사 전체효과/가려진배경·132/135보존 독립.'),
 'shibuki_arrival8_visual':(D/'shibuki_ultimate_arrival8_independent01/visual_review.json','새 전체4+부분4판 실제열람.'),
 'shibuki_arrival8_native':(H/'ultimate_arrival_partial_components_native_checks.json','기존 원MIPS/GPU.이집계에서재실행않음.'),
 'shibuki_arrival8_root':(B/'root_review_checkpoint116.json','루트최종재추출6·부분4·원순서6 실제열람.'),
 'shibuki_victory_first_registered':(H/'ultimate_victory_native01/report.json','204/205 전후 첫4 생성후 초기등록.최종의상/접점 검토전.')}
for k,(p,why)in entries.items():ev(k,p,why)
rt=read(B/'runtime/nana_base_lowhp22_summary.json')
assert not rt['target_trigger_verified']and not rt['new_lowhp_actual_frames_observed']and len(rt['observer_verified_frames'])==33
assert sha(B/'runtime/nana_base_lowhp22_summary.json')=='05d1fb557b7462d4493daf72718d8304d41415ea03cb5e1c02c1565d8340a7fd'
for i,e in enumerate(rt['evidence']):ev(f'nana_lowhp22_evidence{i}',ROOT/e['path'],'RN22 발동실패의 관측·종료·보호 기록.',e['sha256'])
freeze=H/'prepared_ultimate_arrival_partial01/FROZEN.json';shib_frozen=freeze.exists()
if shib_frozen:ev('shibuki_arrival8_frozen',freeze,'등장8 최종동결.현재BR18에는 미포함.')
album=ROOT/'out/sprite_style_unification_20261107/review_v23';am=read(album/'manifest.json')
ev('album23',album/'manifest.json','BR18/RN23 재추출 모음집.후속RN24특수4/RN25귀환3 미포함.')
ev('album23_browser',album/'browser_checks.json','모음집28폼/4재생루프 기존 검사.새브라우저실행없음.')
j['current_album']={'evidence':'album23','browser_evidence':'album23_browser','display_records':sum(q['references']for q in am['counts'].values()),'forms':sum(q['forms']for q in am['counts'].values()),'changed_display_records':len(am['changes']),'completion_percentage':None,'sources':am['sources'],'matches_latest_integration':False,'difference':'앨범23은BR18/RN23.최신RN25의특수4/귀환3 및후속시부키등장8은차기앨범대기.'}
assert j['current_album']['display_records']==4510 and j['current_album']['forms']==28 and len(am['changes'])==2442
for c in j['cells']:
 char,form,cat=c['character'],c['form'],c['category'];keys=[]
 if char=='shibuki':keys=['shibuki_ledger23']
 if char=='nana':keys=['rn25','nana_ledger17']
 if char=='nana'and form in('base','fourth')and cat=='hurt':
  c['note']='기존피격13 RN18실기근거 유지.새저체력6은 동결·RN22 이후 누적통합. RN22 기본 실기에서120..125발동실패/미관측이며기존33참조GPU성공과사망·재등장관측만별도기록.포스저체력실기성공근거도없다.'
  c['runtime_lowhp']={'evidence':'nana_lowhp22_runtime_failed','attempted_form':'base','target_trigger_verified':False,'new_refs_observed':[],'other_refs_verified_count':33,'all_gameplay_verified':False}
  keys+=['nana_lowhp22_runtime_failed']
 if char=='nana'and form in('base','fourth')and cat=='special':
  c['states']=[state('integrated_new_art','새2키+평행2파생 동결·RN25 누적통합','95,96,98,99'),state('registered_candidate','루트 새2키 접점 정합 중·88 파생예정','88,89,97'),state('review_before_decision','보존/수정 판단 추가 필요','85,86,90,91,208..212'),state('preserve_reviewed','기존 세부 보존 판단','87,92'),state('reachability_review_required','사용경로·몸체/효과 분류 추가','213..230'),state('integrated_new_art','라이징7 동결·기존 대표실기 유지','100..104,231,232')]
  c['note']='95/96 및98/99는실제원x+1공유를유지.95비발사사선총은새원화의손/총공통,98은정본85 수평20texel.새89/97 눈1px·부분접점은미완료.98/99기본포스수정을Ultimate에적용완료했다고하지않는다.'
  c['art_review']='특수4 전체2+부분2독립실제열람,root114 재추출2+부분2+원표10열람.실기미검증.'
  keys+=['nana_special4_frozen','nana_special4_reader','nana_special4_visual','nana_special95_relations','nana_standing_registered']
 if char=='nana'and form in('base','fourth')and cat=='ceremony':
  c['states']=[state('effect_only','기존 효과·실루엣 연동범위 분리','126..132,159..161'),state('needs_redraw','재작화 잔여','133..137,156..158,204..207'),state('registered_candidate','138 초기등록·139 y-1 공통화 예정','138,139'),state('review_before_decision','상세·실루엣 보존판단 추가','140'),state('preserve_reviewed','기존 대기/먼지 사본','141,142')]
  c['note']='Audio는새138 한자세양의상등록중이며139는원관계y-1파생예정.루트89/97후속동결부모에합류예정.기본/포스의나머지등장·승리·귀환을Ultimate동결로대체하지않는다.'
  keys+=['nana_settle_registered']
 if char=='nana'and form.startswith('ultimate')and cat=='ceremony':
  c['states']=[state('integrated_new_art','새5몸체 등장 동결·누적통합','133,135..138'),state('integrated_derived_effect','등장5 효과·연결 동결·누적통합','130,131,134,139,141'),state('integrated_new_art','승리4 동결·RN23 이후 통합','204..207'),state('integrated_new_art','귀환156 새2의상 동결·RN25 통합','156'),state('integrated_derived_effect','새156 테두리·원빛 동결·RN25 통합','157,158'),state('preserve_reviewed','대기파생 실루엣·사본','140,142'),state('effect_only','기존 순수 에너지/껍질','126..129,132,159..161')]
  c['note']='승리207/5→89 외부공유보존.귀환157은새156 y-1과Chebyshev1/2,158은y-10 새몸+원159빛1875px.구형afterguard/몸alpha클립미복사.실제승리·귀환장면완료는아직아님.'
  c['art_review']='등장5판·승리2판·귀환3판독립열람 및각FROZEN루트최종미술근거.집계에서미술을다시반복검사하지않음.'
  keys+=['nana_victory4_frozen','nana_victory4_reader','nana_victory4_visual','nana_return3_frozen','nana_return3_reader','nana_return3_visual']
 if char=='shibuki'and form.startswith('ultimate')and cat=='ceremony':
  status='frozen_candidate'if shib_frozen else'independently_verified_candidate'
  c['states']=[state(status,'새5몸체·미통합','133,136..139'),state(status,'3실루엣/구체 연동·미통합','130,131,134'),state('held_unfinished','도구거부편집보류·부모그대로보존','135'),state('preserve_reviewed','대기실루엣/먼지/연결 보존','140..142'),state('registered_candidate','승리 첫4표시 초기등록','204,205'),state('review_before_decision','별도 상세/효과 추가검토','156..158,206,207'),state('effect_only','기존 순수광선/구체','126..129,132,159..161')]
  c['note']='등장8의after138/139흰소매오류는다른자세국소원화로교정.135거부편집은우회하지않고그대로보존.136/139는별도원화이며반전/평행가정없음.136새발만y+1;130131134전체배경·136137번개tile7·132공유비대상exact.현재BR18에는미포함.'
  c['art_review']='독립전체4+부분4실제열람,root116 재추출6+부분4+원순서6실제열람.새승리204/205는초기등록만이며최종수용전.'
  keys+=['shibuki_arrival8_proposal','shibuki_arrival8_reader','shibuki_arrival8_visual','shibuki_arrival8_native','shibuki_arrival8_root','shibuki_victory_first_registered']
  if shib_frozen:keys+=['shibuki_arrival8_frozen']
 c['evidence']=list(dict.fromkeys(c['evidence']+keys))
j['next_work']=[
 {'owner':'overhaul_ui','character':'shibuki','scope':'Ultimate 등장8 통합·승리204..207','stage':'등장8 독립/루트/MIPS 통과.135는도구거부로부모보존·미완료.승리204/205첫4초기등록이며206/207·귀환은후속.','evidence':['shibuki_arrival8_reader','shibuki_arrival8_root','shibuki_arrival135_incomplete','shibuki_victory_first_registered']},
 {'owner':'root','character':'nana','scope':'기본/포스89/97 및88파생','stage':'새2원화등록중.눈높이·상하의부분접점정합이남아있음.특수95/96/98/99는이미동결·RN25누적통합.','evidence':['nana_standing_registered','nana_special4_frozen','rn25']},
 {'owner':'overhaul_audio','character':'nana','scope':'기본/포스138 및139연결','stage':'새138 한자세양의상초기등록.139 y-1전개예정;후속부모와공통층/정본총구패킹은미완료.','evidence':['nana_settle_registered','nana_ledger17']},
 {'owner':'root','character':'nana','scope':'저체력·사다리·특수·승리귀환 대표실기','stage':'저체력RN22는발동실패를유지.관측하지않은새모션은원MIPS/원표검사를실기성공으로대체하지않음.','evidence':['nana_lowhp22_runtime_failed','nana_ladder_frozen','nana_special4_frozen','nana_victory4_frozen','nana_return3_frozen']},
 {'owner':'overhaul_ui + overhaul_audio','character':'shibuki,nana','scope':'남은폼의별도등장승리귀환·정지사격·특수·차량','stage':'각담당장부의보존/신규작업/사용분류를계속유지.한폼완료를다른폼으로확대하지않음.','evidence':['shibuki_ledger23','nana_ledger17']},
 *[p for p in read(P)['next_work']if p['character']in('riko,rin','all')]]
j['snapshot_summary']='BR18/RN25 최신통합과앨범23(BR18/RN23)을분리.나나특수4·Ultimate승리4/귀환3 동결/통합,시부키Ultimate등장8독립/루트검토와135보류를연결.저체력실기발동실패유지.전체작업계속중이며표시수는완료율아님.'
j['completed_milestones_since_previous']=[{'scope':s,'evidence':e,'runtime_verified':False}for s,e in[
 ('Nana Ultimate승리4 동결·RN25누적통합',['nana_victory4_frozen','rn25']),('Nana 기본포스특수4 동결·RN25누적통합',['nana_special4_frozen','rn25']),('Nana Ultimate귀환3 동결·RN25통합',['nana_return3_frozen','rn25']),('Shibuki Ultimate등장8 독립/루트최종검토·미통합',['shibuki_arrival8_reader','shibuki_arrival8_root'])]]
j['all_art_complete']=j['all_gameplay_verified']=j['user_final_accepted']=j['game_or_art_modified']=False
assert old_zero==[c for c in j['cells']if c['character']in('riko','rin')]
for k,v in old_ev.items():assert j['evidence'][k]==v
for c in j['cells']:
 for k in c['evidence']:assert k in j['evidence']
O.mkdir(exist_ok=True);(O/'coverage.json').write_text(json.dumps(j,ensure_ascii=False,indent=2)+'\n','utf8')
esc=html.escape
def link(k):
 e=j['evidence'][k];p=os.path.relpath(ROOT/e['path'],O).replace('\\','/');return f'<a href="{esc(p)}">{esc(k)}</a>'
page=['<!doctype html><html lang="ko"><meta charset="utf-8"><title>전체 폼·모션 범위 BR18 RN25 · 갱신07</title>',
 '<style>body{background:#111820;color:#e9edf2;font:15px system-ui;margin:24px}a{color:#9dcfff}table{border-collapse:collapse;width:100%;margin:18px 0 35px}th,td{border:1px solid #405164;padding:10px;text-align:left;vertical-align:top}th{background:#233547}summary{cursor:pointer}small{color:#b7c5d4}.notice{padding:16px;background:#263547}</style>',
 '<h1>네 캐릭터 · 폼별 모션 범위</h1><p>BR18 / RN25 · 12폼 × 12범주. <b>수정 수는 미술 완료율이 아닙니다.</b></p>',
 '<p class="notice">'+esc(j['snapshot_summary'])+'</p>',
 '<p><a href="coverage.json">전체 JSON</a> · <a href="../full_scope_matrix06/COVERAGE.html">이전 스냅샷</a> · <a href="../final_endpoint_audit01/ZERO_UI_HQ_SUPPLEMENT.html">Zero UI/HQ</a> · <a href="../x_endpoint_supplement01/X_UI_HQ_SUPPLEMENT.html">X UI/HQ</a></p>',
 '<p>통합/관찰: '+' · '.join(link(k)for k in('br18','rn25','album23','nana_lowhp22_runtime_failed'))+'</p><h2>다음 작업</h2><table><tr><th>담당</th><th>범위</th><th>상태</th></tr>']
for q in j['next_work']:page.append('<tr>'+''.join('<td>'+esc(q[k])+'</td>'for k in('owner','scope','stage'))+'</tr>')
page.append('</table>')
for char,name in {'shibuki':'시부키','nana':'나나','riko':'리코','rin':'린'}.items():
 for form,title in j['forms'].items():
  cells=[c for c in j['cells']if c['character']==char and c['form']==form]
  if not cells:continue
  page.append('<h2>'+name+' · '+esc(title)+'</h2><table><tr><th>범주</th><th>상태·참조</th><th>판단·남은 범위</th><th>실제 열람·근거</th></tr>')
  for c in cells:
   states='<br>'.join(esc(s['label']+': '+s['refs'])for s in c['states'])or'별도 사본 범위'
   page.append('<tr><td>'+esc(j['categories'][c['category']])+'</td><td>'+states+'</td><td>'+esc(c['note'])+'</td><td><small>'+esc(c['art_review'])+'</small><details><summary>근거</summary>'+'<br>'.join(link(k)for k in c['evidence'])+'</details></td></tr>')
  page.append('</table>')
page.append('<h2>한계</h2><ul>'+''.join('<li>'+esc(q)+'</li>'for q in j['coverage_limits'])+'</ul></html>')
(O/'COVERAGE.html').write_text('\n'.join(page),'utf8');links=re.findall(r'href="([^"]+)"',(O/'COVERAGE.html').read_text('utf8'))
assert all((O/html.unescape(p)).resolve().is_file()for p in links)
v={'passed':True,'cells':len(j['cells']),'evidence_files':len(j['evidence']),'local_links':len(links),'broken_links':0,'previous_snapshot_sha256':sha(P),'zero_cells_unchanged':True,'new_gameplay_or_native_tests_performed':False,'browser_test_performed':False,'all_art_complete':False,'game_or_art_modified':False,'album_RN23_not_RN25':True,'shibuki_arrival8_frozen_at_snapshot':shib_frozen}
(O/'verification.json').write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n','utf8')
print(json.dumps({'json_sha256':sha(O/'coverage.json'),'html_sha256':sha(O/'COVERAGE.html'),**v}))
