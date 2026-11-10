from pathlib import Path
import json,subprocess,sys
ROOT=Path(__file__).resolve().parents[4];p=Path(__file__).parent
session='work/ver_buki_riko/emulator_sessions/20261026T170727349064Z'
evidence='work/ver_buki_riko/live_poc/20261026T171641006043Z/verification.local.json'
results=[]
for q in json.loads((p/'weapon_test_plans.json').read_text()):
 c=subprocess.run([sys.executable,'scripts/emulator_session.py','key','--session',session,'--scan','0x3d'],cwd=ROOT,capture_output=True,text=True)
 if c.returncode:raise RuntimeError(c.stderr)
 c=subprocess.run([sys.executable,'scripts/capture_shibuki_batch.py','--evidence',evidence,'--plan',q['plan']],cwd=ROOT,capture_output=True,text=True)
 if c.returncode:raise RuntimeError(c.stderr)
 r=json.loads(c.stdout);out=Path(r['output']);trace=json.loads((out/'trace.json').read_text());observed=sorted({row[6] for row in trace['rows']});r.update(weapon=q['weapon'],name=q['name'],observed_weapons=observed,selection_verified=q['weapon'] in observed)
 if not r['selection_verified']:raise RuntimeError('Wrong weapon selected: '+str(r))
 results.append(r);(p/'weapon_runs.json').write_text(json.dumps(results,indent=2));print(json.dumps(r),flush=True)
