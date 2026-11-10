"""Reach character selection with bounded ordinary input, after authenticating the build."""
import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from scripts.observe_sprite_consistency_runtime import ReadOnlyProcess

p = argparse.ArgumentParser()
p.add_argument('--session', type=Path, required=True)
p.add_argument('--project', choices=['ver_buki_riko', 'ver_rin_nana'], required=True)
p.add_argument('--ram-base', type=int, required=True)
p.add_argument('--output', type=Path, required=True)
a = p.parse_args()
assert not a.output.exists()
record = json.loads((a.session / 'session.local.json').read_text('utf8'))
check = json.loads(subprocess.check_output([
    sys.executable, str(Path(__file__).with_name('read_menu_br24.py')),
    '--session', str(a.session), '--pid', str(record['pid']), '--ram-base', str(a.ram_base),
], text=True, encoding='utf8'))
assert check['passed'] and check['project'] == a.project
proc = ReadOnlyProcess(record)
events = []
start = time.monotonic()
previous = None
last_action = -10
try:
    while time.monotonic() - start < 35:
        g = proc.read(a.ram_base + 0x173c70, 16)
        t = proc.read(a.ram_base + 0x141bd8, 12)
        state = (g[0], g[1], g[2], g[13], t[4])
        now = time.monotonic() - start
        if state != previous:
            events.append({'seconds': round(now, 3), 'state': state})
            previous = state
        e = proc.read(a.ram_base + 0x1721c0, 100)
        if (e[0], e[1]) == (1, 3):
            break
        scan = None
        extended = False
        if now - last_action > 1.2:
            # Opening FMV can leave input_phase=1 while the native loop counter pauses.
            # Start is the observed ordinary skip input for these opening routes.
            if (g[0] == 1 and g[13] == 0) or g[0] in (0, 2, 3):
                scan = '0x35'
            elif g[0] == 1 and g[13] == 1 and g[1] < 12:
                scan = '0x35'
            elif g[0] == 6 and g[1] == 1 and t[4] == 0:
                if g[2] == 0:
                    scan = '0x2d'
                else:
                    break
        if scan:
            cmd = [sys.executable, 'scripts/korean_runtime_control.py', '--project', a.project,
                   'key', '--scan', scan, '--session', str(a.session)]
            if extended:
                cmd.append('--extended')
            result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf8', timeout=5)
            events.append({'seconds': round(now, 3), 'scan': scan, 'extended': extended,
                           'exit': result.returncode, 'output': result.stdout, 'error': result.stderr})
            if result.returncode:
                break
            last_action = time.monotonic() - start
        time.sleep(.03)
finally:
    proc.close()
a.output.write_text(json.dumps({'session': str(a.session), 'events': events,
    'memory_written': False, 'save_keys_sent': False}, ensure_ascii=False, indent=2) + '\n', 'utf8')
print(json.dumps({'trace': str(a.output), 'final_state': previous, 'events': len(events)}))
