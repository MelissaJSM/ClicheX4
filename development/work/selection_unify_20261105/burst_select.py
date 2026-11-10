"""선택 화면 실제 프레임을 빠르게 저장한다. 합성/이미지 수정 없음."""
import ctypes,json,runpy,sys,time
from ctypes import wintypes
from pathlib import Path
from datetime import datetime,timezone
import numpy as np
from PIL import ImageGrab
d=runpy.run_path(str(Path(__file__).with_name('runtime_control.py')));m=d['m'];project=d['PROJECT']
s=json.loads((m.OUT/'session.json').read_text('utf8'));m.focus(s['pid'],m.EXE)
if '--left' in sys.argv:m.run('key',0x4b,hold=.06,extended=True)
u,h=m.control.checked_window(s['pid']);rect=wintypes.RECT();pt=wintypes.POINT();u.GetClientRect(h,ctypes.byref(rect));u.ClientToScreen(h,ctypes.byref(pt))
out=Path(__file__).parent/'after_runtime'/(project+'_burst_'+datetime.now(timezone.utc).strftime('%H%M%S'));out.mkdir(parents=True)
records=[]
for i in range(24):
    assert u.GetForegroundWindow()==h,'Focus changed'
    im=ImageGrab.grab((pt.x,pt.y,pt.x+rect.right,pt.y+rect.bottom));a=np.array(im.convert('RGB'))
    green=(a[:,:,1]>200)&(a[:,:,0]<90)&(a[:,:,2]<90)
    rec={'frame':i,'left_green':int(green[110:470,7:25].sum()),'right_green':int(green[110:470,775:793].sum())};records.append(rec)
    im.save(out/f'{i:02}.png');time.sleep(.12)
(out/'frames.json').write_text(json.dumps(records,indent=2)+'\n','utf8');print(json.dumps({'path':str(out),'frames':records}))
