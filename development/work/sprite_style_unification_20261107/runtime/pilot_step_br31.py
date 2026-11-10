"""일시정지한 검증 세션에서 제한된 이동을 하고 즉시 다시 일시정지한다."""
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
p.add_argument('--keys', nargs='+', required=True, choices=('left', 'right', 'up', 'down', 'jump', 'dash', 'fire'))
p.add_argument('--hold', type=float, required=True)
p.add_argument('--output', type=Path, required=True)
a = p.parse_args()
assert .02 <= a.hold <= 2 and len(a.keys) <= 4
assert not a.output.exists() and a.output.resolve().is_relative_to(Path(__file__).resolve().parent)
record = json.loads((a.session / 'session.local.json').read_text('utf8'))
check = json.loads(subprocess.check_output([sys.executable, str(Path(__file__).with_name('read_menu_br31.py')),
    '--session', str(a.session), '--pid', str(record['pid']), '--ram-base', str(a.ram_base)], text=True, encoding='utf8'))
assert check['passed'] and check['project'] == 'ver_buki_riko'
assert (check['engine']['state'], check['engine']['substate']) == (6, 2), 'Require paused gameplay'
base = [sys.executable, 'scripts/korean_runtime_control.py', '--project', 'ver_buki_riko', 'key', '--session', str(a.session)]
proc = ReadOnlyProcess(record)
events = []

def key(args):
    q = subprocess.run(base + args, capture_output=True, text=True, encoding='utf8', timeout=8)
    assert q.returncode == 0, q.stderr
    v = json.loads(q.stdout)
    events.append({'args': args, 'result': v})
    return v

def state():
    return tuple(proc.read(a.ram_base + 0x1721c0, 2))

def wait_state(target):
    end = time.monotonic() + 4
    while time.monotonic() < end:
        if state() == target:
            return True
        time.sleep(.02)
    return False

result = {'session': str(a.session), 'bin_sha256': record['bin_sha256'], 'requested': vars(a).copy(),
          'events': events, 'memory_written': False, 'F1_F3_sent': False}
result['requested'] = {k: str(v) if isinstance(v, Path) else v for k, v in result['requested'].items()}
try:
    key(['--scan', '0x35'])
    assert wait_state((6, 0)), 'Did not resume ordinary gameplay'
    scans = {'left': 0x14b, 'right': 0x14d, 'up': 0x148, 'down': 0x150, 'jump': 0x2d, 'dash': 0x2c, 'fire': 0x2e}
    keys = [scans[k] for k in a.keys]
    args = ['--scan', str(keys[0] & 127), '--hold', str(a.hold)]
    if keys[0] & 0x100:
        args.append('--extended')
    for k in keys[1:]:
        args.extend(['--also-scan', str(k)])
    result['action_capture'] = key(args)['capture']
    key(['--scan', '0x35'])
    result['paused_after'] = wait_state((6, 2))
    result['engine_state_after'] = state()
    result['hp_after'] = proc.read(a.ram_base + 0x1418c8 + 0x5c, 1)[0]
finally:
    proc.close()
    a.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', 'utf8')
print(json.dumps({k: result.get(k) for k in ('action_capture', 'paused_after', 'engine_state_after', 'hp_after')}))
