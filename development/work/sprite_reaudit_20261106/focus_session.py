"""검증된 이번 세션 창에만 포커스를 요청한다. 게임 입력·메모리 쓰기 없음."""
import argparse
import ctypes
from ctypes import wintypes
import json
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from scripts import emulator_session as control

parser = argparse.ArgumentParser()
parser.add_argument('session', type=Path)
args = parser.parse_args()
session = args.session.resolve()
projects = [m for m in ('ver_buki_riko', 'ver_rin_nana') if session.is_relative_to(ROOT / 'work' / m / 'emulator_sessions')]
assert len(projects) == 1
if projects[0] == 'ver_rin_nana':
    control.EMULATOR = ROOT / 'work/ver_rin_nana/emulator/ePSXe.exe'
rec = json.loads((session / 'session.local.json').read_text('utf8'))
user, hwnd = control.checked_window(rec['pid'])
kernel = ctypes.WinDLL('kernel32', use_last_error=True)
kernel.GetCurrentThreadId.restype = wintypes.DWORD
user.GetWindowThreadProcessId.restype = wintypes.DWORD
user.AttachThreadInput.argtypes = [wintypes.DWORD, wintypes.DWORD, wintypes.BOOL]
user.SetFocus.argtypes = [wintypes.HWND]
user.BringWindowToTop.argtypes = [wintypes.HWND]
current_thread = kernel.GetCurrentThreadId()
foreground = user.GetForegroundWindow()
fg_thread = user.GetWindowThreadProcessId(foreground, None) if foreground else 0
target_thread = user.GetWindowThreadProcessId(hwnd, None)
attached = []
try:
    for thread in sorted({fg_thread, target_thread} - {0, current_thread}):
        if user.AttachThreadInput(current_thread, thread, True):
            attached.append(thread)
    user.ShowWindowAsync(hwnd, 9)
    user.BringWindowToTop(hwnd)
    user.SetForegroundWindow(hwnd)
    user.SetFocus(hwnd)
finally:
    for thread in reversed(attached):
        user.AttachThreadInput(current_thread, thread, False)
time.sleep(.3)
passed = user.GetForegroundWindow() == hwnd
print(json.dumps({'pid': rec['pid'], 'focused': passed, 'keys_sent': False, 'memory_written': False}))
if not passed:
    raise RuntimeError('Foreground request refused; no input sent')
