"""Windows distribution entry point; staged with release_paths and release_config."""
import argparse
import csv
import ctypes
from ctypes import wintypes
import importlib
import json
import os
from pathlib import Path
import queue
import re
import shutil
import subprocess
import sys
import threading
import time
import traceback
import winreg

from src.steam_distribution import Package, atomic_write, digest, json_bytes
import release_paths
from release_config import PATCH_SHA256, RELEASE, RUNTIME_MODULES

BUNDLE = Path(getattr(sys, '_MEIPASS', Path(__file__).parent))
HOME = Path(sys.executable).parent if getattr(sys, 'frozen', False) else Path(__file__).parent
LOCAL = Path(os.environ['LOCALAPPDATA']) / 'ClicheX4'
PREFS = LOCAL / 'settings.json'
FLAGS = subprocess.CREATE_NO_WINDOW


def steam_path():
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r'Software\Valve\Steam') as k:
            return Path(winreg.QueryValueEx(k, 'SteamPath')[0])
    except OSError:
        return Path(os.environ.get('ProgramFiles(x86)', 'C:/Program Files (x86)')) / 'Steam'


def discover():
    candidates = []
    if PREFS.exists():
        try:candidates.append(Path(json.loads(PREFS.read_text('utf8'))['game_dir']))
        except (ValueError, KeyError):pass
    base = steam_path()
    libraries = [base]
    vdf = base / 'steamapps/libraryfolders.vdf'
    if vdf.exists():
        libraries += [Path(p.replace('\\\\', '\\')) for p in re.findall(r'"path"\s+"([^"]+)"', vdf.read_text('utf8'))]
    candidates += [p / 'steamapps/common/Mega Man X Legacy Collection' for p in libraries]
    return next((p for p in candidates if (p/'RXC1.exe').is_file()), candidates[0])


def running():
    p = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq RXC1.exe', '/FO', 'CSV', '/NH'],
                       capture_output=True, creationflags=FLAGS, check=True)
    return any(row and row[0].lower() == 'rxc1.exe' for row in csv.reader(p.stdout.decode('mbcs', errors='replace').splitlines()))


def creation_token(pid):
    k = ctypes.WinDLL('kernel32', use_last_error=True)
    k.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    k.OpenProcess.restype = wintypes.HANDLE
    k.GetProcessTimes.argtypes = [wintypes.HANDLE] + [ctypes.POINTER(wintypes.FILETIME)] * 4
    k.CloseHandle.argtypes = [wintypes.HANDLE]
    h = k.OpenProcess(0x1000, False, pid)
    if not h:raise ctypes.WinError(ctypes.get_last_error())
    times = [wintypes.FILETIME() for _ in range(4)]
    try:
        if not k.GetProcessTimes(h, *[ctypes.byref(t) for t in times]):raise ctypes.WinError(ctypes.get_last_error())
        return f'{pid}_{times[0].dwHighDateTime:08x}{times[0].dwLowDateTime:08x}'
    finally:k.CloseHandle(h)


