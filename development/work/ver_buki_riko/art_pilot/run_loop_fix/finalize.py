from pathlib import Path
import json,shutil,hashlib
import sys
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT))
from scripts.emulator_session import working_instances
P=Path(__file__).parent
BUILD=ROOT/'out/ver_buki_riko/riko_motion_20261023T143602957663Z'
SESSION=ROOT/'work/ver_buki_riko/emulator_sessions/20261023T143637197949Z'
MOTION=ROOT/'work/ver_buki_riko/run_loop_frames/20261023T143104731852Z/motion_set.json'
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def write(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def rel(p):return p.relative_to(ROOT).as_posix()
manifest=read(BUILD/'manifest.json');sha=manifest['modified_bin']['sha256']
assert sha=='3b7ffb07e1d731ae93c9cc5afa2a67603a8bdd3e763a4f9dec94c9ba0be5bfd4'
assert read(SESSION/'close.local.json')['exited'] and not working_instances(include_original=True)
attempts=[];verified=set();both={False:set(),True:set()}
for kind in ('run','idle','jump'):
 for path in sorted((ROOT/f'work/ver_buki_riko/{kind}_runtime').glob('20261023T14*/verification.local.json')):
  v=read(path)
  if v['modified_bin_sha256']!=sha:continue
  orientations={n:sorted({m['flip_x'] for m in r['matches']}) for n,r in v['frames'].items() if r['verified']}
  verified.update(int(n) for n in orientations)
  if kind=='run':
   for n,flips in orientations.items():
    for flip in flips:both[flip].add(int(n))
  trace=read(path.parent/'player_trace.json');seq=[]
  for row in trace['rows']:
   key=tuple(row[1:2]+row[3:5])
   if not seq or seq[-1][1]!=key:seq.append((row[0],key))
  edges=[]
  for a,b in zip(seq,seq[1:]):
   if a[1][:2]==(1,8) and b[1][:2]==(1,8) and (a[1][2],b[1][2]) in ((13,14),(20,7)):
    edges.append({'from':a[1][2],'to':b[1][2],'from_seconds':a[0],'to_seconds':b[0]})
  complete=[]
  for i in range(len(seq)-14):
   if [s[1] for s in seq[i:i+15]]==[(1,8,n) for n in (*range(7,21),7)]:
    complete.append({'start_seconds':seq[i][0],'end_seconds':seq[i+14][0],'duration_seconds':seq[i+14][0]-seq[i][0]})
  attempts.append({'mode':kind,'direction':v.get('run_direction'),'evidence':rel(path),
                   'verified_frames':v['verified_frames'],'unverified_frames':v['unverified_frames'],
                   'verified_orientations_flip_x':orientations,'hold_seconds':trace['hold_seconds'],
                   'traced_boundary_transitions':edges,'traced_complete_cycles':complete})
expected_run={3,4,5,6,*range(7,21)}
assert expected_run<=both[True] and expected_run<=both[False]
applied={0,1,2,*range(3,35),146,147,148}
assert applied-verified=={32}
record=read(SESSION/'run_recording/recording.local.json')
summary={'bin_sha256':sha,'session':rel(SESSION),'baseline':'work/ver_buki_riko/live_poc/20261023T143833515321Z/verification.local.json',
         'attempts':attempts,'verified_frames':sorted(verified),'applied_but_unverified_frames':sorted(applied-verified),
         'run_and_settle_verified_both_directions':sorted(expected_run),
         'idle_current_direction':'left','jump_current_direction':'left',
         'trace_is_not_framebuffer_verification':True,'loop_quality_user_approved':False,
         'initial_baseline_failures':['During loading: no matching patched Zero RAM, exit 1',
                                      'First gameplay attempt: frame 147 animation 5 not captured in 15 seconds, exit 1'],
         'runtime_recording':{'source':rel(SESSION/'run_recording'),'frames':record['frame_count'],
                              'seconds':record['frame_times_seconds'][-1]-record['frame_times_seconds'][0],
                              'requested_fps':40,'input_events':record['input_events']},
         'process_memory_written':False,'session_closed':True,'remaining_provided_emulators':[]}
write(BUILD/'runtime_summary.json',summary)
shutil.copyfile(SESSION/'run_recording/run_live.gif',BUILD/'run_live_recording.gif')
shutil.copyfile(SESSION/'recording_review.png',BUILD/'run_live_review.png')
current_path=ROOT/'projects/ver_buki_riko/current_build.json';current=read(current_path)
write(P/'previous_current_build.json',current)
current['previous_build']=current['build']
for name in ('runtime_idle_right_evidence','runtime_motion_right_evidence'):
 current['historical_'+name]=current[name];current[name]=None
current.update({'build':rel(BUILD),'cue':rel(BUILD/'riko_motion.cue'),'bin_sha256':sha,'session':rel(SESSION),
 'runtime_verified_frames':sorted(verified),'runtime_unverified_current_build_frames':[32],
 'verification':rel(BUILD/'verification_20261023T143622692830Z.local.json'),
 'runtime_open_eye_evidence':summary['baseline'],'report':'docs/RIKO_RUN_LOOP_FIX.md','session_closed':True,
 'runtime_verified_orientation':'Current run3/4,7..20 and settle5/6: both; current six idle frames and observed jump: left. Earlier right idle/jump evidence is historical.',
 'runtime_idle_left_evidence':'work/ver_buki_riko/idle_runtime/20261023T144133410341Z/verification.local.json',
 'runtime_motion_left_evidence':'work/ver_buki_riko/jump_runtime/20261023T144150125259Z/verification.local.json',
 'runtime_run_right_evidence':[a['evidence'] for a in attempts if a['direction']=='right'],
 'runtime_run_left_evidence':[a['evidence'] for a in attempts if a['direction']=='left'],
 'motion_set':rel(MOTION),'preview':rel(BUILD/'loop_before_after.gif'),
 'previous_build_comparison':rel(BUILD/'previous_build_comparison.json'),
 'runtime_recording':rel(BUILD/'run_live_recording.gif'),
 'runtime_summary':rel(BUILD/'runtime_summary.json'),
 'run_loop_fix_changed_frames':[12,13,19,20],'run_loop_boundary_pairs':[[13,14],[20,7]],
 'previous_run_loop_rejected_by_user':True,'run_loop_style_review_pending':True,'unique_run_cycle_keys':12})
current['historical_right_facing_22_23_different_pixels']=current.pop('right_facing_22_23_different_pixels',0)
write(current_path,current)
selection_path=ROOT/'projects/ver_buki_riko/art_selection.json';selection=read(selection_path)
selection.update({'runtime_verified_build':rel(BUILD),'runtime_evidence':'docs/RIKO_RUN_LOOP_FIX.md',
 'previous_run_loop_rejected_by_user':True,'run_loop_style_review_pending':True})
selection['runtime_limitations']['current_build_unverified_idle_frames']=[]
selection['runtime_limitations']['current_build_idle_jump_direction']='left; earlier right evidence historical'
if 'scripts/prepare_riko_loop.py' not in selection['used_by']:selection['used_by'].append('scripts/prepare_riko_loop.py')
write(selection_path,selection)
print(json.dumps({'verified':sorted(verified),'both_run':sorted(expected_run),'unverified':sorted(applied-verified),
                  'cycles':[(a['direction'],len(a['traced_complete_cycles'])) for a in attempts if a['mode']=='run']}))
