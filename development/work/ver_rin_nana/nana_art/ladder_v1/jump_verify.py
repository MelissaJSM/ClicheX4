from pathlib import Path
import subprocess,sys,time,threading,json
ROOT=Path(__file__).resolve().parents[4]
session='work/ver_rin_nana/emulator_sessions/20261029T232815589359Z';build='out/ver_rin_nana/nana_ladder_20261029T232724676396Z';control=[]
def jump():
 time.sleep(1.4)
 r=subprocess.run([sys.executable,'scripts/korean_runtime_control.py','--project','ver_rin_nana','key','--session',session,'--scan','0x2d','--hold','.45'],capture_output=True,text=True,cwd=ROOT);control.append({'returncode':r.returncode,'stdout':r.stdout,'stderr':r.stderr})
t=threading.Thread(target=jump);t.start();r=subprocess.run([sys.executable,'scripts/capture_poc_memory.py','--project','ver_rin_nana','--pid','21956','--build',build,'--character','x','--frame','39','--animation','10','--timeout','7'],capture_output=True,text=True,cwd=ROOT);t.join();result={'observer':{'returncode':r.returncode,'stdout':r.stdout,'stderr':r.stderr},'control':control};(Path(__file__).parent/'jump_verify.json').write_text(json.dumps(result,indent=2),'utf8');print(json.dumps(result));sys.exit(r.returncode)
