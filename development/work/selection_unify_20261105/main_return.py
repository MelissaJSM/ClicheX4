"""정식 ePSXe를 타이틀에서 선택창으로 이동. 화면은 메모리 판독만 하고 PNG 저장 안 함."""
import ctypes,importlib.util,json,sys,time
from ctypes import wintypes
from pathlib import Path
import numpy as np
from PIL import Image,ImageGrab
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from scripts import emulator_session as control
from scripts.emulator_probe import Input,KeyInput
spec=importlib.util.spec_from_file_location('isolated_focus',ROOT/'work/hud_frame_fix_20261105/shibuki_runtime_review/run_isolated.py');helper=importlib.util.module_from_spec(spec);spec.loader.exec_module(helper)
session=Path(sys.argv[1]).resolve();assert session.is_relative_to(ROOT/'work/ver_rin_nana/emulator_sessions')
rec=json.loads((session/'session.local.json').read_text('utf8'));exe=ROOT/'work/ver_rin_nana/emulator/ePSXe.exe'
assert rec['executable']==str(exe) and rec['memory_card_overrides']=={}
assert rec['bin_sha256']=='8c5c7ba9bb2fd6d04080db453c2890c6446350fe19b896013661dc97b21b5bc1'
control.EMULATOR=exe;helper.focus(rec['pid'],exe);u,hwnd=control.checked_window(rec['pid'])
rect=wintypes.RECT();pt=wintypes.POINT();u.GetClientRect(hwnd,ctypes.byref(rect));u.ClientToScreen(hwnd,ctypes.byref(pt))
def key(scan,extended=False):
    assert scan in (0x35,0x2d,0x4b) and u.GetForegroundWindow()==hwnd
    e=Input();e.type=1;e.data.key=KeyInput(0,scan,8|int(extended),0,0)
    assert u.SendInput(1,ctypes.byref(e),ctypes.sizeof(e))==1
    try:time.sleep(.06)
    finally:e.data.key.flags|=2;assert u.SendInput(1,ctypes.byref(e),ctypes.sizeof(e))==1
def screen():
    assert u.GetForegroundWindow()==hwnd
    return np.array(ImageGrab.grab((pt.x,pt.y,pt.x+rect.right,pt.y+rect.bottom)).convert('RGB'))
title=np.array(Image.open(ROOT/'work/ver_buki_riko/emulator_sessions/20261105T011419744843Z_isolated_shibuki_hud/20261105T011458165723Z.png').convert('RGB'))[100:250,150:650]
selection=np.array(Image.open(ROOT/'work/selection_unify_20261105/after_runtime/ver_rin_nana.png').convert('RGB'))
boxes=[(165,180,245,250),(465,180,550,250)]
time.sleep(15);key(0x35);deadline=time.monotonic()+35;cross=False;left=False;matches=[]
while time.monotonic()<deadline:
    a=screen();matches=[float(np.mean(np.all(a[y:Y,x:X]==selection[y:Y,x:X],axis=2))) for x,y,X,Y in boxes]
    if min(matches)>.98:
        key(0x4b,True);left=True;time.sleep(.2);break
    if not cross and float(np.mean(np.all(a[100:250,150:650]==title,axis=2)))>.98:key(0x2d);cross=True
    time.sleep(.15)
print(json.dumps({'pid':rec['pid'],'scene':'character_select' if left else 'unconfirmed','portrait_sample_matches':matches,'title_cross_sent':cross,'left_select_sent':left,'PNG_files_created':0,'F1_F3_sent':False,'card_override':False}))
assert left,'Selection scene was not confirmed; no further input sent'
