"""BR25/RN39·앨범30 및 기존 실기/독립 근거를 새 불변 스냅샷으로 결합."""
from pathlib import Path
import copy,hashlib,html,json,os,re
ROOT=Path(__file__).resolve().parents[3];D=Path(__file__).parent;W=D.parent;N=W/'nana_audit';H=W/'shibuki_audit'
P=D/'full_scope_matrix10/coverage.json';O=D/'full_scope_matrix11';assert not O.exists(),O
read=lambda p:json.loads(p.read_text('utf8'));sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();rel=lambda p:p.relative_to(ROOT).as_posix()
old=read(P);j=copy.deepcopy(old);new={};j['previous_snapshot']={'path':rel(P),'sha256':sha(P)}
def ev(k,p,why):
 assert p.is_file()and k not in j['evidence'],(k,p)
 q={'path':rel(p),'sha256':sha(p),'purpose':why};j['evidence'][k]=q;new[k]=q
def state(status,label,refs):return {'status':status,'label':label,'refs':refs}
j['prior_integration']=copy.deepcopy(old['integration']);j['integration']={}
for k,project,v in [('br25','ver_buki_riko',25),('rn39','ver_rin_nana',39)]:
 pp=W/f'staging_{k[:2]}_v{v}.json';np=W/f'staging_{k[:2]}_v{v}_native_checks.json';mp=ROOT/f'out/{project}/sprite_style_unification_20261107_v{v}/manifest.json'
 plan,native,m=map(read,(pp,np,mp));assert native['passed']and m['disc_readback_verified']and m['all_disc_sectors_compared']==251793 and m['gameplay_timing_code_palettes_audio_preserved']
 for name,r in plan['resources'].items():assert r['after']==m['resources'][name]['after']==sha(ROOT/r['path'])
 for q in plan['candidate_freeze_bindings'].values():assert sha(ROOT/q['path'])==q['sha256']
 for suffix,p,why in [('',pp,'통합 자원/동결 해시 결속'),('_native',np,'기존 원MIPS/GPU 결과. 이번 장부 작성에서 재실행하지 않음'),('_disc',mp,'기존 전섹터·재추출 검증. BIN 재작성 없음')]:ev(k+suffix,p,why)
 j['integration'][k]={'output':plan['output'],'bin_sha256':m['modified_bin']['sha256'],'resources':plan['resources'],'preserve_x_selection':plan['preserve_x_selection']}
