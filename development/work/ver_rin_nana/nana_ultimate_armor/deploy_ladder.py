import json,sys,shutil,subprocess,time,importlib.util
from pathlib import Path
R=Path.cwd();sys.path.insert(0,str(R))
from scripts.project import digest
D=R/'work/ver_rin_nana/nana_ultimate_armor'
spec=importlib.util.spec_from_file_location('progress',D/'ladder_progress.py');progress=importlib.util.module_from_spec(spec);spec.loader.exec_module(progress)
saved=json.loads((D/'ladder_saved_progress.json').read_text('utf8'));build=json.loads((D/'ladder_build.json').read_text('utf8'));current=R/'projects/ver_rin_nana/current_build.json';prior=current.read_bytes();c=json.loads(prior);now=progress.player()
assert all(now[k]==saved[k]for k in('character','hp','armor','ultimate','world')),'User progress changed; save again'
assert now['animation']==6 and now['frame']in range(120,126)
assert c['sha256']=='5385c70137954a9e380540539f389899c8f20e5428926e8e7bd51c8dbc60af08'
out=R/build['build'];assert digest(out/'rin_nana.bin')==build['sha256'];manifest=json.loads((out/'manifest.json').read_text('utf8'))
state=R/'work/ver_rin_nana/emulator/sstates/SLUS_005.61.000';ready=R/'work/ver_rin_nana/checkpoints/nana_ultimate_ladder_v1/SLUS_005.61.000';report=json.loads((ready.parent/'refresh.json').read_text('utf8'));assert digest(state)==saved['source_sha256']and digest(ready)==report['output_sha256']
back=json.loads((R/saved['backup']/'backup.json').read_text('utf8'));cards=[q for q in back if '/memcards/'in q['path']];assert len(cards)==2
for q in cards:assert digest(R/q['path'])==q['sha256']
cmd=[sys.executable,'scripts/emulator_session.py','--project','ver_rin_nana'];subprocess.run(cmd+['close','--session',c['current_session']],check=True)
assert current.read_bytes()==prior and digest(state)==saved['source_sha256']
for q in cards:assert digest(R/q['path'])==q['sha256']
shutil.copy2(ready,state);assert digest(state)==report['output_sha256']
launched=subprocess.run(cmd+['launch','--cue',str(out/'rin_nana.cue')],check=True,capture_output=True,text=True);session=json.loads(launched.stdout);print(launched.stdout,flush=True);sess=Path(session['session']).relative_to(R).as_posix()
for file in(current,R/'projects/ver_rin_nana/nana_ultimate_candidate.json'):
 p=json.loads(file.read_text('utf8'));p.update(build=build['build'],cue=build['build']+'/rin_nana.cue',sha256=build['sha256'],current_session=sess,emulator_pid=session['pid'],runtime_verified=False,runtime_verification_source=None,stage='LADDER_REVIEW',ultimate_ladder_applied=True,ultimate_ladder_user_accepted=False,ultimate_ladder_runtime_assets_verified=False,ultimate_ladder_report='docs/NANA_ULTIMATE_LADDER.md',latest_progress_evidence=(D/'ladder_saved_progress.json').relative_to(R).as_posix(),control_handed_to_user=False,next_scope='Review ladder climb/shoot/exit143..155/183; then arrival/victory/return',implemented_ultimate_references=manifest['implemented_ultimate_references'],full_ultimate_complete=False,cumulative_ultimate_references=len(manifest['implemented_ultimate_references']))
 if file.name=='nana_ultimate_candidate.json':p.update(current_build=build['build'],current_sha256=build['sha256'],active_bin_sha256=build['sha256'],active_frames=manifest['ultimate_ladder_recipe']and list(range(143,156))+[183])
 file.write_text(json.dumps(p,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
time.sleep(2);subprocess.run(cmd+['key','--session',sess,'--scan','0x3d'],check=True)
(D/'ladder_deployment.json').write_text(json.dumps(dict(build=build,session=sess,pid=session['pid'],saved=saved,refresh=report,cards=cards,state_sha256=digest(state)),indent=2),encoding='utf8')