def apply_runtime(root, progress):
    release_paths.EXE = root / 'RXC1.exe'
    # Every invocation uses the current selected installation, including repeated
    # GUI launches. Allocation records are scoped to PID AND process creation.
    for name in ['scripts.steam_runtime'] + ['scripts.'+m for m in RUNTIME_MODULES]:
        sys.modules.pop(name, None)
    rt = importlib.import_module('scripts.steam_runtime')
    deadline = time.monotonic() + 45
    while True:
        try:
            _, (_, pid, title) = rt.game_window()
            if title != 'Mega Man X Legacy Collection / ROCKMAN X ANNIVERSARY COLLECTION':
                raise ValueError('게임 초기화 대기 중')
            break
        except (OSError, ValueError):
            if time.monotonic() >= deadline:raise ValueError('게임 창을 찾지 못했습니다. Steam 로그인과 실행 상태를 확인해 주세요.')
            time.sleep(.5)
    session = LOCAL / 'sessions' / RELEASE / creation_token(pid)
    release_paths.ROOT = session
    work = session / 'work/steam_port_20261109'
    for source in (BUNDLE/'runtime_specs').rglob('*.json'):
        dest = work / source.relative_to(BUNDLE/'runtime_specs')
        atomic_write(dest, source.read_bytes())
    (work/'runtime').mkdir(parents=True, exist_ok=True)
    results = {}
    # This Windows file lock also prevents two launchers racing hook allocation.
    with package().lock(session):
        for i, name in enumerate(RUNTIME_MODULES):
            progress(i, len(RUNTIME_MODULES), '게임 표시·음향 보정')
            mod = importlib.import_module('scripts.'+name)
            result = mod.apply()
            if result.get('active') is False:raise ValueError('필수 실행 보정이 적용되지 않았습니다: '+name)
            results[name] = result
            atomic_write(work/'runtime/launcher_result.json', json_bytes(results))
    return {'action': 'launch', 'pid': pid, 'runtime_checks': results, 'save_files_written': False, 'exe_written': False}


def package():
    return Package(HOME/'patches.zip', PATCH_SHA256)


def action(which, root, progress=lambda *_: None):
    root = Path(root).resolve()
    pkg = package()
    if which == 'verify':return pkg.inspect(root, progress)
    if which in ('install', 'restore'):
        return pkg.apply(root, restore=which=='restore', progress=progress, running=running)
    check = pkg.inspect(root, progress)
    if check['installed'] != check['total']:
        raise ValueError('먼저 패치를 설치해 주세요. 다른 버전/손상된 파일이 있으면 파일 확인 결과를 확인해 주세요.')
    if not running():
        steam = steam_path()/'steam.exe'
        if steam.exists():subprocess.Popen([str(steam), '-applaunch', '743890'], creationflags=FLAGS)
        else:os.startfile('steam://rungameid/743890')
    progress(0, 7, 'Steam 게임 시작 대기')
    return apply_runtime(root, progress)


