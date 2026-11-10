"""BR18/RN22 범위 스냅샷. 기존 증거만 연결하며 게임/통과 검사는 재실행하지 않는다."""
from pathlib import Path
import copy,hashlib,html,json,os,re
ROOT=Path(__file__).resolve().parents[3];D=Path(__file__).parent;B=D.parent;H=B/'shibuki_audit';N=B/'nana_audit'
P=D/'full_scope_matrix05/coverage.json';O=D/'full_scope_matrix06'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();read=lambda p:json.loads(p.read_text(encoding='utf8'))
assert sha(P)=='4e3b43624e5e3d14a66881d759c7508e547d8ce5b3120415e4ecfc79e00c33be'
j=read(P);old_ev=copy.deepcopy(j['evidence']);old_zero=copy.deepcopy([c for c in j['cells']if c['character']in('riko','rin')])
j['previous_snapshot']={'path':P.relative_to(ROOT).as_posix(),'sha256':sha(P)}
def ev(k,p,purpose,h=None):
 actual=sha(p)
 if h:assert actual==h,str(p)
 j['evidence'][k]={'path':p.relative_to(ROOT).as_posix(),'sha256':actual,'purpose':purpose}
def state(status,label,refs):return {'status':status,'label':label,'refs':refs}
for e in old_ev.values():assert sha(ROOT/e['path'])==e['sha256'],e['path']
j['prior_integration']=copy.deepcopy(j['integration']);j['integration']={}
for key,project,version in(('br18','ver_buki_riko',18),('rn22','ver_rin_nana',22)):
 tag='br'if key.startswith('br')else'rn';planp=B/f'staging_{tag}_v{version}.json';manifest=ROOT/f'out/{project}/sprite_style_unification_20261107_v{version}/manifest.json';native=B/f'staging_{tag}_v{version}_native_checks.json'
 plan,disc=read(planp),read(manifest);assert read(native)['passed']
 assert disc['all_disc_sectors_compared']==251793 and disc['disc_readback_verified']and disc['gameplay_timing_code_palettes_audio_preserved']
 for name,v in plan['resources'].items():assert v['after']==disc['resources'][name]['after']
 ev(key,planp,'최신 통합 계획. 새 빌드/검사를 이 집계에서 실행하지 않았다.');ev(key+'_disc',manifest,'전섹터·재추출·EDC/ECC 기존 빌드 기록.');ev(key+'_native',native,'통합 원MIPS/GPU 기존 검사. 재실행하지 않았다.')
 j['integration'][key]={'output':plan['output'],'resources':plan['resources'],'bin_sha256':disc['modified_bin']['sha256']}
