"""BR20/RN28과 기존 실기·신규 후보를 연결한다. 게임/원화/검사는 재실행하지 않는다."""
from pathlib import Path
import copy,hashlib,html,json,os,re
ROOT=Path(__file__).resolve().parents[3];D=Path(__file__).parent;B=D.parent;H=B/'shibuki_audit';N=B/'nana_audit'
P=D/'full_scope_matrix07/coverage.json';O=D/'full_scope_matrix08'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();read=lambda p:json.loads(p.read_text('utf8'))
assert sha(P)=='0b7296f4278b7595506a280b6973cf0152e1a08dd97015166e1210c62ff677e3'
j=read(P);old_ev=copy.deepcopy(j['evidence']);old_zero=copy.deepcopy([c for c in j['cells']if c['character']in('riko','rin')])
j['previous_snapshot']={'path':P.relative_to(ROOT).as_posix(),'sha256':sha(P)}
def ev(k,p,purpose):j['evidence'][k]={'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p),'purpose':purpose}
def state(status,label,refs):return {'status':status,'label':label,'refs':refs}
j['prior_integration']=copy.deepcopy(j['integration']);j['integration']={}
for key,project,version in(('br20','ver_buki_riko',20),('rn28','ver_rin_nana',28)):
 tag=key[:2];pp=B/f'staging_{tag}_v{version}.json';mp=ROOT/f'out/{project}/sprite_style_unification_20261107_v{version}/manifest.json';np=B/f'staging_{tag}_v{version}_native_checks.json'
 plan,disc=read(pp),read(mp);assert read(np)['passed']and disc['disc_readback_verified']and disc['all_disc_sectors_compared']==251793 and disc['gameplay_timing_code_palettes_audio_preserved']
 for name,q in plan['resources'].items():assert q['after']==disc['resources'][name]['after']
 for suffix,p,why in(('',pp,'최신 통합 계획'),('_disc',mp,'기존 전섹터·EDC/ECC·재추출 완료 기록'),('_native',np,'기존 통합 원MIPS/GPU 검사')):ev(key+suffix,p,why+'; 이번 집계에서 재실행하지 않음.')
 j['integration'][key]={'output':plan['output'],'resources':plan['resources'],'bin_sha256':disc['modified_bin']['sha256']}
assert j['integration']['br20']['bin_sha256']=='9bfd915f5e717781dd433eb291daa1aac1bad424734ad7decad69498d521598b'
assert j['integration']['rn28']['bin_sha256']=='9ea0cc759b2884d026a305b45ce21a2d97f78aa2682f27b6349b864039784f58'
entries={
 'nana_ledger18':(N/'scope_summary_v18/manifest.json','기본/포스standing3·138139 동결; Ultimate사다리후보.516표시는고유원화/완료율아님.'),
 'shibuki_ledger26':(H/'fullform_ledger26.json','승리4 동결·귀환원화접점미완료 당시 스냅샷.후속귀환독립은아래별도.'),
 'nana_standing3_frozen':(B/'root_nana_standing/packed_standing03/FROZEN.json','88/89/97 동결·RN26 이후 누적통합.'),
 'nana_standing3_independent':(D/'nana_base_standing3_independent01/report.json','생성4셀 및88원효과·부분15층 독립.'),
 'nana_standing3_visual':(D/'nana_base_standing3_independent01/visual_review.json','재추출5판 실제열람.'),
 'nana_settle2_frozen':(N/'base_settle_repaint/packed_settle_candidate_v1/FROZEN.json','138139 동결·RN27 이후 통합.'),
 'nana_settle2_independent':(D/'nana_base_settle2_independent01/report.json','같은행다리·머리표본·총 직교반사/이동 및139 y−1 독립.'),
 'nana_settle2_visual':(D/'nana_base_settle2_independent01/visual_review.json','재추출전체·부분2판 실제열람.'),
 'nana_recoil2_frozen':(B/'root_nana_recoil/packed_recoil03/FROZEN.json','90/91 동결·RN28 통합.실기미검증.'),
 'nana_recoil2_independent':(D/'nana_base_recoil2_independent01/report.json','생성4셀→10층64RGBA/32GPU·head9조립만재사용/기존9픽셀보존 독립.'),
 'nana_recoil2_visual':(D/'nana_base_recoil2_independent01/visual_review.json','최종전체2·부분2판 실제열람.'),
 'nana_special26_runtime':(B/'runtime/nana_fourth_special26_summary.json','RN26 포스 양방향88/89/95..99 대표실기.90/91 및138139는당시구형.'),
 'nana_special26_root':(B/'root_review_checkpoint120.json','815실창중22시간순판 root 직접열람.한전환미검증 유지.'),
 'shibuki_victory4_frozen':(H/'prepared_ultimate_victory01/FROZEN.json','Ultimate승리4 동결·BR20 통합.'),
 'shibuki_victory4_independent':(D/'shibuki_ultimate_victory4_independent01/report.json','새공통몸·손/발 국소정합→20층128RGBA 독립.'),
 'shibuki_victory4_visual':(D/'shibuki_ultimate_victory4_independent01/visual_review.json','새8표시 재추출2판 실제열람.'),
 'shibuki_return3_proposal':(H/'prepared_ultimate_return01/proposal.json','f40f 귀환3 준비본.현재BR20에는미포함.'),
 'shibuki_return3_independent':(D/'shibuki_ultimate_return3_independent01/report.json','생성4셀→접점/15층96RGBA·158역사19타일/18prefix 보호.'),
 'shibuki_return3_visual':(D/'shibuki_ultimate_return3_independent01/visual_review.json','최종3판 실제열람.'),
 'shibuki_return3_contact':(D/'shibuki_ultimate_return3_independent01/contact_constraints.json','기본/Ultimate 손발원점·beam_out 정지단계 코드읽기.실기아님.'),
 'nana_ultimate_ladder_relations':(D/'nana_ultimate_ladder_relations01/conclusions.json','before반전exact/after차이·9raw공유/빈층비대상별칭·사격총구 관계.'),
 'nana_ultimate_ladder_first3':(N/'ultimate_ladder_repaint/a_layers_probe_v1/manifest.json','143144146 첫3양폼 부분레이어 후보.ARC미패킹.')}
for k,(p,why)in entries.items():ev(k,p,why)
fr=H/'prepared_ultimate_return01/FROZEN.json';return_frozen=fr.exists()
if return_frozen:ev('shibuki_return3_frozen',fr,'귀환3 동결·현재BR20미통합.')
rt=read(B/'runtime/nana_fourth_special26_summary.json');assert rt['captured_windows']==815 and rt['root_actually_viewed_board_count']==22 and rt['session_closed']and not rt['process_memory_written']
j['new_runtime_scope']={'evidence':'nana_special26_runtime','form':'fourth','new_refs_verified':[88,89,95,96,97,98,99],'unverified_event_count':sum(len(q['unverified_events'])for q in rt['cases']),'later_new_refs_not_covered':[90,91,138,139],'all_gameplay_verified':False}
album=ROOT/'out/sprite_style_unification_20261107/review_v24';am=read(album/'manifest.json')
ev('album24',album/'manifest.json','BR20/RN27 모음집.새RN28 recoil2는미포함.');ev('album24_browser',album/'browser_checks.json','모음집28폼/4루프 기존검사.재실행없음.')
j['current_album']={'evidence':'album24','browser_evidence':'album24_browser','display_records':sum(q['references']for q in am['counts'].values()),'forms':sum(q['forms']for q in am['counts'].values()),'changed_display_records':len(am['changes']),'completion_percentage':None,'sources':am['sources'],'matches_latest_integration':False,'difference':'앨범24는BR20/RN27.새90/91통합RN28은다음앨범대상이며시부키귀환3도현재BR20미포함.'}
assert j['current_album']['display_records']==4510 and j['current_album']['forms']==28 and len(am['changes'])==2499
for c in j['cells']:
 char,form,cat=c['character'],c['form'],c['category'];keys=[]
 if char=='nana':keys+=['rn28','nana_ledger18']
 if char=='shibuki':keys+=['br20','shibuki_ledger26']
 if char=='nana'and form in('base','fourth')and cat=='special':
  c['states']=[state('integrated_new_art','특수4·standing3·recoil2 동결/누적통합','88,89,90,91,95..99'),state('review_before_decision','상세보존/추가제작 판단','85,86,208..212'),state('preserve_reviewed','기존세부 보존판단','87,92'),state('reachability_review_required','사용경로·효과분류 추가','213..230'),state('integrated_new_art','라이징7 기존동결·대표실기','100..104,231,232')]
  c['note']='새90/91은head9 조립기록2개만재사용하고새머리픽셀을원화그대로저장했다.원형9전체보존.후속실기는아직없다.'
  c['art_review']='standing5판/settle2판/recoil4판 독립실제열람과각FROZEN루트검토.'
  if form=='fourth':c['note']+=' RN26 양방향88/89/95..99 실기성공,815캡처중22판root열람.전환1미확정.그때90/91·138139는구형이므로새후속실기증거가아니다.';keys+=['nana_special26_runtime','nana_special26_root']
  else:c['note']+=' RN26 포스실기를기본형실기로확장하지않는다.'
  keys+=['nana_standing3_frozen','nana_standing3_independent','nana_recoil2_frozen','nana_recoil2_independent','nana_recoil2_visual']
 if char=='nana'and form in('base','fourth')and cat=='ceremony':
  c['states']=[state('effect_only','기존효과 분리','126..132,159..161'),state('needs_redraw','재작화잔여','133..137,156..158,204..207'),state('integrated_new_art','새138동결·139 y−1파생/RN27이후통합','138,139'),state('review_before_decision','상세/실루엣검토','140'),state('preserve_reviewed','대기/먼지사본','141,142')]
  c['note']='138 새머릿결국소표본/정본권총·같은행다리·베일owner를보존한후139 y−1.두폼64RGBA검사와최종시각통과,실제새138/139관측은미확인.';keys+=['nana_settle2_frozen','nana_settle2_independent','nana_settle2_visual']
 if char=='nana'and form.startswith('ultimate')and cat=='ladder':
  c['states']=[state('registered_candidate','첫3양폼 공통손/부분레이어 후보','143,144,146'),state('held_unfinished','등록후하의교정도구거부·우회없음','149,151,153'),state('input_prepared','남은몸체·사격·반전 준비','145,147,148,150,152,154,155,183')]
  c['note']='현재493bf 기존before4반전은exact이나after는159/244/183/150px차이.새공통반전은원US동일복원이아닌제작정책.150/155는149기반의기존정책이며154복사근거없음.원총구(-24,-9)/(-21,-13) 보호.최종ARC는미작성.'
  c['art_review']='현재자원5관계판+첫3공통후보2판 독립 실제열람.새144주먹/커프 연결에추가확정단절못찾음.등록후보를완료집계하지않음.';keys+=['nana_ultimate_ladder_relations','nana_ultimate_ladder_first3']
 if char=='shibuki'and form.startswith('ultimate')and cat=='ceremony':
  c['states']=[state('integrated_new_art','새5몸체·BR19이후통합','133,136..139'),state('integrated_derived_effect','3실루엣/구체연동·통합','130,131,134'),state('held_unfinished','도구거부편집보류·부모보존','135'),state('preserve_reviewed','대기/먼지연결','140..142'),state('integrated_new_art','승리4동결·BR20통합','204..207'),state('frozen_candidate'if return_frozen else'independently_verified_candidate','귀환3독립통과·BR20미포함','156..158'),state('effect_only','기존순수광선/구체','126..129,132,159..161')]
  c['note']='136/139는별도원화;135미완료그대로.승리206/207 발+1/207손−1은새원화정합정책.귀환157은옛가림을복사않는새몸9/14테두리;158은원159의19저장타일/18prefix뒤새몸6파트.귀환실기는별도.'
  c['art_review']='등장·승리FROZEN의루트/독립열람과귀환3재추출·손발원점판실제열람.집계에서이미지를다시검사하지않음.'
  keys+=['shibuki_victory4_frozen','shibuki_victory4_independent','shibuki_victory4_visual','shibuki_return3_proposal','shibuki_return3_independent','shibuki_return3_visual','shibuki_return3_contact']
  if return_frozen:keys+=['shibuki_return3_frozen']
 c['evidence']=list(dict.fromkeys(c['evidence']+keys))
j['next_work']=[
 {'owner':'overhaul_ui','character':'shibuki','scope':'Ultimate귀환3 동결/통합과남은전폼세부','stage':'f40f독립·미술통과,BR20에는아직없음.135거부보류/전폼정지사격·특수·차량별도잔여.','evidence':['shibuki_return3_independent','shibuki_ledger26']},
 {'owner':'overhaul_audio','character':'nana','scope':'Ultimate사다리14','stage':'첫3양폼부분후보,149151153하의교정거부미완료.남은몸체·사격·반전최종화전.','evidence':['nana_ultimate_ladder_first3','nana_ultimate_ladder_relations','nana_ledger18']},
 {'owner':'root','character':'nana','scope':'기본/포스남은등장·승리·귀환·정지사격/특수','stage':'90/91은RN28통합.새138139/90/91대표실기미확인,기본/포스133..137등잔여상세제작을계속.','evidence':['rn28','nana_recoil2_frozen','nana_ledger18']},
 {'owner':'root','character':'nana','scope':'저체력·사다리·후속 대표실기','stage':'저체력발동실패유지.포스RN26대표실기를기본/부분파츠나새후속실기로확대하지않음.','evidence':['nana_lowhp22_runtime_failed','nana_special26_runtime']},
 *[p for p in read(P)['next_work']if p['character']in('riko,rin','all')]]
j['snapshot_summary']='BR20/RN28 통합과앨범24(BR20/RN27)를분리했다.나나standing3·settle2·recoil2와시부키Ultimate등장8·승리4통합,새귀환3독립후보·Ultimate사다리미완료를갱신했다.RN26포스대표실기와후속구형관측을구분하며저체력발동실패유지.전체작업계속중/표시수는완료율아님.'
if return_frozen:
 j['snapshot_summary']=j['snapshot_summary'].replace('새귀환3독립후보','새귀환3동결·미통합')
 j['next_work'][0]['stage']='f40f 동결 완료, BR20에는 아직 없음. 135 거부 보류/전폼 정지사격·특수·차량은 별도 잔여.'
 j['next_work'][0]['evidence'].append('shibuki_return3_frozen')
j['completed_milestones_since_previous']=[{'scope':x,'evidence':e,'runtime_verified':False}for x,e in[('나나standing3·settle2·recoil2통합',['rn28']),('시부키등장8·승리4통합',['br20']),('시부키귀환3독립후보',['shibuki_return3_independent'])]]
j['all_art_complete']=j['all_gameplay_verified']=j['user_final_accepted']=j['game_or_art_modified']=False
assert old_zero==[c for c in j['cells']if c['character']in('riko','rin')]
for k,v in old_ev.items():assert j['evidence'][k]==v
for c in j['cells']:
 for k in c['evidence']:assert k in j['evidence']
O.mkdir(exist_ok=True);(O/'coverage.json').write_text(json.dumps(j,ensure_ascii=False,indent=2)+'\n','utf8')
# 이전 스냅샷의 정적 HTML 출력 블록만 현재 객체에 사용한다.
source=(D/'update_full_scope_matrix07.py').read_text('utf8');render=source[source.index('esc=html.escape'):source.index("v={'passed':True")]
render=render.replace('BR18 RN25 · 갱신07','BR20 RN28 · 갱신08').replace('BR18 / RN25','BR20 / RN28').replace('full_scope_matrix06/COVERAGE.html','full_scope_matrix07/COVERAGE.html').replace("('br18','rn25','album23','nana_lowhp22_runtime_failed')", "('br20','rn28','album24','nana_special26_runtime','nana_lowhp22_runtime_failed')")
exec(compile(render,'scope08_static_html','exec'))
v={'passed':True,'cells':len(j['cells']),'evidence_files':len(j['evidence']),'local_links':len(links),'broken_links':0,'zero_cells_unchanged':True,'new_gameplay_or_native_tests_performed':False,'browser_test_performed':False,'all_art_complete':False,'game_or_art_modified':False,'album_RN27_not_RN28':True,'shibuki_return3_frozen_at_snapshot':return_frozen}
(O/'verification.json').write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps({'json_sha256':sha(O/'coverage.json'),'html_sha256':sha(O/'COVERAGE.html'),**v}))