def gui():
    import tkinter as tk
    from tkinter import ttk, filedialog, messagebox
    window = tk.Tk()
    window.title('ClichéX4 · 스텔라이브 팬 모드 '+RELEASE)
    window.geometry('760x490')
    window.minsize(700, 470)
    font = ('맑은 고딕', 10)
    ttk.Style().configure('.', font=font)
    outer = ttk.Frame(window, padding=22);outer.pack(fill='both', expand=True)
    ttk.Label(outer, text='ClichéX4', font=('맑은 고딕', 25, 'bold')).pack(anchor='w')
    ttk.Label(outer, text='스텔라이브 팬 모드 · Steam 레거시 컬렉션 1', font=('맑은 고딕', 12)).pack(anchor='w', pady=(0, 12))
    ttk.Label(outer, text='Japanese edition → 하나코 나나 / 아오쿠모 린\nEnglish (US) edition → 텐코 시부키 / 유즈하 리코').pack(anchor='w')
    ttk.Label(outer, text='게임 폴더 (RXC1.exe가 있는 폴더)').pack(anchor='w', pady=(15, 4))
    path = tk.StringVar(value=str(discover()))
    row = ttk.Frame(outer);row.pack(fill='x')
    entry = ttk.Entry(row, textvariable=path);entry.pack(side='left', fill='x', expand=True)
    def browse():
        chosen = filedialog.askdirectory(title='레거시 컬렉션 1 게임 폴더 선택', initialdir=path.get())
        if chosen:path.set(chosen)
    pick = ttk.Button(row, text='폴더 선택', command=browse);pick.pack(side='left', padx=(8, 0))
    status = tk.StringVar(value='처음에는 패치 설치, 다음부터는 모드 실행을 눌러 주세요.')
    ttk.Label(outer, textvariable=status, wraplength=690).pack(anchor='w', pady=(15, 6))
    bar = ttk.Progressbar(outer, maximum=100);bar.pack(fill='x')
    buttons = ttk.Frame(outer);buttons.pack(fill='x', pady=15)
    events = queue.Queue();busy = [False];controls = [entry, pick]
    def start(which):
        if busy[0]:return
        if which=='restore' and not messagebox.askyesno('원본 복원', '모드 자원을 설치 전 원본으로 복원합니다. 계속할까요?\n게임 저장 데이터는 변경하지 않습니다.'):return
        busy[0]=True
        for b in controls:b.configure(state='disabled')
        selected = path.get()
        status.set('확인 중…')
        def worker():
            try:
                result = action(which, selected, lambda n,t,label:events.put(('progress', (n,t,label))))
                atomic_write(PREFS, json_bytes({'game_dir': str(Path(selected).resolve())}))
                events.put(('done', result))
            except Exception as e:
                LOCAL.mkdir(parents=True, exist_ok=True)
                (LOCAL/'last_error.txt').write_text(traceback.format_exc(), encoding='utf8')
                events.put(('error', str(e)))
        threading.Thread(target=worker, daemon=True).start()
    for label, which in [('패치 설치','install'),('모드 실행','launch'),('파일 확인','verify'),('원본 복원','restore')]:
        b = ttk.Button(buttons, text=label, command=lambda w=which:start(w));b.pack(side='left', padx=(0,8));controls.append(b)
    ttk.Label(outer, text='게임 안에서 X 키 / 표시된 버튼으로 Japanese ↔ English (US)를 전환합니다.\n플레이할 때마다 이 실행기의 「모드 실행」을 사용해 주세요.\n설치·복원 시에는 게임을 종료해 주세요.', wraplength=690).pack(anchor='w')
    def poll():
        try:
            while True:
                kind, value = events.get_nowait()
                if kind=='progress':
                    n,t,label=value;bar['value']=100*n/max(t,1);status.set(f'{label} · {n}/{t}')
                else:
                    busy[0]=False
                    for b in controls:b.configure(state='normal')
                    if kind=='error':
                        status.set('완료하지 못했습니다. 아래 오류를 확인해 주세요.')
                        messagebox.showerror('ClichéX4', value+'\n\n자세한 기록: '+str(LOCAL/'last_error.txt'))
                    else:
                        bar['value']=100
                        if 'conflicts' in value:
                            common=value['unchanged']
                            status.set(f"패치 {value['installed']-common} / 원본 {value['original']-common} / 공통 {common} / 충돌 {len(value['conflicts'])} · 전체 {value['total']}개")
                            if value['conflicts']:messagebox.showwarning('파일 확인', '\n'.join(value['conflicts'][:12]))
                        elif value['action']=='launch':status.set('실행 보정 완료. 게임 창에서 플레이해 주세요. 실행기는 닫아도 됩니다.')
                        elif value['action']=='install':status.set('설치 확인 완료. 모드 실행을 눌러 주세요.')
                        else:status.set('원본 복원 완료. 백업은 게임 폴더의 .clichex4에 보관됩니다.')
        except queue.Empty:pass
        window.after(100, poll)
    def close():
        if busy[0]:messagebox.showinfo('작업 중', '파일 작업이 끝난 뒤 닫아 주세요.')
        else:window.destroy()
    window.protocol('WM_DELETE_WINDOW', close);poll();window.mainloop()


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--action', choices=['verify','install','restore','launch'])
    p.add_argument('--game-dir', type=Path)
    p.add_argument('--report', type=Path)
    a = p.parse_args()
    if not a.action:return gui()
    try:
        report={'ok':True, 'result': action(a.action, a.game_dir or discover())};code=0
    except Exception as e:report={'ok':False, 'error':str(e), 'traceback':traceback.format_exc()};code=1
    if a.report:atomic_write(a.report, json_bytes(report))
    elif sys.stdout:print(json.dumps(report, ensure_ascii=False))
    return code


if __name__=='__main__':sys.exit(main())