assert j['integration']['br25']['bin_sha256']=='21696e9bae002ef6c9f95fed683e7cd531fd6cdfc6c0fdae97529c3b28a09636'
assert j['integration']['rn39']['bin_sha256']=='8eb84afaa7c201dfcaee8e5cbf4c2fef152d423b10b501e8238362f9b5cca5b2'
entries={
 'nana_ledger25':(N/'scope_summary_v25/manifest.json','호버10 동결 포함 652참조×폼 장부. 그 장부의 PL00는29f7이므로 후속 root85/86·87/92 8표시는 별도 연결.'),
 'shibuki_ledger34':(H/'fullform_ledger34.json','Ultimate85..92 동결과 당시 미패킹 체이서 후보를 분리한 장부. 최신 통합은BR25 별도 근거가 우선.'),
 'shibuki_unique34':(H/'unique_art_keys34.json','771개의 의상별 동형표시 분류. 고유 생성원화 수나 품질 완료율 아님.'),
 'shibuki_ult_fire8_frozen11':(H/'prepared_standing_fire_ultimate01/FROZEN.json','Ultimate85..92 동결·BR25 통합. 새7자세×2의상과88효과 파생.'),
 'shibuki_ult_fire8_reader11':(D/'shibuki_ultimate_fire8_independent01/report.json','신규40층/원83효과/부분/비대상 독립 근거.'),
 'shibuki_br25_shot_runtime11':(W/'runtime/br25_shot_summary.json','획득후Ultimate 양방향 일반/차지 실제224창·9판. 참조별RAM/GPU 미추적.'),
 'nana_rn37_shot_runtime11':(W/'runtime/rn37_shot_summary.json','포스 양방향 일반/차지 실제224창·9판. 기본/부분 및 참조별RAM/GPU와 구분.'),
 'nana_selection8_frozen11':(W/'root_nana_selection8/prepared01/FROZEN.json','RN선택1..8 identity 사본 동결. 기존39전용+확인된 미소비14타일 사용, 공유5 보호.'),
 'nana_selection8_reader11':(D/'nana_selection8_spares_independent01/report.json','8대상과72비대상UI/53변경타일·58파트 및 원점 독립 검사.'),
 'nana_selection8_visual11':(D/'nana_selection8_spares_independent01/visual_review.json','새사본/게임그림 비교4판 실제 열람. 실기는 별도.'),
 'nana_selection8_capacity_native11':(D/'nana_selection8_capacity01/native_initializers.json','원로더·14선택초기화와Xtail 소비 조건의 기존 실행 근거.'),
 'nana_selection39_runtime11':(W/'runtime/rn39_selection_summary.json','새부팅 선택240창/237WebP, 시간 대응4판 실제 열람. 각참조GPU는 미검증.'),
 'nana_hover_frozen11':(N/'ultimate_hover_repaint/packed_hover_candidate_v1/FROZEN.json','호버221..230 동결 및 RN39 통합. 실제engine mask15 공통몸5+사격팔5.'),
 'nana_hover_reader11':(D/'nana_ultimate_hover10_independent01/report.json','50층/320부분/원15jet·7탄환 및 정본총100셀 독립. 생성10셀 재양자화는 제작자 범위.'),
 'nana_hover_visual11':(D/'nana_ultimate_hover10_independent01/visual_review.json','최종팔/목/원추진발 정적14판 직접 열람.'),
 'nana_nova_relations11':(D/'nana_ultimate_nova_relations01/report.json','213/214·215/216 역사정책/원US 차이,219옛683몸 실루엣,218/220역사처리효과 재구성.'),
 'nana_nova_conclusions11':(D/'nana_ultimate_nova_relations01/conclusions.json','현재몸727과 기존효과 가림68/77셀 및 새219 필요 판단. 실제 게임 결함으로 확대하지 않음.'),
 'nana_nova215_arm_visual11':(D/'nana_ultimate_nova215_arm_visual01.json','현215 직접 역사 원화의 머리 뒤 주먹/커프 확인. 새원화의 낮춘 팔은 국소 수정 준비.'),
 'nana_nova_common_candidate11':(N/'ultimate_nova_repaint/common_probe_v5/manifest.json','215 높은 팔을 국소 새원화로 복원한 최신 공통 후보. v1~3 낮춘 팔은 미채택이며 v5도 미동결.'),
 'nana_nova_common_visual_source11':(N/'ultimate_nova_repaint/common_probe_v5/comparison.png','이번 실제 정적 열람: 높은 주먹/어깨와 맨팔 경계. 패킹/효과/실기 판정 아님.'),
 'shibuki_chaser_candidate11':(H/'prepared_chaser_base01/proposal.json','기본/포스 체이서4키×2→13참조 준비본3e11. BR25에는 미통합.'),
 'shibuki_chaser_reader11':(D/'shibuki_chaser13_independent01/report.json','생성8셀 직접 재양자화→65층/9Y별칭·16저장순열 독립 통과.'),
 'shibuki_chaser_visual11':(D/'shibuki_chaser13_independent01/visual_review.json','비교4/부분4/Y별칭4 실제12판. 실제 차량 접점 미검증.'),
 'shibuki_chaser_directory11':(D/'shibuki_chaser13_directory_native01/report.json','전체508 원loader→directory→객체+38/+3c→decode/upload 1016회. 게임/CD/GPU실기 아님.'),
 'shibuki_chaser_sequence11':(D/'shibuki_chaser_sequences01/report.json','원표65..76·duration/차량상태 caller 및 알려진UI사본 목록 읽기.'),
 'shibuki_chaser_ultimate_candidate11':(H/'chaser_ultimate_contacts01/report.json','Ultimate162/166 원화·접점 등록 후보.170/174 및파생은 후속,미동결.'),
 'protection47':(W/'protection_checkpoint47.json','시험 종료후80파일·5카드쌍 보존 기존 근거. 새 검사 아님.'),
}
for k,(p,why)in entries.items():ev(k,p,why)
hoverp=W/'runtime/nana_hover39_summary.json'
# 루트가 실제 열람을 마감한 요약만 연결한다. 임시 캡처수로 실기를 완료 처리하지 않는다.
if not hoverp.exists():
 alternatives=[W/'runtime/rn39_hover_summary.json',W/'runtime/nana_ultimate_hover39_summary.json']
 hoverp=next((p for p in alternatives if p.exists()),hoverp)
