from pathlib import Path
import json,subprocess,sys
ROOT=Path(__file__).resolve().parents[4];p=Path(__file__).parent
session='work/ver_buki_riko/emulator_sessions/20261026T170727349064Z'
evidence='work/ver_buki_riko/live_poc/20261026T172519613434Z/verification.local.json'
results=json.loads((p/'weapon_left_runs.json').read_text()) if len(sys.argv)>1 else []
for q in json.loads((p/'weapon_left_plans.json').read_text()):
 if len(sys.argv)>1 and str(q['weapon']) not in sys.argv[1:]:continue
 c=subprocess.run([sys.executable,'scripts/emulator_session.py','key','--session',session,'--scan','0x3d'],cwd=ROOT,capture_output=True,text=True)
 if c.returncode:raise RuntimeError(c.stderr)
 c=subprocess.run([sys.executable,'scripts/emulator_session.py','key','--session',session,'--scan','0x4b','--extended','--hold','0.7'],cwd=ROOT,capture_output=True,text=True)
 if c.returncode:raise RuntimeError(c.stderr)
 c=subprocess.run([sys.executable,'scripts/capture_shibuki_batch.py','--evidence',evidence,'--plan',q['plan']],cwd=ROOT,capture_output=True,text=True)
 if c.returncode:raise RuntimeError(c.stderr)
 r=json.loads(c.stdout);out=Path(r['output']);trace=json.loads((out/'trace.json').read_text());observed=sorted({row[6] for row in trace['rows']});r.update(weapon=q['weapon'],name=q['name'],observed_weapons=observed,selection_verified=q['weapon'] in observed)
 if not r['selection_verified']:raise RuntimeError('Wrong weapon selected: '+str(r))
 data=json.loads((out/'verification.local.json').read_text())
 target={2:{95,96,138,139},4:{103,104,231,232},7:{97,98,99}}[q['weapon']]
 matched={v['frame'] for v in data['results'] if v['weapon']==q['weapon'] and v['flags15_bit6']==0 and v['ram_equal'] and v['vram_equal'] and any(m['flip_x']==False for m in v['render_matches'])}
 if not target<=matched:raise RuntimeError('Left-facing special frames not matched: '+str(target-matched))
 results=[v for v in results if v['weapon']!=q['weapon']];results.append(r);(p/'weapon_left_runs.json').write_text(json.dumps(results,indent=2));print(json.dumps(r),flush=True)
