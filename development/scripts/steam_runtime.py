"""Control only the verified RXC1 game window; screenshots and bounded key input."""
import argparse
import ctypes
from ctypes import wintypes
import hashlib
import json
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts.emulator_session import windows
from scripts.emulator_probe import Input, KeyInput
from src.steam_executable import validate_executable
EXE = Path('C:/Program Files (x86)/Steam/steamapps/common/Mega Man X Legacy Collection/RXC1.exe')
HASH = '8c549623ce4f010ee0b3c23b17fe1ea52d3bc2acfcac9be9b0ecf374cfaa6949'


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


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('action',choices=['capture','keys','close'])
    p.add_argument('--out',type=Path)
    p.add_argument('--scan',type=lambda x:int(x,0),default=0x1c)
    p.add_argument('--hold',type=float,default=.12)
    p.add_argument('--count',type=int,default=1)
    p.add_argument('--interval',type=float,default=.3)
    p.add_argument('--settle',type=float,default=.5)
    p.add_argument('--passive',action='store_true')
    a=p.parse_args()
    if not 0<=a.hold<=10 or not 1<=a.count<=20 or not 0<=a.settle<=10:raise ValueError('Bounded input only')
    ctypes.windll.user32.SetProcessDPIAware()
    user,(hwnd,pid,title)=game_window()
    if a.passive and a.action!='capture':raise ValueError('Passive mode is capture only')
    if not a.passive:
        user.ShowWindowAsync(hwnd,9);user.SetForegroundWindow(hwnd);time.sleep(.2)
    user.SendInput.argtypes=[wintypes.UINT,ctypes.POINTER(Input),ctypes.c_int]
    def send(scan,down):
        ev=Input(type=1)
        ev.data.key=KeyInput(0,scan,0x8|(0 if down else 2)|(1 if scan in (0x48,0x50,0x4b,0x4d) else 0),0,0)
        if user.SendInput(1,ctypes.byref(ev),ctypes.sizeof(ev))!=1:raise ctypes.WinError()
    if not a.passive and user.GetForegroundWindow()!=hwnd:
        send(0x38,True);send(0x38,False);user.SetForegroundWindow(hwnd);time.sleep(.2)
    if not a.passive and user.GetForegroundWindow()!=hwnd:raise ValueError('Game focus not acquired')
    if a.action=='close':
        kernel=windows()[1]
        kernel.WaitForSingleObject.argtypes=[wintypes.HANDLE,wintypes.DWORD]
        kernel.WaitForSingleObject.restype=wintypes.DWORD
        handle=kernel.OpenProcess(0x100000,False,pid)
        if not handle:raise ctypes.WinError(ctypes.get_last_error())
        user.PostMessageW(hwnd,0x10,0,0)
        try:
            if kernel.WaitForSingleObject(handle,10000)!=0:raise ValueError('Game has not completed shutdown')
        finally:kernel.CloseHandle(handle)
        print(json.dumps({'pid':pid,'action':'WM_CLOSE'}));return
    if a.action=='keys':
        for _ in range(a.count):
            if user.GetForegroundWindow()!=hwnd:raise ValueError('Lost focus')
            try:send(a.scan,True);time.sleep(a.hold)
            finally:send(a.scan,False)
            time.sleep(a.interval)
    time.sleep(a.settle)
    if a.out:
        from PIL import ImageGrab
        if not a.out.resolve().is_relative_to(ROOT/'work'):raise ValueError('Capture outside work refused')
        rect=wintypes.RECT();point=wintypes.POINT(0,0)
        user.GetClientRect(hwnd,ctypes.byref(rect));user.ClientToScreen(hwnd,ctypes.byref(point))
        img=ImageGrab.grab(bbox=(point.x,point.y,point.x+rect.right,point.y+rect.bottom),all_screens=True)
        a.out.parent.mkdir(parents=True,exist_ok=True);img.save(a.out)
        print(json.dumps({'pid':pid,'title':title,'size':img.size,'out':str(a.out),'action':a.action}))


if __name__=='__main__':main()
