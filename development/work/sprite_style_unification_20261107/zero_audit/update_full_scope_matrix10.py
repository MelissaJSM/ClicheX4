"""BR24/RN37 범위 스냅샷. 기존 동결/원화/게임을 변경하거나 검사를 재실행하지 않는다."""
from pathlib import Path
import copy,hashlib,html,json,os,re
ROOT=Path(__file__).resolve().parents[3];D=Path(__file__).parent;W=D.parent;N=W/'nana_audit';H=W/'shibuki_audit'
P=D/'full_scope_matrix09/coverage.json';O=D/'full_scope_matrix10';assert not O.exists(),O
read=lambda p:json.loads(p.read_text('utf8'));sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();rel=lambda p:p.relative_to(ROOT).as_posix()
old=read(P);j=copy.deepcopy(old);new={};j['previous_snapshot']={'path':rel(P),'sha256':sha(P)}
def ev(k,p,why):
 assert p.is_file() and k not in j['evidence'],(k,p)
 q={'path':rel(p),'sha256':sha(p),'purpose':why};j['evidence'][k]=q;new[k]=q
def state(status,label,refs):return {'status':status,'label':label,'refs':refs}
j['prior_integration']=copy.deepcopy(old['integration']);j['integration']={}
for k,project,v in [('br24','ver_buki_riko',24),('rn37','ver_rin_nana',37)]:
 pp=W/f'staging_{k[:2]}_v{v}.json';np=W/f'staging_{k[:2]}_v{v}_native_checks.json';mp=ROOT/f'out/{project}/sprite_style_unification_20261107_v{v}/manifest.json'
 plan,native,m=map(read,(pp,np,mp));assert native['passed'] and m['disc_readback_verified'] and m['all_disc_sectors_compared']==251793 and m['gameplay_timing_code_palettes_audio_preserved']
 for name,r in plan['resources'].items():assert r['after']==m['resources'][name]['after']==sha(ROOT/r['path'])
 for q in plan['candidate_freeze_bindings'].values():assert sha(ROOT/q['path'])==q['sha256']
 for suffix,p,why in [('',pp,'통합 계획·현재 자원 해시 결속'),('_native',np,'기존 원MIPS/GPU 결과; 새 실행 없음'),('_disc',mp,'기존 전섹터·재추출 검사; 새 실행 없음')]:ev(k+suffix,p,why)
 j['integration'][k]={'output':plan['output'],'bin_sha256':m['modified_bin']['sha256'],'resources':plan['resources'],'preserve_x_selection':plan['preserve_x_selection']}