assert j['integration']['br18']['bin_sha256']=='b0bc7e3105966fbca46bb28b6dd8e2ae5daf4b785cd1ffb203b0bdfde6bfcc88'
assert j['integration']['rn22']['bin_sha256']=='769929d3ed42663897afd1e6afc42c74fd4f5d2885efa4a8d2340d4b948b3e6c'
entries={
 'shibuki_ledger21':(H/'fullform_ledger21.json','전폼 실제 재독출 고유표시 분류의 최신 담당 스냅샷. 완료율 아님.'),
 'shibuki_hurt_base_frozen':(H/'prepared_hurt_base01/FROZEN.json','기본/포스13 최종 동결.'),
 'shibuki_hurt_ultimate_frozen':(H/'prepared_ultimate_hurt02/FROZEN.json','Ultimate13 v2 동결. 첫 후보8c9a는GPU경계 실패로 미채택.'),
 'shibuki_hurt_ultimate_reader':(D/'shibuki_ultimate_hurt13_independent01/report.json','65층/416부분/원FX·111tile16→31 복제 독립 읽기.'),
 'shibuki_hurt_ultimate_visual':(D/'shibuki_ultimate_hurt13_independent01/visual_review.json','최종5재추출판 독립 실제열람.'),
 'shibuki_arrival_relations':(D/'shibuki_ultimate_arrival_relations01/conclusions.json','126..142 공유·광선·번개·135136/138139 실제차이 독립 조사.'),
 'shibuki_arrival_native_first':(H/'ultimate_arrival_native01/report.json','133/135 전후 초기등록. 채택·통합과 구분.'),
 'shibuki_arrival_native_second':(H/'ultimate_arrival_native02/report.json','137/138 전후 초기등록. after138 소매는 미수용.'),
 'shibuki_arrival135_incomplete':(H/'ultimate_arrival135_arms01/generation_failure.json','after135 국소 편집 미완료. 담당자가 우회/재시도 없이 보류한 기록.'),
 'nana_ledger15':(N/'scope_summary_v15/manifest.json','나나 등장10/기본포스 사다리14 동결 반영 담당 장부.'),
 'nana_ladder_frozen':(B/'root_nana_ladder/packed_ladder07/FROZEN.json','기본/포스14 새 사다리 동결. RN22 누적통합.'),
 'nana_ladder_reader':(D/'nana_base_ladder14_independent01/report.json','70층/4반전/448부분/64총구 조건 독립.'),
 'nana_ladder_visual':(D/'nana_base_ladder14_independent01/visual_review.json','부분소유 및 실제 재추출판 독립열람.'),
 'nana_lowhp_frozen':(B/'root_nana_lowhp/packed_lowhp01/FROZEN.json','기본/포스 저체력6 동결. RN22 통합,실기 아직미확인.'),
 'nana_lowhp_reader':(D/'nana_base_lowhp6_independent01/report.json','등록4PNG부터 입/호흡/동일행다리/베일소유→30층·192부분 독립.'),
 'nana_lowhp_visual':(D/'nana_base_lowhp6_independent01/visual_review.json','전후2·부분3 새재추출판 실제열람.'),
 'nana_arrival_frozen':(N/'ultimate_ceremony_repaint/packed_arrival_candidate_v1/FROZEN.json','Ultimate 등장10 동결.새5몸체+효과/연결5파생.'),
 'nana_arrival_reader':(D/'nana_ultimate_arrival10_independent01/report.json','권총·손·새하체·역사광선/번개/먼지→50층320부분 독립.'),
 'nana_arrival_visual':(D/'nana_ultimate_arrival10_independent01/visual_review.json','최종 재추출5판 실제열람.'),
 'nana_victory_relations':(D/'nana_ultimate_victory_relations01/conclusions.json','204..207 raw독립·공유89의상/빈층·표39/40/역사빈손·권총 독립읽기.'),
 'nana_victory_registered':(N/'ultimate_victory_repaint/costume_pair_probe_v2/manifest.json','승리4양폼 공통의상 후보. 최종미술/패킹/동결 전.')}
for k,(p,why)in entries.items():ev(k,p,why)
assert sha(B/'root_nana_lowhp/packed_lowhp01/FROZEN.json')=='fbab5575a8ae8e18b4af3612f3d1b1d76540f4f1a828afc142aa6b5ae973b83e'
runtimepath=B/'runtime/shibuki_fourth_hurt17_summary.json';rt=read(runtimepath)
assert rt['verified_new_references']==[233,234,235,236]and rt['actual_captures']==160 and rt['root_viewed_boards']==12 and not rt['unknown_events']
assert rt['asset_sha256']==j['integration']['br18']['resources']['PL00_U.ARC']['after']
ev('shibuki_fourth_hurt17_runtime',runtimepath,'포스233..236 실제160창·루트12판. 기본/106..114 전체 실기 아님.')
for k in('observer','actual_review','root_review','close','protection'):
 e=rt[k];ev('shibuki_hurt17_'+k,ROOT/e['path'],'BR17 포스 피격 실제 증거 '+k,e['sha256'])
