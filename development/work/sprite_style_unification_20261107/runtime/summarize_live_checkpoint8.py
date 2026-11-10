import json,hashlib
from datetime import datetime,timezone
from pathlib import Path
W=Path('work/sprite_style_unification_20261107');R=W/'runtime'
def digest(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for c in iter(lambda:f.read(8388608),b''):h.update(c)
 return h.hexdigest()
base=json.loads((W/'protection_before.json').read_text('utf8'))['files']
current={};bad=[]
for name,old in base.items():
 p=Path(name);now={'size':p.stat().st_size,'sha256':digest(p)};current[name]=now
 if now!=old:bad.append({'path':name,'before':old,'after':now})
protection={'passed':not bad,'protected_files':len(base),'mismatches':bad,'files':current}
(W/'protection_checkpoint10.json').write_text(json.dumps(protection,ensure_ascii=False,indent=2)+'\n','utf8')
a=json.loads((R/'riko_ground_play01/evidence.json').read_text('utf8'));b=json.loads((R/'riko_ground_watch01/evidence.json').read_text('utf8'))
m=json.loads((R/'riko_ground_play01_review/manifest.json').read_text('utf8'))
report={'utc':datetime.now(timezone.utc).isoformat(),'project':'ver_buki_riko','disc_sha256':b['disc_sha256'],'session':a['session'],'pid':a['pid'],
 'fresh_boot':True,'character':'Riko / native character 1','scene':'Intro Sky Lagoon, stage0 area0','actual_window_frames':a['frames'],'record_seconds':a['plan']['duration'],
 'observed_unique_verified_references':len(b['verified_bank_frames']),'verified_bank_frames':b['verified_bank_frames'],
 'native_main_loop_counter':b['native_main_loop_counter'],'resident_assets_still_exact':b['resident_assets_still_exact'],
 'unverified_transition_events':[{ 'event_index':i,'frame':b['events'][i]['frame'],'stable_samples':b['events'][i]['stable_samples'],'same_frame_verified_elsewhere':any(e['verified'] and(e['bank'],e['frame'])==(b['events'][i]['bank'],b['events'][i]['frame'])for e in b['events'])}for i in b['unverified_events']],
 'root_actually_viewed':[{'path':p['path'],'sha256':digest(Path(p['path']))}for p in m['pages']],
 'findings':'Actual recorded still sequences reviewed: idle/run transitions, dash/recovery, jump/landing, ground first saber and aerial saber in both directions. No additional certain body/cape separation or outline-corruption defect seen in these captures.',
 'limits':['Three-hit combo was attempted but observer shows only animation88 ground first strike; second and third strikes not verified here.','No all-boss special skills, vehicles, victory/arrival, black-palette or other-character runtime coverage in this clip.','Recorded 16fps-ish window captures do not include every 60Hz game display. Static/sequence views do not establish user acceptance.'],
 'isolated_test_cards':'work/ver_buki_riko/sprite_style_checkpoint8/cards','session_closed_normally':True,'f1_f3_used':False,'process_memory_written':False,'active_build_pointers_changed':False,'protected_original_files_unchanged':not bad,'protection_report':(W/'protection_checkpoint10.json').as_posix(),
 'input_plan':(R/'riko_ground_plan.json').as_posix(),'watch_evidence':(R/'riko_ground_watch01/evidence.json').as_posix(),'record_evidence':(R/'riko_ground_play01/evidence.json').as_posix(),'user_accepted':False,'all_character_runtime_complete':False}
(R/'riko_checkpoint8_summary.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf8')
print(json.dumps({'protected':len(base),'unchanged':not bad,'actual_window_frames':a['frames'],'verified_refs':len(b['verified_bank_frames']),'actual_review_pages':len(m['pages'])}))
if bad:raise RuntimeError('Protected data changed')