assert hoverp.exists(),'루트 호버 실제 열람 요약 대기'
ev('nana_hover39_runtime11',hoverp,'RN39 호버 실제 녹화/직접 열람. 요약의 한계와 참조별검증 범위를 그대로 분리.')
hr=read(hoverp)
chaser_frozen=(H/'prepared_chaser_base01/FROZEN.json').exists()
if chaser_frozen:
 ev('shibuki_chaser_frozen11',H/'prepared_chaser_base01/FROZEN.json','체이서13 후속 동결. 이 스냅샷의BR25에는 미통합이며 실기 아님.')
 cf=read(H/'prepared_chaser_base01/FROZEN.json');assert cf['frozen']and cf['candidate_sha256']=='3e11b7e6f6c58e6e175ba8a53278a8329440c160096bf89abdb9df334c3ef52d'
album=ROOT/'out/sprite_style_unification_20261107/review_v30';am,ac=read(album/'manifest.json'),read(album/'browser_checks.json')
assert ac['passed']and ac['html_sha256']==am['sha256']==sha(album/'ALL_SPRITES_CURRENT.html')
for project,k in(('ver_buki_riko','br25'),('ver_rin_nana','rn39')):assert am['sources'][project]['sha256']==j['integration'][k]['bin_sha256']
ev('album30',album/'manifest.json','BR25/RN39의4510표시/28폼/2757변경. 고유원화·완료율이 아님.')
ev('album30_browser',album/'browser_checks.json','기존2757 픽셀·4루프 검사. 새실행/실제 게임 검증 아님.')
j['current_album']={'evidence':'album30','browser_evidence':'album30_browser','display_records':sum(q['references']for q in am['counts'].values()),'forms':sum(q['forms']for q in am['counts'].values()),'changed_display_records':len(am['changes']),'changed_by_character':{k:v['new_changed_references']for k,v in am['counts'].items()},'completion_percentage':None,'sources':am['sources'],'matches_latest_integration':True,'difference':None,'new_visual_review_here':False}
assert(j['current_album']['display_records'],j['current_album']['forms'],j['current_album']['changed_display_records'])==(4510,28,2757)
for c in j['cells']:
 char,form,cat=c['character'],c['form'],c['category'];ult=form.startswith('ultimate')
 if char in('riko','rin'):continue
 keys=['rn39','nana_ledger25']if char=='nana'else['br25','shibuki_ledger34']
 if char=='nana'and cat=='special':
  c['states']=[state('preserve_reviewed'if ult else'integrated_new_art','기존 수용 세부 보존'if ult else'새85/86 동결·통합','85,86'),state('preserve_reviewed'if ult else'integrated_new_art','기존 대기 연결 보존'if ult else'새87/92 동결·통합','87,92'),state('integrated_derived_effect','새89 기반 원83픽셀 효과','88'),state('integrated_new_art','새 세부 동결·통합','89..91,95..99'),state('integrated_new_art','라이징7 동결·대표실기 별도','100..104,231,232'),state('review_before_decision','별도 효과/세부 추가 판단','208..212')]
  if ult:
   c['states']+=[state('registered_candidate','새213/215·215 높은팔 국소 수정 공통v5 후보','213,215'),state('derived_rework_pending','기존 동형 정책/원US 차이를 분리해 후속 파생 검토','214,216'),state('body_effect_rework_pending','몸·역사처리효과·실루엣 동기화 미완료','217..220'),state('integrated_new_art','호버5몸체+5사격팔 동결·RN39통합','221..230')]
   c['note']='호버10은 실제renderer mask15의 상체0/하체5이며 두 의상 슬롯에 같은 그림을 표시한다. 20개의 독립 원화로 세지 않는다. 새5팔 총은 원발사점X+1의 정본20셀로 정합했고 옛8열 보존안은 폐기됐다. 원15jet/7탄환은 보존. RN39 실기는 별도 요약의 관측/열람 범위만 인정한다. Nova213/215 공통v5는 미동결;215 역사 원화의 머리 뒤 주먹을 낮춘 초기안은 미채택이고 새 높은팔 국소 후보로 정리됐다. 높은손 원좌표 exact라는 뜻은 아니다.219는 옛683몸 실루엣으로 현727몸과 불일치하며218/220도 역사처리효과의68/77가림을 검토해야 한다.'
   keys+=['nana_hover_frozen11','nana_hover_reader11','nana_hover_visual11','nana_hover39_runtime11','nana_nova_relations11','nana_nova_conclusions11','nana_nova215_arm_visual11','nana_nova_common_candidate11','nana_nova_common_visual_source11']
  else:
   c['states']+=[state('reachability_review_required','아머 능력/별도 몸·효과 사용 조건 분리','213..230')]
   c['note']='기본/포스85..92 새7자세+88효과가 통합됐다. RN37 포스 양방향 일반/차지224창9판 실제 열람은 추가 확정 단절 없음이며 참조별RAM/GPU 추적은 하지 않았다. 기본형·부분조합 전수실기로 확대하지 않는다.213..230은 같은 번호의Ultimate 사용성을 일반폼에 그대로 적용하지 않고 원래아머조건을 분리한다.'
   keys+=['nana_rn37_shot_runtime11']
  c['art_review']='후보별 실제 재추출/부분/원순서 수용 근거를 계승하며 신규 호버 정적14판 및 루트실기는 별도 연결한다. 미동결 Nova를 전체특수 완료로 세지 않는다.'
 if char=='nana'and cat=='ui':
  c['note']='RN38부터 선택1..8이 새85..92와 원RN identity(dx0/dy0/무반전)로 통합됐다. 기존39전용과 원코드/전체소비로 확인한미소비28개 중14개를 써53타일을 변경했으며 공유5타일·72비대상UI·은행/길이는 보존했다. RN39 실제240창/237WebP·시간보정4판에서 자동차지/반동/복귀를 보았으나 참조별GPU는 미검증.선택18..21은RN35부터 기존 통합. UI사본은 전신표시집계에 임의추가하지 않는다.'
  c['separate_copy_states']=[{'status':'integrated','refs':'18..21','source':'207,156..158'},{'status':'integrated_visual_runtime_observed','refs':'1..8','source':'85..92','transform':'no flip; dx0,dy0 for all8','individual_runtime_GPU_verified':False}]
  keys+=['nana_selection8_frozen11','nana_selection8_reader11','nana_selection8_visual11','nana_selection8_capacity_native11','nana_selection39_runtime11']
 if char=='shibuki'and cat=='special':
  c['states']=[state('integrated_new_art','새7자세×두의상 동결·통합','85..87,89..92'),state('integrated_derived_effect','새89 X−1+원83픽셀 효과 동결·통합','88'),state('integrated_new_art','95/96/97 새세부 통합','95..97'),state('integrated_new_art','Cyclone/Rising 새원화 통합','98..104,231,232')]
  if ult:
   c['states']+=[state('effect_only','독립 효과와 몸체 의존 분리','208..212,219'),state('body_effect_rework_pending','Nova/호버 몸체·효과 추가 세부 미완료','213..218,220..230')]
   c['note']='Ultimate85..92 1f271a는 동결·BR25통합됐다.88 원US83효과와 새89 X−1,87/92별도새포즈 및90팔꿈치2셀 공동외곽을 분리 기록했다.획득후Ultimate 일반/차지 양방향224창9판 실제 열람에서 추가 확정 단절은 못찾았으나 참조별RAM/GPU 추적은 미실행. Nova218은 몸+효과,219는효과라 이전 범주표의218 효과-only 표현을 보완한다.213..230 전체상세는 미완료이며217..230의renderer mask15를 별도 적용한다.'
   keys+=['shibuki_ult_fire8_frozen11','shibuki_ult_fire8_reader11','shibuki_br25_shot_runtime11']
  else:
   c['states']+=[state('effect_only','별도 효과/몸체 의존 분리','208..212,218,219'),state('reachability_review_required','호버/Nova 자세와 아머 사용조건 잔여','213..217,220..230')]
   c['note']='기본/포스85..92와선택1..8은 기존동결·통합.이번BR25 실제사격은획득후Ultimate이므로 기본/포스 전수실기 근거로 옮기지 않는다.18저장순열의 전체타일/부분exact와 원directory 근거를 계승한다.후속체이서 후보의16저장순열도 별도이며 아직이BIN에 없다.'
  c['art_review']='전폼85..92 동결별 정적 열람을 연결한다. 획득후Ultimate 실제사격과 기본/부분폼 정적검사를 구분한다.'
 if char=='shibuki'and cat=='ride':
  if not ult:
   c['states']=[state('frozen_pending_integration'if chaser_frozen else'prepared_independent_pass','새4키×두폼·9Y파생 동결/후속통합대기'if chaser_frozen else'새4키×두폼·9Y파생 준비·독립통과','162..174'),state('vehicle_conditional','작은 차량 머리·장식 조건부 검토','184..203')]
   c['note']='새3e11 체이서13은 BR25에는 미통합이다. 생성8고정셀 직접 재양자화,65층·416부분과 원9Y별칭,기존16참조256전체타일 역순열/512부분이 독립통과.원loader→directory→객체주소→decode/upload508참조는 게임/CD/실제GPU를 뜻하지 않는다. 실제 손잡이/발판 접점은 미관측. 기존table65..76 duration96은 마지막상태 유지이며 모션전체96초가 아니다.'
   keys+=['shibuki_chaser_candidate11','shibuki_chaser_reader11','shibuki_chaser_visual11','shibuki_chaser_directory11','shibuki_chaser_sequence11']
   if chaser_frozen:keys+=['shibuki_chaser_frozen11']
  else:
   c['states']=[state('registered_candidate','162/166 새원화·접점 초기후보','162,166'),state('derived_rework_pending','새공통몸의 원Y별칭·의상 정책 후속','163..165,167..169'),state('needs_redraw','170/174 새원화·의상과파생 준비','170..174'),state('vehicle_conditional','작은 차량 머리·장식 조건부 검토','184..203')]
   c['note']='기본/포스 새체이서 수용을 Ultimate에 확대하지 않는다. Ultimate162/166은원화·접점초기후보이고170/174는입력준비다. 현재Ultimate after의9파생은 원US/base의Y별칭과exact가 아니므로 새몸체 공통정책/원역사를 분리해 제작해야 한다.184..203은머리전용이며 전신높이로 늘리지 않는다.'
   keys+=['shibuki_chaser_ultimate_candidate11']
 if char=='nana'and cat=='ride':
  c['note']='기본/포스29f7과Ultimate9432 차량13은누적통합.새4몸체×두폼+9Y별칭이며13고유원화로세지 않는다. 실기없이 원MIPS/독립/정적이 통과한 범위이며RN39호버능력실기를 체이서 차량실기로 재분류하지 않는다.184..203은기존용도별보존판단을계승한다.'
 c['evidence']=list(dict.fromkeys(c['evidence']+keys))