album=ROOT/'out/sprite_style_unification_20261107/review_v22';am=read(album/'manifest.json');ev('album22',album/'manifest.json','BR18/RN21 실제 BIN 재추출 모음집. RN22 저체력6은 아직 이 앨범에 미포함.');ev('album22_browser',album/'browser_checks.json','기존모음집 브라우저 검사 결과.')
j['current_album']={'evidence':'album22','browser_evidence':'album22_browser','display_records':sum(q['references']for q in am['counts'].values()),'forms':sum(q['forms']for q in am['counts'].values()),'changed_display_records':len(am['changes']),'completion_percentage':None,'sources':am['sources'],'matches_latest_integration':False,'difference':'이 앨범은BR18/RN21이며 최신RN22 저체력6은 후속앨범 대기.4510/2416을RN22의새수치로표현하지 않는다.'}
assert j['current_album']['display_records']==4510 and j['current_album']['forms']==28 and len(am['changes'])==2416
for c in j['cells']:
 char,form,cat=c['character'],c['form'],c['category'];keys=[]
 if char=='shibuki':keys=['br18','shibuki_ledger21']
 elif char=='nana':keys=['rn22','nana_ledger15']
 if char=='shibuki'and cat=='hurt':
  ultimate=form.startswith('ultimate');c['states']=[state('integrated_new_art','새4몸체 동결·BR18 누적통합','106,110,233,234'),state('integrated_derived_effect','효과파생9 동결·BR18 누적통합','107..109,111..114,235..236'),state('integrated_new_art','기존 새 저체력 동결 유지','120..125')]
  c['note']='Ultimate v2는111 overlay5의원효과tile16을빈31로복제해GPU경계수정;효과/새몸체표시는동일. BR18통합/원MIPS까지이며신규13실기는아직.'if ultimate else'기본/포스13 동결·누적통합.포스233..236만BR17에서160실창/12판성공,미확정0.기본106..114·모든방향/피해원/부분아머는실기미확인.'
  keys+=['shibuki_hurt_ultimate_frozen','shibuki_hurt_ultimate_reader','shibuki_hurt_ultimate_visual']if ultimate else['shibuki_hurt_base_frozen','shibuki_fourth_hurt17_runtime','shibuki_hurt17_root_review']
  c['art_review']='동결기록의루트/제작자및독립최종재추출열람을연결.이범위표는기존이미지를다시검사하지않았다.'
  if not ultimate:c['runtime_coverage']={'evidence':'shibuki_fourth_hurt17_runtime','observed_form':'fourth','current_cell_observed':form=='fourth','actual_captures':160,'root_viewed_boards':12,'new_references_with_successful_ram_gpu_sample':[233,234,235,236],'unverified_events':[],'all_gameplay_verified':False}
 if char=='shibuki'and form.startswith('ultimate')and cat=='ceremony':
  c['states']=[state('registered_candidate','新의상 초기등록·일부 미수용','133,135,137,138'),state('needs_redraw','단순별칭 아닌 별도원화 준비','136,139'),state('derived_pending','새133 실루엣/구체 연동 필요','130,131,134'),state('preserve_reviewed','대기파생 실루엣·먼지·연결 보존','140..142'),state('review_before_decision','후속 상세/원효과 검토','156..158,204..207'),state('effect_only','기존 순수광선/구체','126..129,132,159..161')]
  c['states'][0]['label']='새 의상 초기등록·일부 미수용'
  c['note']='136은135 y-1아님.139는before만138 y-1exact이고after135px차이.담당자는별도입력을준비한다.after135국소생성은미완료보류,after138긴흰소매는미수용.초기등록을전체완료로세지않는다.141/142는현재idle와먼지12를보존.'
  c['art_review']='기존126..142 다섯판 독립열람.새after138소매비교1판독립열람에서재킷소매잔류확인.다른새의상최종수용은아직.'
  keys+=['shibuki_arrival_relations','shibuki_arrival_native_first','shibuki_arrival_native_second','shibuki_arrival135_incomplete']
 if char=='nana'and form in('base','fourth')and cat=='ladder':
  c['states']=[state('integrated_new_art','10고유 새몸체/사격 동결·RN22 누적통합','143,144,146,149..151,153..155,183'),state('integrated_mirrored_art','4반전 파생 동결·누적통합','145,147,148,152')]
  c['note']='joint03/04와packed04/05는반려,최종joint05/packed07 509cc978만수용.원4반전/총구64조건·베일/머리부분소유·원MIPS 통과.실제사다리진입/손발접점은아직미확인.'
  c['art_review']='독립전체/부분12판및FROZEN루트실제열람근거.이번집계에서재검사하지않음.';keys+=['nana_ladder_frozen','nana_ladder_reader','nana_ladder_visual']
 if char=='nana'and form in('base','fourth')and cat=='hurt':
  c['states']=[s for s in c['states']if s['refs']!='120..125']+[state('integrated_new_art','새 저체력6 동결·RN22 통합','120..125')]
  c['note']='기존피격13의RN18실기근거유지.새저체력6은한몸/한픽셀입과접지호흡,새권총·동일행포스다리·베일legs연속소유를검증해RN22통합.현재root저체력실기준비/진행중이며결과는아직미확인.'
  c['art_review']='새저체력전후2+부분3 독립열람,root111 최종/원순서7판 수용은FROZEN에결속.게임수용과분리.';keys+=['nana_lowhp_frozen','nana_lowhp_reader','nana_lowhp_visual']
 if char=='nana'and form.startswith('ultimate')and cat=='ceremony':
  c['states']=[state('integrated_new_art','새5몸체 양의상 동결·RN22 누적통합','133,135..138'),state('integrated_derived_effect','광선·구체·상승·먼지5 연동 동결','130,131,134,139,141'),state('registered_candidate','승리4 양의상 등록/권총·공통층 정합','204..207'),state('review_before_decision','기존 상세·효과파생 보존 추가판단','156..158'),state('preserve_reviewed','대기파생 기존 실루엣/사본','140,142'),state('effect_only','기존 순수 에너지/껍질','126..129,132,159..161')]
  c['note']='c721 등장10은원권총정본20texel·새손/하체·원번개46px·먼지12와131/132분리보존검사를동결했다.새승리4는별도후속이며207 overlay5→89레코드와빈층공유를보호한다.원표39의81→204..207→idle 또는귀환40 연결은실기와구분.'
  c['art_review']='최종등장5판 독립 실제열람 및FROZEN루트검토.승리현재/원US/연결3판+역사원화열람은관계조사이며새승리최종수용아님.';keys+=['nana_arrival_frozen','nana_arrival_reader','nana_arrival_visual','nana_victory_relations','nana_victory_registered']
 c['evidence']=list(dict.fromkeys(c['evidence']+keys))
