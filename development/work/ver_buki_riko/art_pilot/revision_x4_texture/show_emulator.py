"""사용자가 퇴근 후 허용한 기존 ePSXe 창 복원·관찰. 게임 입력은 보내지 않는다."""
import ctypes
from ctypes import wintypes
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time

root = Path(__file__).resolve().parents[4]
user = ctypes.WinDLL('user32', use_last_error=True)
kernel = ctypes.WinDLL('kernel32', use_last_error=True)
user.FindWindowW.argtypes = [wintypes.LPCWSTR, wintypes.LPCWSTR]
user.FindWindowW.restype = wintypes.HWND
user.GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
user.ShowWindowAsync.argtypes = [wintypes.HWND, ctypes.c_int]
user.SetForegroundWindow.argtypes = [wintypes.HWND]
user.GetForegroundWindow.restype = wintypes.HWND
kernel.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
kernel.OpenProcess.restype = wintypes.HANDLE
kernel.QueryFullProcessImageNameW.argtypes = [wintypes.HANDLE, wintypes.DWORD, wintypes.LPWSTR, ctypes.POINTER(wintypes.DWORD)]
kernel.CloseHandle.argtypes = [wintypes.HANDLE]
hwnd = user.FindWindowW(None, 'ePSXe - Enhanced PSX emulator')
if not hwnd:
    raise RuntimeError('Existing ePSXe window not found')
pid = wintypes.DWORD()
user.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
handle = kernel.OpenProcess(0x1000, False, pid.value)
if not handle:
    raise ctypes.WinError(ctypes.get_last_error())
try:
    size = wintypes.DWORD(32768)
    path = ctypes.create_unicode_buffer(size.value)
    if not kernel.QueryFullProcessImageNameW(handle, 0, path, ctypes.byref(size)):
        raise ctypes.WinError(ctypes.get_last_error())
finally:
    kernel.CloseHandle(handle)
exe = Path(path.value).resolve()
assert exe == (root/'ePSXe2018/ePSXe.exe').resolve()
assert hashlib.sha256(exe.read_bytes()).hexdigest() == 'a266ee19bbeba0da38ffbaa8b02b89fe2524af7a45a13ea9ff37feab7423986d'
user.ShowWindowAsync(hwnd, 9)
requested = bool(user.SetForegroundWindow(hwnd))
time.sleep(0.5)
focused = user.GetForegroundWindow() == hwnd
result = {'pid': pid.value, 'hwnd': hwnd, 'foreground_requested': requested, 'focused': focused,
          'game_input_sent': False, 'game_restarted': False}
if focused:
    capture = subprocess.run([sys.executable, str(root/'scripts/emulator_probe.py'), '--hwnd', str(hwnd),
                              '--output-dir', str(Path(__file__).resolve().parent)], capture_output=True, text=True)
    result.update(capture_exit=capture.returncode, capture_stdout=capture.stdout.strip(), capture_stderr=capture.stderr.strip())
(Path(__file__).parent/'emulator_observation.local.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
print(json.dumps(result))
