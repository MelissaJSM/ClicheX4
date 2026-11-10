"""읽기 전용 아머 관찰이 준비된 뒤 일반 키 입력을 시작한다."""
import argparse,json,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.project import new_run,write_json
from scripts.emulator_session import checked_window

def main():
    p=argparse.ArgumentParser();p.add_argument('--session',type=Path,required=True);p.add_argument('--evidence',type=Path,required=True);p.add_argument('--plan',type=Path,required=True);p.add_argument('--frames',required=True);p.add_argument('--seconds',type=float,default=22);p.add_argument('--both-directions',action='store_true');a=p.parse_args()
    plan=json.loads(a.plan.read_text());session=json.loads((a.session/'session.local.json').read_text());prior=json.loads(a.evidence.read_text())
    if prior['pid']!=session['pid'] or prior['modified_bin_sha256']!=session['bin_sha256'] or not plan['seconds']+1<a.seconds<=30:raise ValueError('Session or observation timing mismatch')
    checked_window(session['pid']);out=new_run(ROOT,'ver_buki_riko','shibuki_armor_playback');ready=out/'ready.json'
    with (out/'observer.txt').open('w',encoding='utf-8') as log:
        observer=subprocess.Popen([sys.executable,str(ROOT/'scripts/capture_shibuki_armor.py'),'--evidence',str(a.evidence),'--frames',a.frames,'--seconds',str(a.seconds),'--ready-file',str(ready)]+(['--both-directions'] if a.both_directions else []),cwd=ROOT,stdout=log,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
        deadline=time.monotonic()+10
        while not ready.exists() and observer.poll() is None and time.monotonic()<deadline:time.sleep(.05)
        if not ready.exists():raise RuntimeError('Observer did not verify RAM; no input sent')
        result=subprocess.run([sys.executable,str(ROOT/'scripts/playback_inputs.py'),'--session',str(a.session),'--plan',str(a.plan)],cwd=ROOT,capture_output=True,text=True)
        (out/'input.txt').write_text(result.stdout+result.stderr,encoding='utf-8');code=observer.wait(timeout=35)
    write_json(out/'result.json',{'observer_exit':code,'input_exit':result.returncode,'ready':json.loads(ready.read_text()),'session':str(a.session),'plan':str(a.plan)})
    print(json.dumps({'output':str(out),'observer_exit':code,'input_exit':result.returncode}));print((out/'observer.txt').read_text())
if __name__=='__main__':main()
