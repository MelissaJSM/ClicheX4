from pathlib import Path
import json,shutil
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[4];D=Path(__file__).parent
B=ROOT/'out/ver_buki_riko/riko_motion_20261024T000131718284Z'
session=ROOT/'work/ver_buki_riko/emulator_sessions/20261024T000202081856Z'
def rel(p):return str(p.relative_to(ROOT)).replace('\\','/')
def read(p):return json.loads(p.read_text('utf8'))
def write(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
old=read(ROOT/'projects/ver_buki_riko/current_build.json')
assert old['bin_sha256']=='a2ff0b8c3ec3fd3748a2058725f2b7764a899c13a1e859b11b4c46a885b95c7f'
direct={'left':set(),'right':set()};pipeline={'left':set(),'right':set()};runs=[]
for name in ('20261024T000459647667Z','20261024T000522197610Z'):
 p=ROOT/'work/ver_buki_riko/dash_runtime'/name/'verification.local.json';j=read(p);runs.append(rel(p))
 for n,r in j['frames'].items():
  for m in r['matches']:direct['right' if m['flip_x'] else 'left'].add(int(n))
  for m in (r.get('pipeline_evidence') or {}).get('matches',[]):pipeline['right' if m['flip_x'] else 'left'].add(int(n))
verified=set.union(*direct.values());staggered=set.union(*pipeline.values())
inherited=(set(old['runtime_verified_frames'])|set(old['runtime_pipeline_verified_frames'])|set(old['runtime_inherited_unchanged_frames']))-{46,47,48}
all_frames=set(old['applied_frames']);sha=read(B/'manifest.json')['modified_bin']['sha256']
rec=read(session/'dash_recording/recording.local.json')
summary={'build':rel(B),'bin_sha256':sha,'direct_frames':sorted(verified),'direct_by_orientation':{k:sorted(v) for k,v in direct.items()},'pipeline_by_orientation':{k:sorted(v) for k,v in pipeline.items()},'pipeline_frames':sorted(staggered),'runs':runs,'baseline':'work/ver_buki_riko/live_poc/20261024T000358335934Z/verification.local.json','observation_only_run':'work/ver_buki_riko/dash_runtime/20261024T000407332774Z/verification.local.json','observation_only_result':'Idle147 only; no focus change or input; subsequently conducted explicit dash tests','session':rel(session),'session_closed':False,'agent_loaded_save_state':False,'agent_process_memory_written':False,'boot_navigation_fully_observed':False,'boot_observation':'Opening FMV and Zero Sky Lagoon loading observed; selection navigation not continuously observed. Current character1 and full graphics bank verified from read-only memory.','inherited_build':old['build'],'inherited_unchanged_frames':sorted(inherited),'inherited_evidence':'44 PNGs and all other decoded references identical; prior runtime summary distinguishes earlier sources','unverified_any_evidence_frames':sorted(all_frames-verified-staggered-inherited),'frame44':'Current RAM and upload equality; no complete exact framebuffer match. Cause unresolved.','new_dash_art_user_review_pending':True,'full_character_complete':False,'recording':{'path':rel(session/'dash_recording'),'frames':rec['frame_count'],'seconds':rec['frame_times_seconds'][-1]-rec['frame_times_seconds'][0]}}
write(B/'runtime_summary.json',summary)
shutil.copyfile(session/'dash_recording/dash_live.gif',B/'dash_live_recording.gif')
frames=sorted((session/'dash_recording').glob('client_*.png'))
if frames:
 board=Image.new('RGB',(960,720),(40,43,55));draw=ImageDraw.Draw(board)
 for i,f in enumerate(frames[::max(1,len(frames)//9)][:9]):
  im=Image.open(f).convert('RGB');im.thumbnail((320,220));board.paste(im,((i%3)*320,(i//3)*240+20));draw.text(((i%3)*320+4,(i//3)*240+4),f.name,fill='white')
 board.save(B/'runtime_contact_sheet.png')
shutil.copyfile(ROOT/'projects/ver_buki_riko/current_build.json',D/'previous_current_build.json')
shutil.copyfile(ROOT/'projects/ver_buki_riko/art_selection.json',D/'previous_art_selection.json')
old.update({'build':rel(B),'cue':rel(B/'riko_motion.cue'),'bin_sha256':sha,'session':rel(session),'session_closed':False,'boot_navigation_fully_observed':False,'motion_set':'work/ver_buki_riko/scale_frames/20261024T000122432696Z/motion_set.json','runtime_verified_frames':sorted(verified),'runtime_verified_by_orientation':summary['direct_by_orientation'],'runtime_pipeline_verified_frames':sorted(staggered),'runtime_inherited_unchanged_frames':sorted(inherited),'runtime_unverified_current_build_frames':sorted(all_frames-verified-staggered),'runtime_unverified_any_evidence_frames':summary['unverified_any_evidence_frames'],'runtime_summary':rel(B/'runtime_summary.json'),'runtime_recording':rel(B/'dash_live_recording.gif'),'preview':rel(B/'cape_before_after.png'),'dash_preview':rel(B/'dash_preview_4x.gif'),'all_current_frames_preview':rel(B/'riko_current_frames_2x.png'),'dash_context_preview':rel(B/'dash_context_sheet.png'),'verification':rel(B/'verification_20261024T000201339100Z.local.json'),'previous_build_comparison':rel(B/'previous_build_comparison.json'),'previous_build':summary['inherited_build'],'report':'docs/RIKO_DASH_CAPE_FIX.md','historical_pointer':rel(D/'previous_current_build.json'),'dash_style_user_review_pending':True,'cape_attachment_and_full_surface_revision':True})
write(ROOT/'projects/ver_buki_riko/current_build.json',old)
p=ROOT/'projects/ver_buki_riko/art_selection.json';art=read(p)
art.update({'status':'accepted_design_basis_whole_cape_revision_applied_review_pending','runtime_verified_build':rel(B),'runtime_evidence':'docs/RIKO_DASH_CAPE_FIX.md','runtime_summary':rel(B/'runtime_summary.json'),'historical_selection_snapshot':rel(D/'previous_art_selection.json'),'dash_cape_revision_requested':True,'dash_cape_revision_implemented':True,'dash_style_user_review_pending':True,'runtime_limitations':{'unverified_frames_including_inherited_evidence':summary['unverified_any_evidence_frames'],'current_dash_direct_frames_both_directions':[46,47,48],'current_dash_direct_right':summary['direct_by_orientation']['right'],'other_evidence':'Unchanged PNGs/decoded data inherit prior checks; not all motions freshly executed','frame44_ram_vram_equal':True,'frame44_render_exact_unverified':True}})
write(p,art)
print(json.dumps(summary))