nl=read(N/'scope_summary_v25/manifest.json');ul=read(H/'unique_art_keys34.json')
j['ledger_units']={'nana_scope25':{'evidence':'nana_ledger25','reference_form_pairs':nl['all_frozen_reference_form_pairs'],'new_art_reference_form_pairs':nl['frozen_full_new_art_reference_form_pairs'],'derived_effect_pairs':nl['frozen_derived_effect_reference_form_pairs'],'mirrored_pairs':nl['frozen_mirrored_reference_form_pairs'],'later_root_additions':[{'refs':[85,86],'forms':['base','fourth'],'evidence':'nana_base_shot85_frozen10'},{'refs':[87,92],'forms':['base','fourth'],'evidence':'nana_base_shot87_frozen10'}],'these_later_8_are_not_part_of_the_652':True},'shibuki_scope34':{'evidence':'shibuki_ledger34','unique_evidence':'shibuki_unique34','count_kind':'의상별RGBA 동형표시 상태분류이며 고유 생성원화 수가 아님','frozen_display_keys':598,'pending_keys':87,'preserved_keys':24,'effect_keys':56,'vehicle_head_conditional_keys':4,'mixed_keys':2,'all_keys':771,'chaser_followup_not_in_counts':True},'counts_are_not_completion_or_quality_scores':True,'combined_artwork_count':None}
assert nl['all_frozen_reference_form_pairs']==652 and nl['frozen_full_new_art_reference_form_pairs']==576
j['gap_analysis']=[
 {'owner':'overhaul_ui / root','scope':'Shibuki 기본/포스 체이서13','finding':('새3e11은최종미술·독립·원MIPS 결속동결. 'if chaser_frozen else'새3e11 후보 원화·부분·순열/508원directory 독립통과. ')+'이스냅샷 BR25에는미통합.','acceptance_needed':'후속통합 및 실제 기체손잡이·발판/각동작 별도실기. 기존16순열은화면불변.','evidence':['shibuki_chaser_candidate11','shibuki_chaser_reader11','shibuki_chaser_visual11','shibuki_chaser_directory11']+(['shibuki_chaser_frozen11']if chaser_frozen else[])},
 {'owner':'overhaul_ui','scope':'Shibuki Ultimate체이서·Nova/호버','finding':'162/166 접점등록후보,170/174 입력준비.213..230 상세도미완료.다른폼이나부분머리 수정만으로완료할수없음.','acceptance_needed':'몸·효과·engine mask15와 원별칭/역사정책 분리, 원손발/발사점/효과보존 및 새원화·부분·독립·최종미술 검토.','evidence':['shibuki_ledger34','shibuki_chaser_sequence11','shibuki_chaser_ultimate_candidate11']},
 {'owner':'overhaul_audio','scope':'Nana Ultimate Nova213..220','finding':'213/215 공통v5 등록후보.215 낮춘팔 초기안은 미채택,높은팔 새국소 후보로 복원.214/216 역사별칭/원US차이와217..220 연동은 남음.','acceptance_needed':'새몸/팔정합과219실루엣 동기화.218/220은처리된역사효과이므로 새몸가림검토.원효과전체불변/원US동일복원이라는무근거주장금지.','evidence':['nana_ledger25','nana_nova_relations11','nana_nova_conclusions11','nana_nova215_arm_visual11','nana_nova_common_candidate11']},
 {'owner':'overhaul_audio','scope':'Nana Ultimate 사다리 보류7','finding':'148/149/150/151/152/153/155는부모그림으로미완료.허용7과분리.','acceptance_needed':'거부된의상교정 우회/재시도 없이보류.별도허용범위가있을때만후속판단.','evidence':['nana_ultimate_ladder7_frozen09','nana_ledger25']},
 {'owner':'overhaul_ui','scope':'Shibuki Ultimate135 및 탑승머리','finding':'135거부편집은부모보존미완료.184..203작은머리장식조건부검토도별도.','acceptance_needed':'다른등장/체이서동결수로덮지않고실제용도별판단.기체나전신을임의추가하지않음.','evidence':['shibuki_ledger34']},
 {'owner':'root / overhaul_audio','scope':'Nana기본 아머능력·208..212·보존후보','finding':'원래아머별도달/별도효과와미재작화목록을품질미달로동일시하지않음.','acceptance_needed':'기존원표/렌더러/미술근거에서실제로빠진몸체가있는지만분류.목록에있다는이유로기존양호디자인을새로만들지않음.','evidence':['nana_ledger25','nana_nova_relations11']},
 {'owner':'root','scope':'대표실기와 미관측범위','finding':'RN37포스사격/BR25획득후Ultimate사격/RN39선택 및 호버는 각기별도관측.저체력발동실패·새승리/귀환/차량실기한계는유지.','acceptance_needed':'영상열람과참조별RAM/GPU·전폼/부분조합을구분.등장RN30의mask0조건을mask15나모든등장폼으로확대하지않음.','evidence':['nana_rn37_shot_runtime11','shibuki_br25_shot_runtime11','nana_selection39_runtime11','nana_hover39_runtime11','nana_lowhp22_runtime_failed','nana_arrival30_runtime']},
 {'owner':'root','scope':'Riko/Rin 및 별도HQ/대사/잔기','finding':'기존미술/대표실기와끝점보존근거유지.추가확정재작화후보없음.','acceptance_needed':'새우려없는통과검사반복불필요.큰일러스트·작은아이콘을45px전신과일괄동일화하지않음.잔여실기한계유지.','evidence':['riko_views','rin_views','zero_endpoint_views','x_endpoint_views']},
]
j['next_work']=[{'owner':g['owner'],'scope':g['scope'],'stage':g['finding'],'evidence':g['evidence']}for g in j['gap_analysis']]
j['new_runtime_scope']=[{'evidence':'nana_rn37_shot_runtime11','kind':'포스일반/차지 양방향','captured_frames':224,'root_viewed_boards':9,'individual_ref_GPU_verified':False},{'evidence':'shibuki_br25_shot_runtime11','kind':'획득후Ultimate 일반/차지 양방향','captured_frames':224,'encoded_WebP_frames':223,'root_viewed_boards':9,'individual_ref_GPU_verified':False},{'evidence':'nana_selection39_runtime11','kind':'선택자동연출','captured_frames':240,'encoded_WebP_frames':237,'root_viewed_boards':4,'individual_ref_GPU_verified':False},{'evidence':'nana_hover39_runtime11','kind':'호버','details_from_summary':hr,'scope_not_expanded':True}]
j['coverage_limits']=[s for s in old['coverage_limits']if not(s.startswith('앨범28의')or s.startswith('호버총구차이는'))]
j['coverage_limits']+=['앨범30의2757변경/4510표시/28폼은BR25/RN39와일치한다.고유원화수·품질완료율·실기표본율로환산하지않는다.','기본/포스 체이서3e11의정적독립통과/동결여부는이앨범의통합여부와다르다.BR25에는미포함.','호버새팔은원발사점표와정본총으로정합된최종e630이다.이전8열보존중간안은폐기된진단이며현재미완료항목처럼세지않는다.','원US Nova214/216의차이를보존복원한것과기존Nana의동형정책은다르다.현재213/215새원화등록은동결이아니다.','이번장부작성은기존근거파일을결속한것이며새게임실행·Zero전수검사·전체최신시트미술열람을하지않았다.']
j['scope']='BR25/RN39·앨범30 기준 네 캐릭터 전체 범위11. 기존 근거 결속이며 완료율이 아니다.'
j['snapshot_summary']='BR25/RN39와앨범30을동일자원으로연결했다.시부키Ultimate85..92·나나선택8·Ultimate호버10은동결통합,각대표실기는원요약범위로분리했다.시부키기본체이서13은'+('후속동결됐지만'if chaser_frozen else'새준비/독립통과했지만')+'BR25미통합이며Ultimate체이서/Nova·호버,나나Nova·보류사다리7,시부키135및미관측실기는남아있다.'
j['completed_milestones_since_previous']=[{'scope':'BR25 Ultimate85..92 동결통합','evidence':['br25','shibuki_ult_fire8_frozen11'],'all_runtime_verified':False},{'scope':'RN38선택8/RN39호버10 동결통합','evidence':['rn39','nana_selection8_frozen11','nana_hover_frozen11'],'all_runtime_verified':False},{'scope':'BR25/RN39 최신앨범30 일치','evidence':['album30','album30_browser'],'all_art_complete':False}]
for k in('all_art_complete','all_gameplay_verified','user_final_accepted','game_or_art_modified'):j[k]=False
assert[c for c in old['cells']if c['character']in('riko','rin')]==[c for c in j['cells']if c['character']in('riko','rin')]
for k,v in old['evidence'].items():assert j['evidence'][k]==v
def parse_refs(text):
 out=[]
 for r in text.replace(' ','').split(','):
  if '..'in r:a,b=map(int,r.split('..'));out+=list(range(a,b+1))
  elif r:out.append(int(r))
 return out