assert j['integration']['br24']['bin_sha256']=='45b5e019396f37aaa623e2c23bd4b91ceff344826ef95b6496c41e3d55b91644'
assert j['integration']['rn37']['bin_sha256']=='8a7ee9c47d170c8869f5415e18dc23e920157e28e9d49d7762a7acebc416a01e'
entries={
 'nana_ledger23':(N/'scope_summary_v23/manifest.json','632 참조×폼 당시 장부. root85/86·87/92의 후속8표시는 별도 결합하며 고유원화 수가 아니다.'),
 'shibuki_ledger32':(H/'fullform_ledger32.json','BR23 기본85..92 통합·선택8 당시준비·Ultimate 후속미완료 장부.'),
 'nana_base_vehicle_frozen10':(W/'root_nana_vehicle/packed_vehicle03/FROZEN.json','기본/포스4새몸체·9Y별칭→13참조 동결·RN35 이후통합.'),
 'nana_base_vehicle_reader10':(D/'nana_base_vehicle13_independent01/report_clarified.json','조립은행6의40B 후미 재활용·독립 보존 근거. 미소비이지만 모두0이었다고 하지 않는다.'),
 'nana_ultimate_vehicle_frozen10':(N/'ultimate_vehicle_repaint/packed_vehicle_candidate_v1/FROZEN.json','Ultimate 차량13 동결·RN36 이후통합. 새몸4×두폼 및9별칭.'),
 'nana_ultimate_vehicle_reader10':(D/'nana_ultimate_vehicle13_independent01/report.json','생성8셀 독립 재양자화·목표65층·공유·부분·비대상 근거.'),
 'nana_ultimate_special4_frozen10':(N/'ultimate_special_finish_repaint/packed_special_candidate_v1/FROZEN.json','Ultimate95/96/98/99 동결·RN35 이후통합.'),
 'nana_base_shot85_frozen10':(W/'root_nana_shot85/packed_shot01/FROZEN.json','새85/86 10층·RN36 이후통합.86 총20 중19가시+피부1가림.'),
 'nana_base_shot85_reader10':(D/'nana_base_shot2_independent01/report.json','기존 독립 원화/부분/정본총 근거.'),
 'nana_base_shot87_frozen10':(W/'root_nana_shot87/packed_settle01/FROZEN.json','새87/92 10층·RN37통합.부분92 베일1셀 소유 수정.'),
 'nana_base_shot87_reader10':(D/'nana_base_settle87_92_independent01/report.json','고유87/92 검수 보고서.옛138/139와 분리.'),
 'nana_base_shot87_visual10':(D/'nana_base_settle87_92_independent01/visual.json','87/92 실제4판 열람.새실기 아님.'),
 'nana_base_shot87_lock10':(D/'nana_base_settle87_92_independent01/READER_INPUT_LOCK.json','31입력·고유reader·보고서/4판 잠금과 별도재현.'),
 'settle_audit_recovery10':(D/'settle138_139_recovery01/restoration.json','옛138/139 감사경로 충돌을 세션원문·FROZEN report byte exact로 복원한 사고기록.자원/동결파일 불변.'),
 'nana_selection4_frozen10':(W/'nana_selection_sync34_03/FROZEN.json','RN 선택18..21 새승리/귀환 사본·RN35통합.19/20은 mirror Y0.'),
 'nana_selection4_reader10':(D/'nana_selection4_independent01/report.json','RN 원고유변환과 비대상 보존 독립근거.'),
 'nana_selection35_runtime10':(W/'runtime/rn35_selection_summary.json','새부팅 실제 선택전환128창·3판.참조별GPU 미검증.'),
 'nana_selection8_origins10':(W/'nana_selection8_origins.json','RN UI1..8→85..92는 원래 flip없음/dx0/dy0 exact.사본동기화는 후속.'),
 'shibuki_fire8_frozen10':(H/'prepared_standing_fire_base01/FROZEN.json','기본/포스85..92 동결·BR23 이후통합.18비대상참조 전체타일 역순열 exact.'),
 'shibuki_selection8_frozen10':(H/'prepared_selection_standing01/FROZEN.json','선택1..8 동결·BR24통합.전용49타일 안48패턴/flip공유.'),
 'shibuki_selection8_reader10':(D/'shibuki_selection8_independent01/report.json','선택8 원점·비대상·52GPU파트 독립근거.'),
 'shibuki_selection24_runtime10':(W/'runtime/br24_selection_summary.json','실제선택240창/232WebP·시간보정4판.참조별GPU 미검증.'),
 'protection43':(W/'protection_checkpoint43.json','루트 세션종료후80파일·카드5쌍 보존 기존근거.'),
 'shibuki_ult_recoil_candidate10':(H/'ultimate_standing_followthrough_common03/report.json','Ultimate90/91 등록·공통팔 외곽 후보.미패킹/미동결.'),
 'shibuki_ult_recoil_visual10':(D/'shibuki_ultimate_recoil90_boundary_visual01/review.json','중간비교2·부분1 실제열람.전체85..92 수용 아님.'),
 'nana_hover_relations10':(D/'nana_ultimate_hover_relations01/conclusions.json','호버5짝 하체층/engine mask15 및 별도추진효과15위상 원관계.'),
 'nana_hover_shot_candidate10':(N/'ultimate_hover_repaint/shot_joint_probe_v1/manifest.json','호버5사격 중간정합.실제 발사점과현재8열이일치한다는근거는아님.'),
 'nana_hover_muzzle10':(D/'nana_ultimate_hover_muzzle01/report.json','원US/RN36 실제총구표·일반탄 첫효과188px 읽기.'),
 'nana_hover_muzzle_visual10':(D/'nana_ultimate_hover_muzzle01/visual_findings.json','222/224 총끝의위·오른쪽 어긋남 및228 원점이총열안쪽인 정적발견.현실기결함으로확대하지않음.'),
}
for k,(p,why)in entries.items():
 if k=='shibuki_ult_recoil_candidate10'and not p.exists():p=p.parent/'manifest.json'
 ev(k,p,why)
