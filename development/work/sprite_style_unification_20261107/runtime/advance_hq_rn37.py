"""Bounded ordinary dialogue advances; stop before stage selection."""
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
p.add_argument('--ram-base', type=int, required=True)
p.add_argument('--output', type=Path, required=True)
a = p.parse_args()
assert not a.output.exists()
rec = json.loads((a.session / 'session.local.json').read_text('utf8'))
check = json.loads(subprocess.check_output([
    sys.executable, str(Path(__file__).with_name('read_menu_rn37.py')),
    '--session', str(a.session), '--pid', str(rec['pid']), '--ram-base', str(a.ram_base)
], text=True, encoding='utf8'))
assert check['passed'] and check['project'] == 'ver_rin_nana'
assert check['engine']['character'] == 0 and check['engine']['stage'] == 13
proc = ReadOnlyProcess(rec)
trace = []
try:
    started = time.monotonic()
    for _ in range(18):
        state = list(proc.read(a.ram_base + 0x1721c0, 4))
        trace.append({'seconds': time.monotonic() - started, 'state': state})
        if state[0] != 3 or state[1] != 9:
            break
        result = subprocess.run([sys.executable, 'scripts/korean_runtime_control.py',
            '--project', 'ver_rin_nana', 'key', '--session', str(a.session), '--scan', '0x2d'],
            capture_output=True, text=True, encoding='utf8', timeout=5)
        trace.append({'ordinary_cross': True, 'exit': result.returncode, 'output': result.stdout, 'error': result.stderr})
        if result.returncode:
            break
        time.sleep(0.8)
finally:
    proc.close()
a.output.write_text(json.dumps({'session': str(a.session), 'trace': trace,
    'memory_written': False, 'save_keys_sent': False}, ensure_ascii=False, indent=2) + '\n', 'utf8')
print(json.dumps({'output': str(a.output), 'final_state': state, 'steps': len(trace)}))
