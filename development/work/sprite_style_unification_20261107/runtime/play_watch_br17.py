"""Run ordinary controls only after the read-only observer authenticates BR v12."""
import argparse
import json
import subprocess
import sys
from pathlib import Path

p = argparse.ArgumentParser()
p.add_argument('--name', required=True)
p.add_argument('--plan', type=Path, required=True)
p.add_argument('--session', type=Path, required=True)
p.add_argument('--project', choices=['ver_buki_riko', 'ver_rin_nana'], required=True)
p.add_argument('--ram-base', type=int, required=True)
p.add_argument('--vram-base', type=int, required=True)
a = p.parse_args()
root = Path(__file__).resolve().parent
watch, play = root / (a.name + '_watch'), root / (a.name + '_play')
assert not watch.exists() and not play.exists()
duration = float(json.loads(a.plan.read_text('utf8'))['duration']) + 3
observe = [sys.executable, str(root / 'observe_br17.py'), '--project', a.project,
    '--session', str(a.session), '--ram-base', str(a.ram_base), '--vram-base', str(a.vram_base),
    '--seconds', str(duration), '--output', str(watch)]
recorder = [sys.executable, str(root / 'record_br17.py'), '--session', str(a.session),
    '--plan', str(a.plan), '--output', str(play)]
observer = subprocess.Popen(observe, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    text=True, encoding='utf8', creationflags=subprocess.CREATE_NO_WINDOW)
first = observer.stdout.readline()
try:
    ready = json.loads(first)
    if not ready.get('ready'):
        raise RuntimeError('Observer did not authenticate session')
    recorded = subprocess.run(recorder, capture_output=True, text=True, encoding='utf8', timeout=40)
    rest, err = observer.communicate(timeout=35)
    result = {'observer_start': ready, 'observer_exit': observer.returncode,
        'observer_output': rest, 'observer_error': err, 'record_exit': recorded.returncode,
        'record_output': recorded.stdout, 'record_error': recorded.stderr}
    (root / (a.name + '_orchestration.json')).write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', 'utf8')
    print(json.dumps({'name': a.name, 'observer_exit': observer.returncode,
        'record_exit': recorded.returncode, 'record_output': recorded.stdout}))
    if observer.returncode or recorded.returncode:
        raise RuntimeError('Runtime evidence capture failed; see report')
except Exception:
    if observer.poll() is None:
        observer.terminate()
        observer.wait(timeout=10)
    raise
