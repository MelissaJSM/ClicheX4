"""검증용 짧은 입력: 메뉴 해제 직후 이동, 화면 확보 직후 다시 일시정지."""
import argparse
import ctypes
import json
from pathlib import Path
import subprocess
import sys
import time
from ctypes import wintypes
from PIL import ImageGrab

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from scripts.observe_sprite_consistency_runtime import ReadOnlyProcess
from scripts.emulator_session import checked_window, Input, KeyInput

p = argparse.ArgumentParser()
p.add_argument('--session', type=Path, required=True)
p.add_argument('--keys', nargs='+', choices=('left', 'right', 'jump', 'dash', 'fire'), required=True)
p.add_argument('--hold', type=float, required=True)
p.add_argument('--output', type=Path, required=True)
a = p.parse_args()
assert .02 <= a.hold <= 2 and len(set(a.keys)) == len(a.keys) <= 4
out = a.output.resolve()
assert not out.exists() and out.is_relative_to(Path(__file__).resolve().parent)
rec = json.loads((a.session / 'session.local.json').read_text('utf8'))
checked = json.loads(subprocess.check_output([sys.executable, str(Path(__file__).with_name('read_menu_br31.py')),
    '--session', str(a.session), '--pid', str(rec['pid']), '--ram-base', '19537440'], text=True, encoding='utf8'))
assert checked['passed'] and checked['project'] == 'ver_buki_riko'
assert (checked['engine']['state'], checked['engine']['substate']) == (6, 2)
user, hwnd = checked_window(rec['pid'])
user.ShowWindowAsync(hwnd, 9)
user.SetForegroundWindow(hwnd)
assert user.GetForegroundWindow() == hwnd
proc = ReadOnlyProcess(rec)
events = []
held = set()
scans = {'left': 0x14b, 'right': 0x14d, 'jump': 0x2d, 'dash': 0x2c, 'fire': 0x2e, 'start': 0x35}
started = time.monotonic()
result = {'session': str(a.session), 'bin_sha256': rec['bin_sha256'], 'events': events,
          'memory_written': False, 'F1_F3_sent': False, 'keys': a.keys, 'hold': a.hold}

def state():
    return tuple(proc.read(19537440 + 0x1721c0, 2))

def send(name, down):
    if down:
        assert user.GetForegroundWindow() == hwnd, 'Focus changed'
    scan = scans[name]
    event = Input()
    event.type = 1
    event.data.key = KeyInput(0, scan & 127, 8 | int(bool(scan & 256)) | (0 if down else 2), 0, 0)
    assert user.SendInput(1, ctypes.byref(event), ctypes.sizeof(event)) == 1
    (held.add if down else held.discard)(name)
    events.append({'at': time.monotonic() - started, 'key': name, 'down': down})

def start_tap():
    send('start', True)
    time.sleep(.05)
    send('start', False)

def until(target):
    stop = time.monotonic() + 4
    while time.monotonic() < stop:
        if state() == target:
            return True
        time.sleep(.002)
    return False

try:
    start_tap()
    assert until((6, 0)), 'Resume did not complete'
    result['resumed_at'] = time.monotonic() - started
    for name in a.keys:
        send(name, True)
    stop = time.monotonic() + a.hold
    while time.monotonic() < stop:
        assert user.GetForegroundWindow() == hwnd
        time.sleep(.003)
    for name in list(held):
        send(name, False)
    rect, point = wintypes.RECT(), wintypes.POINT()
    user.GetClientRect(hwnd, ctypes.byref(rect))
    user.ClientToScreen(hwnd, ctypes.byref(point))
    im = ImageGrab.grab(bbox=(point.x, point.y, point.x + rect.right, point.y + rect.bottom)).convert('RGB')
    result['captured_at'] = time.monotonic() - started
    start_tap()
    result['paused_after'] = until((6, 2))
    result['engine_state_after'] = state()
    result['hp_after'] = proc.read(19537440 + 0x1418c8 + 0x5c, 1)[0]
    im.save(out.with_suffix('.png'))
    result['action_capture'] = str(out.with_suffix('.png'))
finally:
    for name in list(held):
        send(name, False)
    result['keys_released'] = not held
    proc.close()
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', 'utf8')
print(json.dumps({k: result.get(k) for k in ('action_capture', 'paused_after', 'hp_after', 'resumed_at', 'captured_at')}))