album=ROOT/'out/sprite_style_unification_20261107/review_v28';am,ac=read(album/'manifest.json'),read(album/'browser_checks.json')
assert ac['passed'] and ac['html_sha256']==am['sha256']==sha(album/'ALL_SPRITES_CURRENT.html')
ev('album28',album/'manifest.json','BR23/RN36의28폼·4510표시·2699변경.현재BR24/RN37과구분.')
ev('album28_browser',album/'browser_checks.json','기존 픽셀·원표/루프 검사.실기아님.')
j['current_album']={'evidence':'album28','browser_evidence':'album28_browser','display_records':sum(q['references']for q in am['counts'].values()),'forms':sum(q['forms']for q in am['counts'].values()),'changed_display_records':len(am['changes']),'completion_percentage':None,'sources':am['sources'],'matches_latest_integration':False,'difference':'앨범28은BR23/RN36. BR24 선택8 및 RN37 기본87/92는이앨범에미포함.','new_visual_review_here':False}
assert(j['current_album']['display_records'],j['current_album']['forms'],j['current_album']['changed_display_records'])==(4510,28,2699)
for c in j['cells']:
 char,form,cat=c['character'],c['form'],c['category'];ult=form.startswith('ultimate')
 if char in('riko','rin'):continue
 keys=['rn37','nana_ledger23']if char=='nana'else['br24','shibuki_ledger32']
 if char=='nana'and cat=='special':
  c['states']=[state('preserve_reviewed'if ult else'integrated_new_art','기존세부 보존 판단'if ult else'새85/86 동결·RN36통합','85,86'),state('preserve_reviewed'if ult else'integrated_new_art','기존 대기연결 보존'if ult else'새87/92 동결·RN37통합','87,92'),state('integrated_derived_effect','새89 기반 원83픽셀 효과','88'),state('integrated_new_art','새 세부 동결·통합','89..91,95..99'),state('integrated_new_art','라이징7 동결·기존 대표실기','100..104,231,232'),state('review_before_decision','별도효과/세부 추가판단','208..212'),state('reachability_review_required','Nova/특수의몸체·효과·사용조건 분리','213..220'),state('registered_candidate'if ult else'reachability_review_required','새호버5몸체/5팔 등록·원발사점 정합 미완료'if ult else'호버사용조건·별도몸체 판단','221..230')]
  if ult:
   c['note']='Ultimate95/96/98/99는56a3 동결·RN35 이후통합.96/99의양폼X+1은신규제작정책이며옛after exact복원이아니다.호버10은새등록/용량진단단계;실제mask15에서layer5가하체이며불꽃은별도visual0x21이다.현재8열총끝을보존한222/224/228은원게임탄환원점과별도정합검토가필요하다.217/218/220머리수정을전신완료로세지않는다.'
   keys+=['nana_ultimate_special4_frozen10','nana_hover_relations10','nana_hover_shot_candidate10','nana_hover_muzzle10','nana_hover_muzzle_visual10']
  else:
   c['note']='85..92는새7자세와88효과가누적동결·RN37통합됐다.새85/86·87/92는정적/원MIPS까지이며각발동실기는아직이다.포스88/89/95..99 RN26 및90/91 RN28기존표본을새7전체또는기본형전수실기로확대하지않는다.87/92감사는고유경로·31입력잠금이며옛138/139보고서는동결해시exact로복원됐다.'
   keys+=['nana_base_shot85_frozen10','nana_base_shot85_reader10','nana_base_shot87_frozen10','nana_base_shot87_reader10','nana_base_shot87_visual10','nana_base_shot87_lock10','settle_audit_recovery10']
  c['art_review']='후보별 실제 재추출·부분판/원순서 열람과 동결 기록을 계승한다.현재호버중간판의시각검토는최종수용이아니다.'
 if char=='nana'and cat=='ride':
  c['states']=[state('integrated_new_art','새4몸체×두폼 및9Y별칭 동결·통합','162..174'),state('preserve_reviewed','기존 작은 탑승머리 용도별보존','184..203')]
  c['note']='기본/포스29f7은RN35,Ultimate9432는RN36부터통합.13참조를13고유원화로세지않는다.옛Ultimateafter의미세차이는새공통Y별칭정책으로정리했으며원작전층exact라고하지않는다.새체이서실제플레이는별도미검증.184..203은root72의기존용도별판단을계승한다.'
  keys+=['nana_base_vehicle_frozen10','nana_base_vehicle_reader10','nana_ultimate_vehicle_frozen10','nana_ultimate_vehicle_reader10']
 if char=='nana'and cat=='ui':
  c['note']='RN35이후선택18..21승리/귀환사본은a577으로통합;19/20은mirror Y0이며BR의Y+1을쓰지않는다.실제선택전환128창·3판에서큰단절은못찾았으나각참조GPU는미검증.선택1..8→85..92의RN원변환은flip없음/dx0/dy0이며새87/92까지의별도사본동기화는root후속이다.선택사본은전신참조집계에임의합산하지않는다.'
  c['separate_copy_states']=[{'status':'integrated','refs':'18..21','source':'207,156..158'},{'status':'source_origins_verified_sync_pending','refs':'1..8','source':'85..92','transform':'no flip; dx0,dy0 for all8'}]
  keys+=['nana_selection4_frozen10','nana_selection4_reader10','nana_selection35_runtime10','nana_selection8_origins10']
 if char=='nana'and not ult and cat=='ceremony':
  c['note']+=' 선택화면사본18..21은RN35부터새그림으로통합되고실제전환은별도선택근거로연결한다.이것을플레이승리/전송원동작전수실기로바꾸어세지않는다.'
  keys+=['nana_selection4_frozen10','nana_selection35_runtime10']
 if char=='shibuki'and cat=='special':
  if ult:
   c['states']=[state('registered_candidate','85/89새공통·90/91국소팔 등록중','85,89..91'),state('needs_redraw','후속별도원화/접점미완료','86,87,92'),state('effect_derivation_pending','새89 연동 원83픽셀 효과 미완료','88')]+c['states'][2:]
   c['note']='Ultimate85/89·90/91은새원화등록/팔외곽정합중이며90두셀공동외곽은정적후보다.86/87/92는후속원화미완료,88효과도최종동결아니다.기존95..97및Cyclone/Rising동결은별도보존한다.'
   keys+=['shibuki_ult_recoil_candidate10','shibuki_ult_recoil_visual10']
  else:
   c['states'][0]=state('integrated_new_art','새7몸체14원화 동결·BR23통합','85..87,89..92');c['states'][1]=state('integrated_derived_effect','새89+원83픽셀 효과 동결·통합','88')
   c['note']='4fe717새85..92는고정은행내무손실패킹·동결·BR23통합완료.용량을위해18비대상참조타일순서를바꿨으나역순열전체256nibble/5층exact이고508원directory검사를통과했다.기존1410B부족은해결된과거진단이다.선택1..8은BR24별도통합·실제화면관측,플레이85..92의발동전수실기는별도다.'
   keys+=['shibuki_fire8_frozen10','shibuki_selection8_frozen10','shibuki_selection24_runtime10']
  c['art_review']='기본85..92최종판동결수용과Ultimate중간정합시각검토를분리한다.한폼의수용을다른폼으로확대하지않는다.'
 if char=='shibuki'and cat=='ui':
  c['note']='BR24선택1..8은새기본85..92와BR원변환dy[-1,0,0,0,0,-1,-2,0]exact로통합됐다.전용49타일내48패턴/반전공유·52파트이며17비대상X참조/Zero/초상화보존.실제15초240창/232WebP의시간보정4판을root가열람했으나참조별GPU는미검증.이BR변환을RN에복사하지않는다.'
  c['separate_copy_states']=[{'status':'integrated_visual_runtime_observed','refs':'1..8','source':'85..92','individual_runtime_GPU_verified':False}]
  keys+=['shibuki_selection8_frozen10','shibuki_selection8_reader10','shibuki_selection24_runtime10']
 c['evidence']=list(dict.fromkeys(c['evidence']+keys))
