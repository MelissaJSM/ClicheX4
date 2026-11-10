"""실제 타이틀 로고가 보일 때만 Cross를 눌러 자동 데모를 피한다."""
import ctypes,json,runpy,sys,time
from ctypes import wintypes
from pathlib import Path
import numpy as np
from PIL import Image,ImageGrab
ROOT=Path(__file__).resolve().parents[2]
d=runpy.run_path(str(Path(__file__).with_name('runtime_control.py')));m=d['m']
s=json.loads((m.OUT/'session.json').read_text('utf8'));session=Path(s['session'])
m.focus(s['pid'],m.EXE);u,hwnd=m.control.checked_window(s['pid'])
rect=wintypes.RECT();pt=wintypes.POINT();u.GetClientRect(hwnd,ctypes.byref(rect));u.ClientToScreen(hwnd,ctypes.byref(pt))
reference=np.array(Image.open(ROOT/'work/ver_buki_riko/emulator_sessions/20261105T011419744843Z_isolated_shibuki_hud/20261105T011458165723Z.png').convert('RGB'))[100:250,150:650]
if '--boot' in sys.argv:
    time.sleep(15);m.run('key',0x35,hold=.04)
sent=0;deadline=time.monotonic()+35;last=0
while time.monotonic()<deadline:
    assert u.GetForegroundWindow()==hwnd,'Focus changed; no input'
    im=ImageGrab.grab((pt.x,pt.y,pt.x+rect.right,pt.y+rect.bottom));a=np.array(im.convert('RGB'))
    match=float(np.mean(np.all(a[100:250,150:650]==reference,axis=2)))
    if match>.98 and time.monotonic()-last>1.2:
        m.run('key',0x2d,hold=.15);sent+=1;last=time.monotonic()
        if sent>=3:break
    elif sent and match<.2:break
    time.sleep(.15)
m.run('capture');print(json.dumps({'title_cross_presses':sent,'title_logo_match_last':match}))
