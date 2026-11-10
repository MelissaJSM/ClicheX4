"""실제로 받은 사용자 수용과 현재 제작 대상을 기록한다."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
def read(p):return json.loads((ROOT/p).read_text('utf8'))
def write(p,d):(ROOT/p).write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n','utf8')
build='out/ver_rin_nana/rin_common_20261029T051459667484Z'
sha='5434083adbcbb4dd651a4b6e83228dd6cbc2ca6a03291d882db13ba58de55571'
quote='좋아 내가 테스트해봤는데 잘된거같아 계속 진행해도좋아'
session='work/ver_rin_nana/emulator_sessions/20261029T051617976097Z'
r={'date':'2026-10-29','build_sha256':sha,'session':session,'fresh_boot':True,
   'observed_screens':['title','character_selection'],'screenshots':[session+'/20261029T051758034056Z.png',session+'/20261029T051723063593Z.png'],
   'f3_source':'title state saved from this common build; no previous English F3',
   'user_tested_accepted':True,'user_quote':quote,'user_exact_scene_list':None,
   'all_dialogue_runtime_verified':False,'all_save_armor_combinations_runtime_verified':False,
   'automatic_runtime_exhaustive':False,'cpu_evidence':'common/native_cpu_verification.json'}
for p in r['screenshots']:
    if not (ROOT/p).exists():raise ValueError('Missing screenshot '+p)
write(build+'/runtime/verification.json',r)
p=read('projects/ver_rin_nana/project.json')
p['active_task']='x_nana';p['active_substage']='NANA_ART_PILOT_PENDING_REVIEW';p['latest_integrated_build']=build
p['character_names']['game_text_applied']=True
p['integration_policy']['status']='common_localization_user_accepted'
p['integration_policy']['current_test_base']='original_ps1_us_with_rin_art_and_common_localization'
p['integration_policy']['current_test_scope']='수용한 린 그래픽과 공통 한글·이름·로고·강지 통합. 나나 몸체/아머는 아직 원작.'
p['common_localization']={'build':build,'sha256':sha,'status':'user_tested_accepted','quote':quote,'record':'docs/RIN_COMMON_LOCALIZATION.md','exhaustive_runtime':False}
p['warp_tone_fix'].update(user_accepted=True,user_acceptance_quote='좋아 이상없어 다음작업으로 넘어가도 좋아',user_acceptance_date='2026-10-29',animation_runtime_verified=False,user_runtime_observation_accepted=True)
p['nana_pilot']={'status':'pending_user_art_review','candidate':'out/ver_rin_nana/nana_pilot_v9/candidate.json','art_approved':False,'game_applied':False,'runtime_verified':False}
p['style_approval_task']='zero_rin'
write('projects/ver_rin_nana/project.json',p)
q=read('projects/ver_rin_nana/current_build.json')
if q['sha256']!=sha:raise ValueError('Current build advanced unexpectedly')
q['runtime_verified']=True;q['runtime_scope']='fresh_boot_title_and_selection_observed; user acceptance; not exhaustive'
q['common_localization_user_accepted']=True;q['runtime_evidence']=build+'/runtime/verification.json';q['nana_art_produced_in_build']=False
write('projects/ver_rin_nana/current_build.json',q)
for name in ('manifest.json','verification.json'):
    m=read(build+'/'+name);m['runtime_verified']=True;m['runtime_scope']=q['runtime_scope'];m['runtime_evidence']='runtime/verification.json';m['user_accepted']=True
    if name=='manifest.json':m['verification'].update(runtime_verified=True,runtime_scope=q['runtime_scope'])
    write(build+'/'+name,m)
write('projects/ver_rin_nana/nana_candidate.json',{'project':'ver_rin_nana','task':'x_nana','candidate':'out/ver_rin_nana/nana_pilot_v9/candidate.json','review':'out/ver_rin_nana/nana_pilot_v9/review_1x_4x.png','art_approved':False,'game_applied':False})
print('Acceptance, current build and Nana pilot metadata recorded.')