j['ledger_units']={'nana_scope23':{'evidence':'nana_ledger23','reference_form_pairs':632,'new_art_reference_form_pairs':556,'derived_effect_pairs':64,'mirrored_pairs':12,'later_root_additions':[{'refs':[85,86],'forms':['base','fourth'],'evidence':'nana_base_shot85_frozen10'},{'refs':[87,92],'forms':['base','fourth'],'evidence':'nana_base_shot87_frozen10'}]},'shibuki_scope32':{'evidence':'shibuki_ledger32','count_kind':'의상별표시/동형키 상태분류이며 원화장수 아님'},'counts_are_not_completion_or_quality_scores':True,'combined_artwork_count':None}
j['gap_analysis']=[
 {'owner':'root','scope':'Nana 선택1..8 사본','finding':'RN37새85..92와별도사본동기화미완료.원RN변환8개모두dx0/dy0/무반전.','acceptance_needed':'대상소유타일/원점·부분조립·비대상UI/Rin/HQ보존,독립읽기·실제선택검토후통합.','evidence':['rn37','nana_selection8_origins10']},
 {'owner':'overhaul_audio','scope':'Nana Ultimate호버221..230','finding':'새5몸체/5사격등록·용량진단.기존8열총끝과실제원점표차이확인.','acceptance_needed':'222/224/228등총/손·팔을원발사점과국소정합.추진발15위상·층5하체·mask15·짝공유/부분/원순서/독립을확인.원효과/로직변경금지.','evidence':['nana_hover_relations10','nana_hover_muzzle10','nana_hover_muzzle_visual10']},
 {'owner':'overhaul_ui','scope':'Shibuki Ultimate85..92','finding':'85/89·90/91등록중,86/87/92후속.기본/포스8은이미통합.','acceptance_needed':'남은원화·양폼손/총·부분소유·88원효과·원순서/비대상·저장검사와최종미술판정.','evidence':['shibuki_ledger32','shibuki_ult_recoil_candidate10','shibuki_ult_recoil_visual10']},
 {'owner':'overhaul_audio','scope':'Nana Ultimate사다리보류7','finding':'148/149/150/151/152/153/155는기존그림미완료.허용7동결과별도.','acceptance_needed':'거부된의상교정을우회/재시도하지않고보류유지.별도허용범위가있을때만후속판단.','evidence':['nana_ultimate_ladder7_frozen09','nana_ledger23']},
 {'owner':'overhaul_ui','scope':'Shibuki Ultimate135','finding':'등장8동결에도135거부편집은부모보존미완료.','acceptance_needed':'해당보류를다른동결/통합수로덮지않는다.','evidence':['shibuki_ledger32']},
 {'owner':'overhaul_ui / overhaul_audio','scope':'Shibuki차량162..174·두X Nova/기타특수','finding':'Shibuki차량/호버/Nova와Nana213..220/208..212는새전체수용근거없음.기존작은차량머리조건부·별도효과를구분.','acceptance_needed':'실제사용/공유/몸체·효과를분류하고용도별보존또는새원화필요를판정.부분머리변경만으로전신완료표시금지.','evidence':['shibuki_ledger32','nana_ledger23']},
 {'owner':'root','scope':'대표실기·미관측 동작','finding':'저체력발동실패유지.새승리/귀환·차량·Ult90/91·새87/92의실기는정적과분리.등장RN30실제mask0,선택RN35/BR24는별도화면.','acceptance_needed':'해당동작/폼과새자원해시가실제관측된범위만추가하며전모션전팔레트완료로확대하지않음.','evidence':['nana_lowhp22_runtime_failed','nana_arrival30_runtime','nana_selection35_runtime10','shibuki_selection24_runtime10']},
 {'owner':'root','scope':'Riko/Rin 및별도HQ/대사/잔기','finding':'기존전체미술·대표실기/끝점보존근거유지.추가확정재작화후보없음.','acceptance_needed':'새우려없는통과검사반복불필요.큰일러스트/작은아이콘을45px전신과일괄동일화하지않고잔여실기한계유지.','evidence':['riko_views','rin_views','zero_endpoint_views','x_endpoint_views']},
]
j['next_work']=[{'owner':g['owner'],'scope':g['scope'],'stage':g['finding'],'evidence':g['evidence']}for g in j['gap_analysis']]
j['new_runtime_scope']=[{'evidence':'nana_selection35_runtime10','kind':'선택전환','captured_frames':128,'root_viewed_boards':3,'individual_ref_GPU_verified':False},{'evidence':'shibuki_selection24_runtime10','kind':'선택자동연출','captured_frames':240,'encoded_WebP_frames':232,'root_viewed_boards':4,'individual_ref_GPU_verified':False}]
j['coverage_limits']=[s for s in old['coverage_limits']if not s.startswith('선택 X 사본은 현재 RN34') and not s.startswith('표본 수/변경 표시2592')]
j['coverage_limits']+=['앨범28의2699변경/4510표시/28폼은BR23/RN36시점이며최신BR24/RN37과다르다.품질완료율·고유원화수아님.','RN35/BR24선택화면실기에서새사본이보였지만모든참조별GPU/모든효과가림을검증하지않았다.','호버총구차이는원코드/원타일의정적발견이며실제게임결함·최종새원화수용으로확대하지않는다.','87/92새감사는고유폴더로잠갔고경로충돌로덮어쓴옛138/139보고서는원동결해시exact로복원했다.사고를기록에서숨기거나옛FROZEN을수정하지않았다.']
j['snapshot_summary']='BR24/RN37통합·기존원MIPS/전섹터근거와별도선택실기를연결했다.앨범28은BR23/RN36이며차이를명시한다.나나차량양자원·특수4·기본사격85/86/87/92는동결통합,시부키기본85..92/선택8도통합했다.나나호버총구정합·선택1..8,시부키Ultimate85..92/차량·호버,보류사다리7/135및미관측실기는남아있다.'
j['completed_milestones_since_previous']=[{'scope':'BR23 기본85..92/BR24선택8 통합','evidence':['br24','shibuki_fire8_frozen10','shibuki_selection8_frozen10'],'all_runtime_verified':False},{'scope':'RN35~37 차량양자원/특수4/선택4/85·86·87·92 누적통합','evidence':['rn37'],'all_runtime_verified':False},{'scope':'BR24/RN35 선택 실제화면 관측','evidence':['shibuki_selection24_runtime10','nana_selection35_runtime10'],'individual_ref_GPU_verified':False}]
for key in('all_art_complete','all_gameplay_verified','user_final_accepted','game_or_art_modified'):j[key]=False
assert[c for c in old['cells']if c['character']in('riko','rin')]==[c for c in j['cells']if c['character']in('riko','rin')]
for k,v in old['evidence'].items():assert j['evidence'][k]==v
def refs(text):
 out=[]
 for r in text.replace(' ','').split(','):
  if '..'in r:a,b=map(int,r.split('..'));out+=list(range(a,b+1))
  elif r:out.append(int(r))
 return out
