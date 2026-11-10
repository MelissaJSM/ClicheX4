"""Approach the visible enemy with bounded ordinary keys; no RAM writes."""
from pathlib import Path
import argparse,json,subprocess,sys,time
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from scripts.observe_sprite_consistency_runtime import ReadOnlyProcess
p=argparse.ArgumentParser();p.add_argument('--session',type=Path,required=True);p.add_argument('--ram-base',type=int,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();assert not a.output.exists()
rec=json.loads((a.session/'session.local.json').read_text('utf8'));check=json.loads(subprocess.check_output([sys.executable,str(Path(__file__).with_name('read_menu_rn22.py')),'--session',str(a.session),'--pid',str(rec['pid']),'--ram-base',str(a.ram_base)],text=True,encoding='utf8'));assert check['passed']and check['engine']['stage']==10 and check['engine']['state']==6 and check['player']['active']==1
trace=[];proc=ReadOnlyProcess(rec);start=time.monotonic();last=-3
def key(scan,hold):
 r=subprocess.run([sys.executable,'scripts/korean_runtime_control.py','--project','ver_rin_nana','key','--session',str(a.session),'--scan',scan,'--extended','--hold',str(hold)],capture_output=True,text=True,encoding='utf8',timeout=4)
 trace.append({'key':scan,'hold':hold,'exit':r.returncode,'output':r.stdout,'error':r.stderr});assert r.returncode==0
try:
 while time.monotonic()-start<23:
  q=proc.read(a.ram_base+0x1418c8,228);engine=proc.read(a.ram_base+0x1721c0,14);now=time.monotonic()-start
  if now-last<1.2:time.sleep(.03);continue
  trace.append({'seconds':now,'active':q[0],'hp':q[0x5c],'frame':q[0x47],'engine':list(engine[:4]),'stage':engine[12]});last=now
  if engine[0]!=6 or engine[12]!=10 or q[0]!=1 or not q[0x5c]:break
  if q[0x5c]<16:
   key('0x4b',.55);break
  key('0x4d',.30)
finally:proc.close()
a.output.write_text(json.dumps({'session':str(a.session),'events':trace,'memory_written':False,'save_keys_sent':False,'purpose':'눈으로 확인한 스페이스포트 적에게 일반 이동 키로 접근; 체력16미만이면 왼쪽으로 벗어남.'},ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps({'last_observation':next(q for q in reversed(trace)if'hp'in q),'output':str(a.output)}))