checks=[]
for char in('shibuki','nana'):
 for form in('base','fourth','ultimate_before','ultimate_after'):
  rr=[r for c in j['cells']if(c['character'],c['form'])==(char,form)for s in c['states']for r in parse_refs(s['refs'])]
  assert len(rr)==len(set(rr))==228 and set(rr)==set(range(237))-{105,*range(175,183)},(char,form)
  checks.append({'character':char,'form':form,'classified_unique_refs':228,'missing':[],'duplicate':[],'classification_is_not_acceptance':True})
for c in j['cells']:
 for k in c['evidence']:assert k in j['evidence']
for k,q in new.items():assert sha(ROOT/q['path'])==q['sha256'],k
O.mkdir(exist_ok=False);(O/'coverage.json').write_text(json.dumps(j,ensure_ascii=False,indent=2)+'\n','utf8')
esc=html.escape
def link(k):return '<a href="'+esc(os.path.relpath(ROOT/j['evidence'][k]['path'],O).replace('\\','/'))+'">'+esc(k)+'</a>'
page=['<!doctype html><html lang="ko"><meta charset="utf-8"><title>전체 범위11 · BR25/RN39</title><style>body{font:15px system-ui;background:#14202b;color:#edf3fa;margin:24px}a{color:#9dceff}table{border-collapse:collapse;width:100%;margin:20px 0}td,th{border:1px solid #526577;padding:10px;vertical-align:top;text-align:left}small{color:#b8c8d6}</style><h1>네 캐릭터 범위11</h1><p>BR25/RN39 · 12전신폼 × 12범주. 표시 수는 고유원화나 품질 완료율이 아닙니다.</p><p>'+esc(j['snapshot_summary'])+'</p><p><a href="coverage.json">전체 JSON</a> · <a href="../full_scope_matrix10/COVERAGE.html">이전10</a></p><p>현재 근거: '+' · '.join(link(k)for k in('br25','rn39','album30','album30_browser','protection47'))+'</p><h2>남은 범위와 수용 조건</h2><table><tr><th>담당/범위</th><th>현재 판단</th><th>남은 조건</th></tr>']
for g in j['gap_analysis']:page.append('<tr><td>'+esc(g['owner']+' · '+g['scope'])+'</td><td>'+esc(g['finding'])+'</td><td>'+esc(g['acceptance_needed'])+'<details><summary>근거</summary>'+'<br>'.join(link(k)for k in g['evidence'])+'</details></td></tr>')
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
v={'passed':True,'cells':len(j['cells']),'evidence_files':len(j['evidence']),'new_bound_inputs':len(new),'local_links':len(links),'broken_links':0,'x_reference_classification':checks,'zero_cells_unchanged':True,'prior_snapshot_unmodified_sha256':sha(P),'new_gameplay_or_native_tests_performed':False,'new_all_sheet_visual_review_performed':False,'source_art_or_game_modified':False,'all_art_complete':False,'album_matches_current_integration':True,'chaser_in_BR25':False}
(O/'verification.json').write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n','utf8')
print(json.dumps({'coverage_sha256':sha(O/'coverage.json'),'html_sha256':sha(O/'COVERAGE.html'),'verification_sha256':sha(O/'verification.json'),'cells':len(j['cells']),'evidence_files':len(j['evidence'])}))
