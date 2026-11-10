from pathlib import Path
import sys,json,hashlib
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT))
from scripts.emulator_session import working_instances
from PIL import Image
P=Path(__file__).parent
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def save(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
build='out/ver_buki_riko/riko_motion_20261023T140114425399Z'
session='work/ver_buki_riko/emulator_sessions/20261023T140133142039Z'
runr=['work/ver_buki_riko/run_runtime/20261023T140402942164Z/verification.local.json',
      'work/ver_buki_riko/run_runtime/20261023T140534690093Z/verification.local.json']
runl='work/ver_buki_riko/run_runtime/20261023T140527497073Z/verification.local.json'
idle='work/ver_buki_riko/idle_runtime/20261023T140600725005Z/verification.local.json'
jump='work/ver_buki_riko/jump_runtime/20261023T140610137080Z/verification.local.json'
expected=set((3,4,5,6,*range(7,21)))
verified=set();directional={}
for label,paths,flip in [('left',[runl],False),('right',runr,True)]:
 found=set()
 for rel in paths:
  d=load(ROOT/rel)
  assert d['modified_bin_sha256']=='f60f8a050b1a2b4894e0a09aad986935e34c2396a82635c2d13f9752584ae50a'
  found|={int(n) for n,r in d['frames'].items() if any(m['flip_x']==flip for m in r['matches'])}
  verified|=set(d['verified_frames'])
 assert expected<=found
 directional[label]=sorted(found)
for rel in (idle,jump):verified|=set(load(ROOT/rel)['verified_frames'])
assert not working_instances(include_original=True)
manifest=load(ROOT/build/'manifest.json')
current=load(ROOT/'projects/ver_buki_riko/current_build.json')
save(P/'previous_current_build.json',current)
current.update({'build':build,'cue':build+'/riko_motion.cue','bin_sha256':manifest['modified_bin']['sha256'],
 'previous_build':'out/ver_buki_riko/riko_motion_20261023T130950715295Z',
 'session':session,'session_closed':True,'runtime_verified_frames':sorted(verified),
 'runtime_unverified_current_build_frames':[1,2,32,148],
 'runtime_verified_orientation':'Revised 3/4,7..20 and settle5/6: both. Current idle0/146/147 and observed jump: right. Other idle PNGs unchanged with prior evidence.',
 'verification':build+'/verification_20261023T140132330623Z.local.json',
 'runtime_open_eye_evidence':'work/ver_buki_riko/live_poc/20261023T140332770878Z/verification.local.json',
 'runtime_run_right_evidence':runr,'runtime_run_left_evidence':runl,
 'runtime_idle_right_evidence':idle,'runtime_motion_right_evidence':jump,
 'runtime_dash_evidence':None,'dash_short_frame_render_verification_pending':True,
 'report':'docs/RIKO_RUN_REVISION.md',
 'motion_set':'work/ver_buki_riko/run_revision_frames/20261023T140033413871Z/motion_set.json',
 'preview':build+'/run_before_after_4x.gif','runtime_recording':build+'/run_live_recording.gif',
 'previous_build_comparison':build+'/previous_build_comparison.json',
 'previous_run_rejected_by_user':True,'run_revision_requested':True,'run_style_review_pending':True,
 'production_quality_complete':False,'unique_run_cycle_keys':10,
 'fresh_process_launch_verified':True,'boot_navigation_fully_observed':False,'fresh_boot_verified':False,
 'agent_loaded_save_state':False})
save(ROOT/'projects/ver_buki_riko/current_build.json',current)
art=load(ROOT/'projects/ver_buki_riko/art_selection.json')
art.update({'runtime_verified_build':build,'runtime_evidence':'docs/RIKO_RUN_REVISION.md',
 'previous_run_rejected_by_user':True,'run_revision_requested':True,'run_style_review_pending':True})
art['used_by'].append('scripts/prepare_riko_run_revision.py')
art['runtime_limitations']['current_build_unverified_idle_frames']=[1,2,148]
save(ROOT/'projects/ver_buki_riko/art_selection.json',art)
save(ROOT/session/'zero_observation.local.json',{'pid':40620,'character':1,
 'basis':current['runtime_open_eye_evidence'],'fresh_process_launch':True,
 'boot_navigation_fully_observed':False,'agent_menu_input':False,'agent_loaded_state':False,
 'agent_saved_state':False,'observation':'31 seconds: game loading logo; 86 seconds: Zero in game. Intermediate navigation not observed.',
 'process_memory_written':False,'instances_remaining':working_instances(include_original=True)})
save(ROOT/build/'runtime_summary.json',{'directional_verified_frames':directional,
 'verified_current_build_frames':sorted(verified),'unverified_current_build_frames':[1,2,32,148],
 'run_left':runl,'run_right':runr,'idle_right':idle,'jump_right':jump,
 'session':session,'session_closed':True,'art_review_pending':True})
idle_ref=ROOT/'out/ver_buki_riko/riko_pilot_20261023T082720987715Z/riko_idle147_8x.png'
calls=[('cycle14_draft.png','prompt_cycle.txt',[idle_ref],False),
 ('paired8_v1.png','prompt_paired8.txt',[idle_ref],False),
 ('paired8_clean.png','prompt_paired8_cleanup.txt',[P/'paired8_v1.png',idle_ref],True),
 ('paired8_legorder.png','prompt_leg_order.txt',[P/'paired8_clean.png'],True),
 ('start2.png','prompt_start2.txt',[idle_ref,P/'paired8_clean.png'],True),
 ('paired8_down.png','prompt_down_clearance.txt',[P/'paired8_clean.png'],True),
 ('down_far.png','prompt_down_far.txt',[P/'down_far_edit.png'],True),
 ('flight2.png','prompt_flight2.txt',[P/'paired8_clean.png',idle_ref],False),
 ('flight2_compact.png','prompt_flight_compact.txt',[P/'flight2.png'],True)]
rows=[]
for name,prompt,refs,used in calls:
 im=Image.open(P/name)
 rows.append({'output':name,'sha256':digest(P/name),'size':im.size,'prompt':prompt,
  'prompt_sha256':digest(P/prompt),'references':[{'path':str(p),'sha256':digest(p)} for p in refs],
  'selected_crops_used':used,'transparent_background_requested':True})
save(P/'imagegen_calls.json',{'mode':'built-in image_gen.imagegen','calls':rows,
 'game_assets_sent':False,'selected_manifest':current['motion_set'],
 'note':'Only selected whole-pose crops are used. Exact crop, phase and scale are in motion_set. Drafts are not game frames.'})
print(json.dumps({'current_build':build,'verified_count':len(verified),'left':directional['left'],
 'right':directional['right'],'closed':True}))
