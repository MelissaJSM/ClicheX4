"""Load the authenticated copied full-armor DATA3 using ordinary menu keys only."""
import argparse,json,subprocess,sys,time,struct
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from scripts.observe_sprite_consistency_runtime import ReadOnlyProcess
p=argparse.ArgumentParser();p.add_argument('--session',type=Path,required=True);p.add_argument('--ram-base',type=int,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
assert not a.output.exists()
rec=json.loads((a.session/'session.local.json').read_text('utf8'))
result=json.loads(subprocess.check_output([sys.executable,str(Path(__file__).with_name('read_menu_br31.py')),'--session',str(a.session),'--pid',str(rec['pid']),'--ram-base',str(a.ram_base)],text=True,encoding='utf8'))
assert result['passed'] and result['project']=='ver_buki_riko' and result['game_info']['route']==7
proc=ReadOnlyProcess(rec);trace=[];start=time.monotonic();last=-2;authenticated=False;loaded=False
try:
    while time.monotonic()-start<25:
        g=proc.read(a.ram_base+0x173c70,4);e=proc.read(a.ram_base+0x1721c0,100);t=proc.read(a.ram_base+0x141bd8,12)
        now=time.monotonic()-start
        if e[0]==3:
            assert authenticated and (e[0x43],e[0x47],e[0x48],e[0x37])==(0,15,2,0)
            loaded=True;break
        if now-last<1.0:time.sleep(.03);continue
        scan=None;extended=False
        if g[0]==7 and g[1]==3:scan='0x2d'
        elif g[0]==9 and e[0]==0:
            if e[1]==1:
                assert t[7]==0,'Unexpected memory-card cursor';scan='0x2d'
            elif e[1]==3:
                assert t[7]<=2,'Unexpected data cursor'
                if t[7]<2:scan='0x50';extended=True
                else:
                    m=proc.read(a.ram_base+0x1721b0,16);ptr=struct.unpack_from('<I',m,12)[0]
                    assert 0x80000000<=ptr<=0x801fffd6
                    slot=proc.read(a.ram_base+(ptr&0x1fffff),42)
                    selected=tuple(slot[i] for i in (0,1,2,3,4,41))
                    if selected!=(0,48,2,15,255,0):
                        trace.append({'seconds':now,'record_not_ready':selected,'cursor':t[7]})
                        last=now;time.sleep(.05);continue
                    authenticated=True;scan='0x2d'
            elif e[1]==4:
                assert authenticated and t[7]==0;scan='0x2d'
        if scan:
            cmd=[sys.executable,'scripts/korean_runtime_control.py','--project','ver_buki_riko','key','--session',str(a.session),'--scan',scan]
            if extended:cmd.append('--extended')
            q=subprocess.run(cmd,capture_output=True,text=True,encoding='utf8',timeout=5)
            trace.append({'seconds':now,'engine':list(e[:4]),'route':list(g),'cursor':t[7],'scan':scan,'extended':extended,'exit':q.returncode,'output':q.stdout,'error':q.stderr})
            assert q.returncode==0;last=time.monotonic()-start
        time.sleep(.03)
finally:proc.close()
a.output.write_text(json.dumps({'loaded':loaded,'source_record_authenticated':authenticated,'session':str(a.session),'events':trace,'memory_written':False,'save_keys_sent':False},indent=2)+'\n','utf8')
assert loaded,'Timed out without loading'
print(json.dumps({'loaded':loaded,'trace':str(a.output),'events':len(trace)}))