j['next_work']=[
 {'owner':'overhaul_ui','character':'shibuki','scope':'Ultimate 등장/승리/귀환','stage':'133/135/137/138 의상초기등록. after135편집미완료보류·after138소매미수용.136/139별도입력준비와광선파생은후속.','evidence':['shibuki_arrival_relations','shibuki_arrival_native_second','shibuki_arrival135_incomplete']},
 {'owner':'overhaul_audio','character':'nana','scope':'Ultimate 승리204..207','stage':'8표시 고정등록/권총·공통의상 정합.89의상레코드와빈층외부공유 보호.최종패킹·독립·미술검토전.','evidence':['nana_victory_registered','nana_victory_relations']},
 {'owner':'root','character':'nana','scope':'RN22 기본/포스 저체력6 대표실기','stage':'동결·통합·원MIPS 완료.실기는준비/진행중이며성공결과없음.','evidence':['rn22','nana_lowhp_frozen']},
 {'owner':'root','character':'shibuki,nana','scope':'누적 새 사다리/Ultimate피격/등장 대표실기','stage':'기존원MIPS와정적열람을유지.아직관측하지않은모션/폼을실기완료로표시하지않음.','evidence':['br18','rn22','shibuki_hurt_ultimate_frozen','nana_ladder_frozen','nana_arrival_frozen']},
 {'owner':'overhaul_ui + overhaul_audio','character':'shibuki,nana','scope':'남은 폼의등장승리귀환·특수85..99/208..212·차량/호버','stage':'원장별보존/새제작/도달추가판단을구분.한폼통과를다른폼으로확대하지않음.','evidence':['shibuki_ledger21','nana_ledger15']},
 *[p for p in read(P)['next_work']if p['character']in('riko,rin','all')]]
