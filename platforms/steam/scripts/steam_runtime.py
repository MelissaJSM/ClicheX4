import ctypes
from ctypes import wintypes
from pathlib import Path
from release_paths import EXE
from src.steam_executable import validate_executable

def windows():
    user=ctypes.WinDLL('user32',use_last_error=True)
    kernel=ctypes.WinDLL('kernel32',use_last_error=True)
    user.GetForegroundWindow.restype=wintypes.HWND
    user.GetWindowThreadProcessId.argtypes=[wintypes.HWND,ctypes.POINTER(wintypes.DWORD)]
    user.GetWindowTextW.argtypes=[wintypes.HWND,wintypes.LPWSTR,ctypes.c_int]
    user.ShowWindowAsync.argtypes=[wintypes.HWND,ctypes.c_int]
    user.SetForegroundWindow.argtypes=[wintypes.HWND]
    user.GetClientRect.argtypes=[wintypes.HWND,ctypes.POINTER(wintypes.RECT)]
    user.ClientToScreen.argtypes=[wintypes.HWND,ctypes.POINTER(wintypes.POINT)]
    user.PostMessageW.argtypes=[wintypes.HWND,wintypes.UINT,wintypes.WPARAM,wintypes.LPARAM]
    kernel.OpenProcess.argtypes=[wintypes.DWORD,wintypes.BOOL,wintypes.DWORD]
    kernel.OpenProcess.restype=wintypes.HANDLE
    kernel.QueryFullProcessImageNameW.argtypes=[wintypes.HANDLE,wintypes.DWORD,wintypes.LPWSTR,ctypes.POINTER(wintypes.DWORD)]
    kernel.CloseHandle.argtypes=[wintypes.HANDLE]
    return user,kernel

def game_window():
    user,kernel = windows()
    user.IsWindowVisible.argtypes=[wintypes.HWND]
    found=[]
    callback_type=ctypes.WINFUNCTYPE(wintypes.BOOL,wintypes.HWND,wintypes.LPARAM)
    @callback_type
    def callback(hwnd,_):
        if not user.IsWindowVisible(hwnd):return True
        pid=wintypes.DWORD();user.GetWindowThreadProcessId(hwnd,ctypes.byref(pid))
        handle=kernel.OpenProcess(0x1000,False,pid.value)
        if not handle:return True
        try:
            path=ctypes.create_unicode_buffer(32768);size=wintypes.DWORD(len(path))
            if kernel.QueryFullProcessImageNameW(handle,0,path,ctypes.byref(size)) and Path(path.value).resolve()==EXE.resolve():
                title=ctypes.create_unicode_buffer(512);user.GetWindowTextW(hwnd,title,512)
                found.append((hwnd,pid.value,title.value))
        finally:kernel.CloseHandle(handle)
        return True
    user.EnumWindows(callback,0)
    if len(found)!=1:raise ValueError(f'Expected one RXC1 window; found {found}')
    validate_executable(EXE.read_bytes())
    return user,found[0]
