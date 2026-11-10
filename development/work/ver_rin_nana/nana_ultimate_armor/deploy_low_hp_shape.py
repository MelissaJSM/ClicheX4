import json,sys,shutil,subprocess,time,importlib.util
from pathlib import Path
R=Path.cwd();sys.path.insert(0,str(R))
from scripts.project import digest
D=R/'work/ver_rin_nana/nana_ultimate_armor'
spec=importlib.util.spec_from_file_location('progress',D/'low_hp_shape_progress.py');progress=importlib.util.module_from_spec(spec);spec.loader.exec_module(progress)
saved=json.loads((D/'low_hp_shape_saved_progress.json').read_text('utf8'));build=json.loads((D/'low_hp_shape_build.json').read_text('utf8'));current=R/'projects/ver_rin_nana/current_build.json';prior=current.read_bytes();c=json.loads(prior);now=progress.player()
assert all(now[k]==saved[k]for k in('character','hp','armor','ultimate','world')),'User progress changed; save latest again'
assert now['animation']==6 and now['frame'] in range(120,126)
assert c['sha256']=='1cf2d96949548cf1b4e468a561fa82f67019017e6df5b74779f2ed50aad1ab9f'
out=R/build['build'];assert digest(out/'rin_nana.bin')==build['sha256']
state=R/'work/ver_rin_nana/emulator/sstates/SLUS_005.61.000';ready=R/'work/ver_rin_nana/checkpoints/nana_ultimate_low_hp_shape_v1/SLUS_005.61.000';report=json.loads((ready.parent/'refresh.json').read_text('utf8'));assert digest(state)==saved['source_sha256'] and digest(ready)==report['output_sha256']
back=json.loads((R/saved['backup']/'backup.json').read_text('utf8'));cards=[q for q in back if '/memcards/'in q['path']];assert len(cards)==2
for q in cards:assert digest(R/q['path'])==q['sha256']
cmd=[sys.executable,'scripts/emulator_session.py','--project','ver_rin_nana']
subprocess.run(cmd+['close','--session',c['current_session']],check=True)
assert current.read_bytes()==prior and digest(state)==saved['source_sha256']
for q in cards:assert digest(R/q['path'])==q['sha256']
shutil.copy2(ready,state);assert digest(state)==report['output_sha256']
launched=subprocess.run(cmd+['launch','--cue',str(out/'rin_nana.cue')],check=True,capture_output=True,text=True);session=json.loads(launched.stdout);print(launched.stdout,flush=True)
sess=Path(session['session']).relative_to(R).as_posix()
for file in(current,R/'projects/ver_rin_nana/nana_ultimate_candidate.json'):
 p=json.loads(file.read_text('utf8'));p.update(build=build['build'],cue=build['build']+'/rin_nana.cue',sha256=build['sha256'],current_session=sess,emulator_pid=session['pid'],runtime_verified=False,runtime_verification_source=None,stage='LOW_HEALTH_REVIEW',ultimate_low_hp_shape_applied=True,ultimate_low_hp_user_accepted=False,ultimate_low_hp_runtime_assets_verified=False,ultimate_low_hp_report='docs/NANA_ULTIMATE_LOW_HP.md',latest_progress_evidence=(D/'low_hp_shape_saved_progress.json').relative_to(R).as_posix(),control_handed_to_user=False,next_scope='Review fuller low-health body 120..125; other reaction review remains')
 if file.name=='nana_ultimate_candidate.json':p.update(current_build=build['build'],current_sha256=build['sha256'],active_bin_sha256=build['sha256'],active_frames=list(range(120,126)))
 file.write_text(json.dumps(p,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
time.sleep(2)
subprocess.run(cmd+['key','--session',sess,'--scan','0x3d'],check=True)
(D/'low_hp_shape_deployment.json').write_text(json.dumps(dict(build=build,session=sess,pid=session['pid'],saved=saved,refresh=report,cards=cards,state_sha256=digest(state)),indent=2),encoding='utf8')