j['snapshot_summary']='BR18/RN22 최신통합. Shibuki피격13 전폼·Nana사다리14/저체력6/Ultimate등장10 동결연결.최신기존앨범v22는BR18/RN21로RN22저체력미포함.전체작업계속중이며수정표시수는완료율아님.'
j['completed_milestones_since_previous']=[{'scope':s,'evidence':e,'runtime_verified':False}for s,e in[
 ('Shibuki Ultimate피격13 v2동결·BR18통합',['shibuki_hurt_ultimate_frozen','br18']),('Nana 기본/포스 사다리14 동결·누적통합',['nana_ladder_frozen','rn22']),('Nana Ultimate등장10 동결·누적통합',['nana_arrival_frozen','rn22']),('Nana 기본/포스 저체력6 동결·RN22통합',['nana_lowhp_frozen','rn22'])]]
j['completed_milestones_since_previous'].append({'scope':'Shibuki 포스피격233..236 BR17대표실기','evidence':['shibuki_fourth_hurt17_runtime'],'actual_captures':160,'root_viewed_boards':12,'verified_new_references':[233,234,235,236],'unverified_events':0,'all_gameplay_verified':False})
j['all_art_complete']=j['all_gameplay_verified']=j['user_final_accepted']=j['game_or_art_modified']=False
assert old_zero==[c for c in j['cells']if c['character']in('riko','rin')]
for k,v in old_ev.items():assert j['evidence'][k]==v
for c in j['cells']:
 for k in c['evidence']:assert k in j['evidence']
O.mkdir(exist_ok=True);(O/'coverage.json').write_text(json.dumps(j,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
esc=html.escape
def link(k):
 e=j['evidence'][k];p=os.path.relpath(ROOT/e['path'],O).replace('\\','/');return f'<a href="{esc(p)}">{esc(k)}</a>'
page=['<!doctype html><html lang="ko"><meta charset="utf-8"><title>전체 폼·모션 범위 BR18 RN22 · 갱신06</title>',
 '<style>body{background:#111820;color:#e9edf2;font:15px system-ui;margin:24px}a{color:#9dcfff}table{border-collapse:collapse;width:100%;margin:18px 0 35px}th,td{border:1px solid #405164;padding:10px;text-align:left;vertical-align:top}th{background:#233547}summary{cursor:pointer}small{color:#b7c5d4}.notice{padding:16px;background:#263547}</style>',
 '<h1>네 캐릭터 · 폼별 모션 범위</h1><p>BR18 / RN22 · 12폼 × 12범주. <b>수정 수는 미술 완료율이 아닙니다.</b></p>',
 '<p class="notice">'+esc(j['snapshot_summary'])+'</p>',
 '<p><a href="coverage.json">전체 JSON</a> · <a href="../full_scope_matrix05/COVERAGE.html">이전 스냅샷</a> · <a href="../final_endpoint_audit01/ZERO_UI_HQ_SUPPLEMENT.html">Zero UI/HQ</a> · <a href="../x_endpoint_supplement01/X_UI_HQ_SUPPLEMENT.html">X UI/HQ</a></p>',
 '<p>통합/대표실기: '+' · '.join(link(k)for k in('br18','rn22','album22','shibuki_fourth_hurt17_runtime'))+'</p><h2>다음 작업</h2><table><tr><th>담당</th><th>범위</th><th>상태</th></tr>']
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
(O/'COVERAGE.html').write_text('\n'.join(page),encoding='utf8');links=re.findall(r'href="([^"]+)"',(O/'COVERAGE.html').read_text(encoding='utf8'));assert all((O/html.unescape(p)).resolve().is_file()for p in links)
v={'passed':True,'cells':len(j['cells']),'evidence_files':len(j['evidence']),'local_links':len(links),'broken_links':0,'previous_snapshot_sha256':sha(P),'zero_cells_unchanged':True,'new_gameplay_or_native_tests_performed':False,'browser_test_performed':False,'all_art_complete':False,'game_or_art_modified':False,'album_RN21_not_RN22':True}
(O/'verification.json').write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps({'json_sha256':sha(O/'coverage.json'),'html_sha256':sha(O/'COVERAGE.html'),**v}))
