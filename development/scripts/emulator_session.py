"""제공된 ePSXe 작업 사본의 실행·전면 전환·제한된 키 입력·창 캡처. Windows 전용."""
import argparse
import ctypes
from ctypes import wintypes
import json
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts.project import digest,new_run,write_json
from scripts.emulator_probe import Input,KeyInput

EXE_HASH='a266ee19bbeba0da38ffbaa8b02b89fe2524af7a45a13ea9ff37feab7423986d'
EMULATOR=ROOT/'work/ver_buki_riko/baseline/20261023T054951214649Z/emulator/ePSXe.exe'


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


def checked_window(pid):
    user,kernel=windows()
    handle=kernel.OpenProcess(0x1000,False,pid)
    if not handle:raise ctypes.WinError(ctypes.get_last_error())
    try:
        path=ctypes.create_unicode_buffer(32768);size=wintypes.DWORD(len(path))
        if not kernel.QueryFullProcessImageNameW(handle,0,path,ctypes.byref(size)):
            raise ctypes.WinError(ctypes.get_last_error())
    finally:kernel.CloseHandle(handle)
    if Path(path.value).resolve()!=EMULATOR.resolve() or digest(EMULATOR)!=EXE_HASH:
        raise ValueError('Only the verified working emulator copy may be controlled')
    found=[]
    callback_type=ctypes.WINFUNCTYPE(wintypes.BOOL,wintypes.HWND,wintypes.LPARAM)
    @callback_type
    def callback(hwnd,_):
        actual=wintypes.DWORD();user.GetWindowThreadProcessId(hwnd,ctypes.byref(actual))
        title=ctypes.create_unicode_buffer(256);user.GetWindowTextW(hwnd,title,256)
        if actual.value==pid and title.value=='ePSXe - Enhanced PSX emulator':found.append(hwnd)
        return True
    user.EnumWindows(callback,0)
    if len(found)!=1:raise ValueError('Expected exactly one emulator window')
    return user,found[0]


def working_instances(include_original=False):
    """작업 사본을 조회. 새 실행 전에는 제공된 원래 EXE도 조회해 중복 창을 방지한다."""
    import csv
    _, kernel = windows()
    result = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq ePSXe.exe', '/FO', 'CSV', '/NH'],
                            capture_output=True, text=True, check=True)
    found = []
    allowed = {EMULATOR.resolve()}
    if include_original:
        allowed.add((ROOT/'ePSXe2018/ePSXe.exe').resolve())
    for row in csv.reader(result.stdout.splitlines()):
        if len(row) < 2 or row[0].lower() != 'epsxe.exe' or not row[1].isdigit():
            continue
        pid = int(row[1]); handle = kernel.OpenProcess(0x1000, False, pid)
        if not handle: continue
        try:
            path = ctypes.create_unicode_buffer(32768); size = wintypes.DWORD(len(path))
            if kernel.QueryFullProcessImageNameW(handle, 0, path, ctypes.byref(size)) and Path(path.value).resolve() in allowed:
                found.append(pid)
        finally:
            kernel.CloseHandle(handle)
    return found


