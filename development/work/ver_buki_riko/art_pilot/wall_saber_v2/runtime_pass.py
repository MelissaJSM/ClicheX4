"""Concurrent read-only capture and normal-input playback for this candidate."""
from pathlib import Path
import subprocess,sys,time,json
ROOT=Path(__file__).resolve().parents[4];D=Path(__file__).parent
S=ROOT/'work/ver_buki_riko/emulator_sessions/20261024T074619623607Z'
B=ROOT/'out/ver_buki_riko/riko_bank1_20261024T074353134413Z'
BASE=ROOT/'work/ver_buki_riko/live_poc/20261024T074944605716Z/verification.local.json'
mode,name=sys.argv[1:];startup=subprocess.STARTUPINFO();startup.dwFlags|=subprocess.STARTF_USESHOWWINDOW;startup.wShowWindow=0
logfile=D/(name+'_runtime.log')
with logfile.open('x',encoding='utf8') as log:
 p=subprocess.Popen([sys.executable,'scripts/capture_jump_cycle.py','--build',str(B),'--baseline',str(BASE),'--'+mode,'--observe'],cwd=ROOT,stdout=log,stderr=subprocess.STDOUT,startupinfo=startup)
 time.sleep(.7)
 run=subprocess.run([sys.executable,'scripts/playback_inputs.py','--session',str(S),'--plan',str(S/(name+'.json')),'--baseline',str(BASE)],cwd=ROOT,capture_output=True,text=True)
 (D/(name+'_playback.log')).write_text(run.stdout+run.stderr,'utf8');print(run.stdout,flush=True)
 status=p.wait(timeout=60)
print(logfile.read_text('utf8'))
if status or run.returncode:raise SystemExit(1)
