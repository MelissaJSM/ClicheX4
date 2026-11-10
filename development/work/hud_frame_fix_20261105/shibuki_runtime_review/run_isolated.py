"""시부키 HUD 실제 촬영용 격리 ePSXe. 기존 상태/카드에는 쓰지 않는다."""
import argparse
import ctypes
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
from ctypes import wintypes
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from scripts.hud_underlay_verify import digest
from scripts import emulator_session as control

OUT = Path(__file__).resolve().parent
TEMPLATE = ROOT/'work/ver_buki_riko/baseline/20261023T054951214649Z/emulator'
EXE = OUT/'emulator/ePSXe.exe'
CUE = ROOT/'out/ver_buki_riko/hud_reference_details_20261105_v8/shibuki_riko.cue'
GAME_SHA = '92ab09adf0284c0581a6993c88f64b2348f4e2bdc886e4ca9df1e1bc8c2bdb50'
NANA_SESSION = ROOT/'work/ver_rin_nana/emulator_sessions/20261105T003459094056Z'


def original_files():
    result = {}
    for base in (TEMPLATE, ROOT/'work/ver_rin_nana/emulator', ROOT/'ePSXe2018'):
        for sub in ('memcards','sstates'):
            folder = base/sub
            if folder.exists():
                for p in sorted(folder.rglob('*')):
                    if p.is_file():
                        result[p.relative_to(ROOT).as_posix()] = {'sha256': digest(p), 'size': p.stat().st_size}
    return result


def focus(pid, exe):
    control.EMULATOR = exe
    user, hwnd = control.checked_window(pid)
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    kernel.GetCurrentThreadId.restype = wintypes.DWORD
    user.AttachThreadInput.argtypes = [wintypes.DWORD,wintypes.DWORD,wintypes.BOOL]
    user.BringWindowToTop.argtypes = [wintypes.HWND]
    user.SetFocus.argtypes = [wintypes.HWND]
    current = kernel.GetCurrentThreadId()
    target_thread = user.GetWindowThreadProcessId(hwnd, None)
    foreground = user.GetForegroundWindow()
    foreground_thread = user.GetWindowThreadProcessId(foreground, None)
    attached = []
    try:
        for thread in {target_thread,foreground_thread} - {0,current}:
            if user.AttachThreadInput(current,thread,True):
                attached.append(thread)
        user.ShowWindowAsync(hwnd,9)
        user.BringWindowToTop(hwnd)
        user.SetForegroundWindow(hwnd)
        user.SetFocus(hwnd)
    finally:
        for thread in reversed(attached):
            user.AttachThreadInput(current,thread,False)
    time.sleep(.2)
    if user.GetForegroundWindow() != hwnd:
        raise RuntimeError('Focus did not move; no keyboard events sent')
    return hwnd


def launch():
    assert digest(CUE.with_suffix('.bin')) == GAME_SHA
    assert digest(TEMPLATE/'ePSXe.exe') == control.EXE_HASH
    assert not EXE.parent.exists(), 'Isolated emulator already exists'
    original = original_files()
    (OUT/'preservation_before.json').write_text(json.dumps(original,indent=2)+'\n','utf8')
    EXE.parent.mkdir()
    for filename in ('ePSXe.exe','burutter.dll'):
        shutil.copy2(TEMPLATE/filename,EXE.parent/filename)
    for dirname in ('bios','plugins','config','shaders'):
        shutil.copytree(TEMPLATE/dirname,EXE.parent/dirname)
    for dirname in ('memcards','sstates','snap','cheats','patches','idx','info','covers'):
        (EXE.parent/dirname).mkdir(exist_ok=True)
    cards=[]
    for filename in ('epsxe000.mcr','epsxe001.mcr'):
        target=EXE.parent/'memcards'/filename
        shutil.copy2(TEMPLATE/'memcards'/filename,target)
        cards.append(target)
    assert not list((EXE.parent/'sstates').iterdir())
    env=os.environ.copy();env['__COMPAT_LAYER']='WIN7RTM'
    startup=subprocess.STARTUPINFO();startup.dwFlags|=subprocess.STARTF_USESHOWWINDOW;startup.wShowWindow=0
    command=[str(EXE),'-nogui','-loadiso',str(CUE),'-loadmemc0',str(cards[0]),'-loadmemc1',str(cards[1])]
    process=subprocess.Popen(command,cwd=EXE.parent,env=env,startupinfo=startup)
    stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    session=ROOT/'work/ver_buki_riko/emulator_sessions'/(stamp+'_isolated_shibuki_hud')
    session.mkdir()
    record={'pid':process.pid,'executable':str(EXE),'exe_sha256':control.EXE_HASH,'cue':str(CUE),'bin_sha256':GAME_SHA,'save_state_loaded':False,'fresh_boot':True,'isolated_sstates':str(EXE.parent/'sstates'),'memory_card_overrides':{str(i):{'path':str(p),'sha256':digest(p)}for i,p in enumerate(cards)},'command':command}
    (session/'session.local.json').write_text(json.dumps(record,indent=2)+'\n','utf8')
    (OUT/'session.json').write_text(json.dumps({'session':str(session),'pid':process.pid},indent=2)+'\n','utf8')
    assert original_files()==original
    print(json.dumps({'session':str(session),'pid':process.pid,'original_state_and_card_files_preserved':len(original)}))


def run(action, scan=None, hold=.12, extended=False):
    saved=json.loads((OUT/'session.json').read_text('utf8'))
    session=Path(saved['session'])
    if action=='restore_focus':
        nana=json.loads((NANA_SESSION/'session.local.json').read_text('utf8'))
        hwnd=focus(nana['pid'],Path(nana['executable']))
        print(json.dumps({'focused_existing_nana_pid':nana['pid'],'hwnd':hwnd,'keys_sent':False}))
        return
    if action=='audit':
        before=json.loads((OUT/'preservation_before.json').read_text('utf8'))
        after=original_files();ok=before==after
        report={'passed':ok,'protected_original_files':len(before),'before':before,'after':after,'F1_or_F3_sent':False,'original_cards_used_by_test':False,'state_folder_was_empty':True,'isolated_state_files':[p.name for p in (EXE.parent/'sstates').iterdir()]}
        (OUT/'preservation_after.json').write_text(json.dumps(report,indent=2)+'\n','utf8')
        print(json.dumps({'passed':ok,'protected_original_files':len(before)}))
        assert ok
        return
    if action=='dump':
        control.EMULATOR=EXE
        from scripts.capture_korean_runtime import main
        main(session,'shibuki_v8_actual_HUD',project='ver_buki_riko')
        return
    focus(saved['pid'],EXE)
    if action=='key':
        assert scan not in (0x3b,0x3c,0x3d), 'Save/load/state selection keys forbidden'
    control.EMULATOR=EXE
    sys.argv=['emulator_session.py',action,'--session',str(session)]
    if scan is not None:sys.argv.extend(['--scan',hex(scan),'--hold',str(hold)])
    if extended:sys.argv.append('--extended')
    control.main()


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['launch','capture','key','close','dump','restore_focus','audit']);p.add_argument('--scan',type=lambda x:int(x,0));p.add_argument('--hold',type=float,default=.12);p.add_argument('--extended',action='store_true');a=p.parse_args()
    if a.action=='launch':launch()
    else:run(a.action,a.scan,a.hold,a.extended)
