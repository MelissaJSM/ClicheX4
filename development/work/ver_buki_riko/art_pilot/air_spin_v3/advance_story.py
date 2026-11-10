"""Advance only while the already inspected dialogue border remains visible."""
from pathlib import Path
import sys,json,subprocess,time
from PIL import Image
import numpy as np
ROOT=Path(__file__).resolve().parents[4];S=ROOT/'work/ver_buki_riko/emulator_sessions/20261025T102010009360Z'
box=(100,55,698,63);reference=np.array(Image.open(ROOT/'work/ver_buki_riko/emulator_sessions/20261025T095836045176Z'/'20261025T100117896685Z.png').convert('RGB').crop(box)).astype(int)
def call(action):
 args=[sys.executable,str(ROOT/'scripts/emulator_session.py'),action,'--session',str(S)]
 if action=='key':args+=['--scan','0x2c','--hold','0.15']
 return json.loads(subprocess.check_output(args,text=True))
for i in range(10):
 r=call('capture');a=np.array(Image.open(r['capture']).convert('RGB').crop(box)).astype(int)
 if abs(a-reference).mean()>4:
  print(json.dumps({'stopped_before_input':True,'capture':r['capture'],'keys_sent':i}));break
 call('key');time.sleep(2.2)
else:print(json.dumps({'max_dialogue_keys':10}))