checks=[]
for char in('shibuki','nana'):
 for form in('base','fourth','ultimate_before','ultimate_after'):
  rr=[r for c in j['cells']if(c['character'],c['form'])==(char,form)for s in c['states']for r in refs(s['refs'])];assert len(rr)==len(set(rr))==228 and set(rr)==set(range(237))-{105,*range(175,183)},(char,form)
  checks.append({'character':char,'form':form,'classified_unique_refs':228,'missing':[],'duplicate':[],'classification_is_not_acceptance':True})
for c in j['cells']:
 for k in c['evidence']:assert k in j['evidence']
for k,q in new.items():assert sha(ROOT/q['path'])==q['sha256'],k
O.mkdir(exist_ok=False);(O/'coverage.json').write_text(json.dumps(j,ensure_ascii=False,indent=2)+'\n','utf8')
esc=html.escape
def link(k):return '<a href="'+esc(os.path.relpath(ROOT/j['evidence'][k]['path'],O).replace('\\','/'))+'">'+esc(k)+'</a>'
page=['<!doctype html><html lang="ko"><meta charset="utf-8"><title>전체 범위10 · BR24/RN37</title><style>body{font:15px system-ui;background:#14202b;color:#edf3fa;margin:24px}a{color:#9dceff}table{border-collapse:collapse;width:100%;margin:20px 0}td,th{border:1px solid #526577;padding:10px;vertical-align:top;text-align:left}small{color:#b8c8d6}</style><h1>네 캐릭터 범위10</h1><p>BR24/RN37 · 12전신폼 × 12범주. 표시 수는 고유원화나 품질완료율이 아닙니다.</p><p>'+esc(j['snapshot_summary'])+'</p><p><a href="coverage.json">전체 JSON</a> · <a href="../full_scope_matrix09/COVERAGE.html">이전09</a></p><p>현재 근거: '+' · '.join(link(k)for k in('br24','rn37','album28','album28_browser','protection43'))+'</p><h2>남은 범위와 수용 조건</h2><table><tr><th>담당/범위</th><th>현재 판단</th><th>남은 조건</th></tr>']
for g in j['gap_analysis']:page.append('<tr><td>'+esc(g['owner']+' · '+g['scope'])+'</td><td>'+esc(g['finding'])+'</td><td>'+esc(g['acceptance_needed'])+'<details><summary>근거</summary>'+ '<br>'.join(link(k)for k in g['evidence'])+'</details></td></tr>')
page.append('</table>')
for char,name in{'shibuki':'시부키','nana':'나나','riko':'리코','rin':'린'}.items():
 for form,title in j['forms'].items():
  cells=[c for c in j['cells']if(c['character'],c['form'])==(char,form)]
  if not cells:continue
  page.append('<h2>'+name+' · '+esc(title)+'</h2><table><tr><th>범주</th><th>상태/참조</th><th>판단·잔여</th><th>실제열람·근거</th></tr>')
  for c in cells:page.append('<tr><td>'+esc(j['categories'][c['category']])+'</td><td>'+('<br>'.join(esc(s['label']+': '+s['refs'])for s in c['states'])or'별도사본')+'</td><td>'+esc(c['note'])+'</td><td><small>'+esc(c['art_review'])+'</small><details><summary>근거</summary>'+'<br>'.join(link(k)for k in c['evidence'])+'</details></td></tr>')
  page.append('</table>')
page.append('<h2>한계</h2><ul>'+''.join('<li>'+esc(s)+'</li>'for s in j['coverage_limits'])+'</ul></html>');(O/'COVERAGE.html').write_text('\n'.join(page),'utf8')
links=re.findall(r'href="([^"]+)"',(O/'COVERAGE.html').read_text('utf8'));assert all((O/html.unescape(x)).resolve().is_file()for x in links)
v={'passed':True,'cells':len(j['cells']),'evidence_files':len(j['evidence']),'new_bound_inputs':len(new),'local_links':len(links),'broken_links':0,'x_reference_classification':checks,'zero_cells_unchanged':True,'prior_snapshot_unmodified_sha256':sha(P),'new_gameplay_or_native_tests_performed':False,'new_all_sheet_visual_review_performed':False,'source_art_or_game_modified':False,'all_art_complete':False,'album_matches_current_integration':False,'album_difference':j['current_album']['difference']}
(O/'verification.json').write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n','utf8')
print(json.dumps({'coverage_sha256':sha(O/'coverage.json'),'html_sha256':sha(O/'COVERAGE.html'),'verification_sha256':sha(O/'verification.json'),'cells':len(j['cells']),'evidence_files':len(j['evidence'])}))
