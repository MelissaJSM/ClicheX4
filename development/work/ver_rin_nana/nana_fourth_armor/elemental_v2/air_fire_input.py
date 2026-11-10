"""현재 검증된 창에 점프 후 발사만 입력한다. 게임 메모리 쓰기 없음."""
import ctypes,json,sys,time,winreg
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT))
import scripts.emulator_session as em
from scripts.emulator_probe import Input,KeyInput
from scripts.project import digest
session=ROOT/'work/ver_rin_nana/emulator_sessions/20261030T112248937334Z'
s=json.loads((session/'session.local.json').read_text('utf8'))
assert s['pid']==31836 and s['bin_sha256']=='161942372bd8016b0002d1de09722df60545c314a56954b944a1294555d27d42'
assert digest(Path(s['cue']).with_suffix('.bin'))==s['bin_sha256']
with winreg.OpenKey(winreg.HKEY_CURRENT_USER,r'Software\epsxe\config') as k:
    pad=list(map(int,winreg.QueryValueEx(k,'Pad1')[0].split(',')))
assert pad[6:8]==[45,46]
em.EMULATOR=ROOT/'work/ver_rin_nana/emulator/ePSXe.exe';u,w=em.checked_window(s['pid']);held=set()
def key(sc,down):
    e=Input();e.type=1;e.data.key=KeyInput(0,sc,8|(0 if down else 2),0,0)
    if u.SendInput(1,ctypes.byref(e),ctypes.sizeof(e))!=1:raise RuntimeError('Input failed')
    if down:held.add(sc)
    else:held.discard(sc)
try:
    if u.GetForegroundWindow()!=w:
        key(0x38,True);key(0x38,False);u.SetForegroundWindow(w);time.sleep(.2)
    assert u.GetForegroundWindow()==w
    for _ in range(3):
        assert u.GetForegroundWindow()==w
        key(0x2d,True);time.sleep(.18);key(0x2e,True);time.sleep(.10)
        key(0x2e,False);key(0x2d,False);time.sleep(1.2)
finally:
    for sc in list(held):key(sc,False)
print(json.dumps({'jump_fire_repeats':3,'process_memory_written':False,'save_written':False}))