def main():
    global EMULATOR
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--project',choices=['ver_buki_riko','ver_rin_nana'],default='ver_buki_riko')
    p.add_argument('action',choices=['launch','capture','key','close'])
    p.add_argument('--cue',type=Path)
    p.add_argument('--session',type=Path)
    p.add_argument('--scan',type=lambda x:int(x,0))
    p.add_argument('--also-scan',type=lambda x:int(x,0),action='append',default=[],
                   help='동시 입력. 확장 키는 scan code에0x100을 더한다.')
    p.add_argument('--extended',action='store_true')
    p.add_argument('--hold',type=float,default=0.12)
    p.add_argument('--card0',type=Path)
    p.add_argument('--card1',type=Path)
    args=p.parse_args()
    project=args.project
    if project=='ver_rin_nana':EMULATOR=ROOT/'work/ver_rin_nana/emulator/ePSXe.exe'
    if args.action=='launch':
        running = working_instances(include_original=True)
        if running:
            raise RuntimeError(f'Provided emulator already running: {running}; use its session or close it first')
        if not args.cue:raise ValueError('CUE required')
        cue=args.cue.resolve()
        if not cue.is_relative_to((ROOT/'out'/project).resolve()) or cue.suffix.lower()!='.cue' or not cue.is_file():
            raise ValueError('Expected an existing first-project output CUE')
        manifest=json.loads((cue.parent/'manifest.json').read_text(encoding='utf-8'))
        import re
        match=re.match(r'FILE "([^"\r\n]+)" BINARY',cue.read_text(encoding='ascii'))
        if not match or Path(match[1]).name!=match[1]:raise ValueError('Unsupported CUE file reference')
        game=(cue.parent/match[1]).resolve()
        if game.parent!=cue.parent or digest(game)!=manifest['modified_bin']['sha256']:
            raise ValueError('Build image hash mismatch')
        if digest(EMULATOR)!=EXE_HASH:raise ValueError('Unexpected emulator binary')
        env=os.environ.copy();env['__COMPAT_LAYER']='WIN7RTM'
        startup=subprocess.STARTUPINFO();startup.dwFlags|=subprocess.STARTF_USESHOWWINDOW;startup.wShowWindow=0
        command=[str(EMULATOR),'-nogui','-loadiso',str(cue)];cards={}
        for index,path in enumerate((args.card0,args.card1)):
            if path is None:continue
            path=path.resolve()
            if not path.is_relative_to((ROOT/'work'/project).resolve()) or path.suffix.lower()!='.mcr' or path.stat().st_size!=131072 or path.parent==EMULATOR.parent/'memcards':raise ValueError('Expected isolated test memory card')
            command.extend([f'-loadmemc{index}',str(path)]);cards[str(index)]={'path':str(path),'sha256':digest(path)}
        process=subprocess.Popen(command,cwd=EMULATOR.parent,env=env,startupinfo=startup)
        out=new_run(ROOT,project,'emulator_sessions')
        write_json(out/'session.local.json',{'pid':process.pid,'executable':str(EMULATOR),'exe_sha256':EXE_HASH,
                                           'cue':str(cue),'bin_sha256':manifest['modified_bin']['sha256'],'save_state_loaded':False,'memory_card_overrides':cards})
        print(json.dumps({'session':str(out),'pid':process.pid}));return
    if not args.session:raise ValueError('Session required')
    session=args.session.resolve()
    if not session.is_relative_to((ROOT/'work'/project/'emulator_sessions').resolve()):raise ValueError('Unexpected session')
    record=json.loads((session/'session.local.json').read_text(encoding='utf-8'))
    user,hwnd=checked_window(record['pid'])
    user.ShowWindowAsync(hwnd,9);user.SetForegroundWindow(hwnd);time.sleep(0.2)
    if user.GetForegroundWindow()!=hwnd:raise RuntimeError('Emulator not focused; no key or screenshot')
    if args.action=='close':
        # -nogui로 시작한 이 사본은 Escape로 종료됨을 로컬 실행에서 확인했다.
        args.scan=0x01;args.extended=False;args.hold=0.12;args.also_scan=[]
    if args.action in ('key','close'):
        if args.scan is None or not 1<=args.scan<=0x7f or not 0.02<=args.hold<=2:
            raise ValueError('Invalid scan code or hold duration')
        chord=[(args.scan,args.extended)]+[(s&255,bool(s&0x100)) for s in args.also_scan]
        if len(chord)>4 or len(set(chord))!=len(chord) or any(s<1 or s>0x7f for s,_ in chord) or any(s&~0x17f for s in args.also_scan):
            raise ValueError('Invalid simultaneous keys')
        pressed=[]
        try:
            for scan,extended in chord:
                event=Input();event.type=1;event.data.key=KeyInput(0,scan,8|int(extended),0,0)
                if user.SendInput(1,ctypes.byref(event),ctypes.sizeof(event))!=1:raise RuntimeError('Key down failed')
                pressed.append(event)
            time.sleep(args.hold)
        finally:
            released=True
            for event in reversed(pressed):
                event.data.key.flags|=2
                released=(user.SendInput(1,ctypes.byref(event),ctypes.sizeof(event))==1) and released
            if not released:raise RuntimeError('Key release failed')
        time.sleep(0.3)
    if args.action=='close':
        deadline=time.monotonic()+3
        while time.monotonic()<deadline and record['pid'] in working_instances():
            time.sleep(0.2)
        exited=record['pid'] not in working_instances()
        write_json(session/'close.local.json',{'pid':record['pid'],'escape_sent':True,'exited':exited})
        print(json.dumps({'pid':record['pid'],'exited':exited}))
        if not exited: raise RuntimeError('Emulator did not exit; no forced termination performed')
        return
    if user.GetForegroundWindow()!=hwnd:raise RuntimeError('Focus changed; capture skipped')
    from PIL import ImageGrab
    from datetime import datetime,timezone
    rect=wintypes.RECT();point=wintypes.POINT()
    user.GetClientRect(hwnd,ctypes.byref(rect));user.ClientToScreen(hwnd,ctypes.byref(point))
    if rect.right<=0 or rect.bottom<=0:raise ValueError('Empty client area')
    picture=ImageGrab.grab(bbox=(point.x,point.y,point.x+rect.right,point.y+rect.bottom))
    name=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    path=session/(name+'.png')
    with path.open('xb') as stream:picture.save(stream,format='PNG')
    write_json(session/(name+'.json'),{'action':args.action,'pid':record['pid'],'hwnd':hwnd,'scan':args.scan,
                                     'extended':args.extended,'hold':args.hold if args.action=='key' else 0,'capture':str(path)})
    print(json.dumps({'pid':record['pid'],'hwnd':hwnd,'capture':str(path)}))


if __name__=='__main__':main()
