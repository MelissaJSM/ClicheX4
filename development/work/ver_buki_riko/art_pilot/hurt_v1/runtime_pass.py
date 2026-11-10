"""Run a checked input plan beside the read-only hurt observer, then preserve logs."""
from pathlib import Path
import subprocess,sys,time,json
ROOT=Path(__file__).resolve().parents[4];D=Path(__file__).parent
baseline,session,plan=map(Path,sys.argv[1:4]);prior=json.loads(baseline.read_text());build=Path(prior['source_build'])
extra=['--hurt-facing',sys.argv[4]] if len(sys.argv)>4 else []
name=plan.stem;startup=subprocess.STARTUPINFO();startup.dwFlags|=subprocess.STARTF_USESHOWWINDOW;startup.wShowWindow=0
logfile=D/(name+'_runtime.log')
with logfile.open('x',encoding='utf8') as log:
 p=subprocess.Popen([sys.executable,'scripts/capture_jump_cycle.py','--build',str(build),'--baseline',str(baseline),'--hurt','--observe',*extra],cwd=ROOT,stdout=log,stderr=subprocess.STDOUT,startupinfo=startup)
 time.sleep(.7)
 run=subprocess.run([sys.executable,'scripts/playback_inputs.py','--session',str(session),'--plan',str(plan),'--baseline',str(baseline)],cwd=ROOT,capture_output=True,text=True)
 (D/(name+'_playback.log')).write_text(run.stdout+run.stderr,'utf8');print(run.stdout,flush=True)
 status=p.wait(timeout=60)
print(logfile.read_text('utf8'))
if status or run.returncode:raise SystemExit(1)
