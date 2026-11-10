from pathlib import Path
import subprocess,sys,time
ROOT=Path(__file__).resolve().parents[4]
D=Path(__file__).parent
S=ROOT/'work/ver_buki_riko/emulator_sessions/20261024T071038950106Z'
B=ROOT/'out/ver_buki_riko/riko_bank1_20261024T070810249163Z'
BASE=ROOT/'work/ver_buki_riko/live_poc/20261024T071202334491Z/bank_baseline.local.json'
startup=subprocess.STARTUPINFO();startup.dwFlags|=subprocess.STARTF_USESHOWWINDOW;startup.wShowWindow=0
with (D/'wall_runtime.log').open('x',encoding='utf8') as log:
 p=subprocess.Popen([sys.executable,'scripts/capture_jump_cycle.py','--build',str(B),'--baseline',str(BASE),'--wall-saber','--observe'],cwd=ROOT,stdout=log,stderr=subprocess.STDOUT,startupinfo=startup)
 time.sleep(.8)
 run=subprocess.run([sys.executable,'scripts/playback_inputs.py','--session',str(S),'--plan',str(S/'wall_saber_check.json'),'--baseline',str(BASE)],cwd=ROOT)
 status=p.wait(timeout=60)
print((D/'wall_runtime.log').read_text('utf8'))
if status or run.returncode:raise SystemExit(1)
