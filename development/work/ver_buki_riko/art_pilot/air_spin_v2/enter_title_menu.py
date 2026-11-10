"""Wait for the actual PRESS START text, then send one Start tap; no blind repeat."""
from pathlib import Path
import sys,time,ctypes,json
from ctypes import wintypes
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT))
from scripts.emulator_session import checked_window,Input,KeyInput
from PIL import Image,ImageGrab
import numpy as np
S=ROOT/'work/ver_buki_riko/emulator_sessions/20261025T095836045176Z';D=Path(__file__).parent
pid=json.loads((S/'session.local.json').read_text())['pid'];user,hwnd=checked_window(pid)
user.ShowWindowAsync(hwnd,9);user.SetForegroundWindow(hwnd);time.sleep(.2)
rect=wintypes.RECT();point=wintypes.POINT();user.GetClientRect(hwnd,ctypes.byref(rect));user.ClientToScreen(hwnd,ctypes.byref(point))
def grab():
 if user.GetForegroundWindow()!=hwnd:raise RuntimeError('Focus changed')
 return ImageGrab.grab(bbox=(point.x,point.y,point.x+rect.right,point.y+rect.bottom)).convert('RGB')
press=Image.open(ROOT/'work/ver_buki_riko/emulator_sessions/20261025T094244721335Z/20261025T094656427766Z.png').convert('RGB').crop((240,378,562,414))
menu=Image.open(ROOT/'work/ver_buki_riko/emulator_sessions/20261025T091005223979Z/20261025T091242346877Z.png').convert('RGB').crop((280,298,501,328))
def match(im,ref,box):
 a=np.array(im.crop(box)).astype(int);b=np.array(ref).astype(int);mask=(b.min(axis=2)>195)
 return mask.sum()>50 and np.abs(a[mask]-b[mask]).mean()<15
deadline=time.monotonic()+45;sent=False
while time.monotonic()<deadline:
 im=grab()
 if match(im,menu,(280,298,501,328)):
  im.save(S/'recognized_menu.png');print(json.dumps({'menu':True,'start_sent':sent}),flush=True);break
 if not sent and match(im,press,(240,378,562,414)):
  im.save(S/'recognized_press_start.png');event=Input();event.type=1;event.data.key=KeyInput(0,0x2f,8,0,0)
  try:
   if user.SendInput(1,ctypes.byref(event),ctypes.sizeof(event))!=1:raise RuntimeError('Key down failed')
   time.sleep(.5)
  finally:event.data.key.flags|=2;user.SendInput(1,ctypes.byref(event),ctypes.sizeof(event))
  sent=True;print('Start sent after visible prompt',flush=True)
 time.sleep(.08)
else:raise RuntimeError('No menu recognized; no repeated key input')
