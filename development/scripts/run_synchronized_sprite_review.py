"""Start ordinary-input recording only after the read-only observer is ready."""
import argparse,json,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def main(a):
    out=a.output.resolve()
    if out.exists() or not any(out.is_relative_to(ROOT/p) for p in ('work/sprite_consistency_20261105/runtime','work/sprite_reaudit_20261106/runtime')):
        raise ValueError('New review output directory required')
    plan=json.loads(a.plan.read_text('utf8'))
    if plan['duration']>22:raise ValueError('Record at most 22 seconds within 30-second watch')
    out.mkdir(parents=True)
    observer=[sys.executable,'-B',str(ROOT/'scripts/observe_sprite_consistency_runtime.py'),
        '--project',a.project,'--session',str(a.session),'--ram-base',str(a.ram_base),
        '--vram-base',str(a.vram_base),'--seconds','30','--output',str(out/'observer')]
    proc=subprocess.Popen(observer,cwd=ROOT,stdout=subprocess.PIPE,stderr=subprocess.PIPE,
        text=True,encoding='utf8',creationflags=subprocess.CREATE_NO_WINDOW)
    prefix=[]
    try:
        while True:
            line=proc.stdout.readline()
            if not line:raise RuntimeError('Observer exited before ready: '+proc.stderr.read())
            prefix.append(line)
            try:ready=json.loads(line)
            except ValueError:continue
            if ready.get('ready'):break
        print(json.dumps(ready),flush=True)
        command=[sys.executable,'-B',str(ROOT/'scripts/record_sprite_review_play.py'),
            '--session',str(a.session),'--plan',str(a.plan),'--output',str(out/'recording')]
        recording=subprocess.run(command,cwd=ROOT,capture_output=True,text=True,encoding='utf8',
            creationflags=subprocess.CREATE_NO_WINDOW)
        stdout,stderr=proc.communicate(timeout=40)
        (out/'observer.log').write_text(''.join(prefix)+stdout+stderr,'utf8')
        (out/'recording.log').write_text(recording.stdout+recording.stderr,'utf8')
        if proc.returncode or recording.returncode:raise RuntimeError('Review failed; inspect logs')
        obs=json.loads((out/'observer/evidence.json').read_text('utf8'))
        rec=json.loads((out/'recording/evidence.json').read_text('utf8'))
        overlap=int(obs['watch_start_monotonic_ns'])<=int(rec['record_start_monotonic_ns'])<int(rec['record_end_monotonic_ns'])<=int(obs['watch_end_monotonic_ns'])
        evidence={'observer_ready':ready,'input_recording_fully_within_observation':overlap,
            'verified_bank_frames':obs['verified_bank_frames'],'recorded_frames':rec['frames'],
            'recording_error':rec['error'],'observer_unverified_events':obs['unverified_events']}
        (out/'synchronization.json').write_text(json.dumps(evidence,ensure_ascii=False,indent=2)+'\n','utf8')
        print(json.dumps(evidence),flush=True)
        if not overlap:raise RuntimeError('Input recording exceeded observation window')
    finally:
        if proc.poll() is None:proc.terminate();proc.wait(timeout=5)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--project',choices=['ver_buki_riko','ver_rin_nana'],required=True)
    p.add_argument('--session',type=Path,required=True);p.add_argument('--plan',type=Path,required=True)
    p.add_argument('--ram-base',type=int,required=True);p.add_argument('--vram-base',type=int,required=True)
    p.add_argument('--output',type=Path,required=True);main(p.parse_args())
