"""현재 실행 파일의 메뉴 상태를 확인한 뒤 한 단계만 입력한다. 메모리 읽기 전용."""
from pathlib import Path
import argparse,ctypes,json,struct,sys,time
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from scripts.observe_sprite_consistency_runtime import ReadOnlyProcess
import scripts.emulator_session as control
from scripts.discover_inputs import DiscReader

p=argparse.ArgumentParser();p.add_argument('--session',type=Path,required=True);p.add_argument('--ram',type=int,required=True);p.add_argument('--action',choices=['title_continue','load_fourth','load_ultimate','load_preultimate','load_rin','load_base','advance_hq','read','confirm','down','up','left','right','cancel','start'],required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--hold',type=float,default=.09);a=p.parse_args()
assert .03<=a.hold<=.2 and not a.output.exists();rec=json.loads((a.session/'session.local.json').read_text('utf8'));project='ver_rin_nana'if'ver_rin_nana'in a.session.as_posix()else'ver_buki_riko'
assert rec['bin_sha256']==json.loads((ROOT/'work/armor_dialogue_20261108/builds.json').read_text('utf8'))[project]['sha256']
if project=='ver_rin_nana':control.EMULATOR=ROOT/'work/ver_rin_nana/emulator/ePSXe.exe'
proc=ReadOnlyProcess(rec)
with (Path(rec['cue']).with_suffix('.bin')).open('rb')as f:
    disc=DiscReader(f,Path(f.name).stat().st_size);q=next(q for q in disc.inspect()['files']if q['path']=='/SLUS_005.61;1');exe=disc.read(q['lba'],q['size'])
for at in (0x1540c,0x15ecc,0x233c8):assert proc.read(a.ram+at,48)==exe[at-0x10000+2048:at-0x10000+2048+48],'RAM base not verified'
user,hwnd=control.checked_window(rec['pid']);user.ShowWindowAsync(hwnd,9);user.SetForegroundWindow(hwnd);time.sleep(.1);assert user.GetForegroundWindow()==hwnd
events=[];states=[];start=time.monotonic()
def state():
    gi=proc.read(a.ram+0x173c70,16);en=proc.read(a.ram+0x1721c0,100);menu=proc.read(a.ram+0x1721b0,16);pl=proc.read(a.ram+0x1418c8,228)
    return {'route':gi[0],'mode':gi[1],'title_cursor':gi[2],'input_phase':gi[13],'transition':proc.read(a.ram+0x141bdc,1)[0],'engine':list(en[:4]),'stage':en[12],'area':en[13],'character':en[0x43],'armor':en[0x47],'ultimate':en[0x37],'card_port':menu[6],'card_index':menu[7],'card_state':list(menu[:11]),'player_frame':pl[0x47],'player_animation':pl[0x17],'hp':pl[0x5c]}
def press(scan):
    assert user.GetForegroundWindow()==hwnd
    e=control.Input();e.type=1;e.data.key=control.KeyInput(0,scan&127,8|int(bool(scan&128)),0,0)
    assert user.SendInput(1,ctypes.byref(e),ctypes.sizeof(e))==1
    try:time.sleep(a.hold)
    finally:e.data.key.flags|=2;user.SendInput(1,ctypes.byref(e),ctypes.sizeof(e))
    events.append({'seconds':time.monotonic()-start,'scan':scan});time.sleep(.2)
try:
    states.append(state())
    if a.action in ('title_continue','load_fourth','load_ultimate','load_preultimate','load_rin','load_base'):
        sent=0;last_movie_skip=-10
        while time.monotonic()-start<30:
            s=state()
            if s['route']==6 and s['mode']==1 and s['transition']==0:
                if s['title_cursor']==1:press(45);break
                press(208 if s['title_cursor']==0 else 200);sent+=1;assert sent<=2
            elif s['route']==0 and time.monotonic()-start-last_movie_skip>2:
                press(53);last_movie_skip=time.monotonic()-start
            elif s['route']==1 and s['input_phase']==0 and s['transition']==0:
                press(53);sent+=1;assert sent<=2
            elif s['route']==7:break
            elif s['engine'][0]!=0:raise ValueError('Unexpected live engine; title inputs refused')
            time.sleep(.04)
        else:raise TimeoutError('Title menu did not become ready')
        if a.action in ('load_fourth','load_ultimate','load_preultimate','load_rin','load_base'):
            is_rin=a.action=='load_rin'
            assert rec['memory_card_overrides']['0']['sha256']==('b0a596dba2e0e6ba6cdaaf87a894990365f0a33ee2b8d6536f6a5eb2298d77f9' if is_rin else 'bfeacc6f59f0731581af8e8d77709fea04211775a2b66acf4478ff01ff5c9c6e' if a.action in ('load_ultimate','load_base') else '4002040abe7bfa897b114d56b962cce74b2d23ee7a044d43768c6edaff95daff' if a.action=='load_preultimate' else 'ab68aa740dd7a93b8b01b4b4b9cf1a57dab11c9900052879bfbc665499bf120f')
            def wait_for(test):
                end=time.monotonic()+15
                while time.monotonic()<end:
                    s=state()
                    if test(s):states.append(s);return s
                    time.sleep(.03)
                raise TimeoutError('Expected memory card menu not ready')
            wait_for(lambda s:s['route']==7 and s['mode']==3 and s['transition']==0);time.sleep(.6);press(45)
            wait_for(lambda s:s['engine'][:2]==[0,1] and s['transition']==0);press(45)
            wait_for(lambda s:s['engine'][:2]==[0,3] and s['transition']==0)
            # The card reader sets substate3 before its blocking read completes.
            # Wait for rendered native frames, then prove each cursor transition.
            frame0=struct.unpack('<I',proc.read(a.ram+0x141bd8,4))[0]
            wait_for(lambda s:(struct.unpack('<I',proc.read(a.ram+0x141bd8,4))[0]-frame0)&0xffffffff>30)
            for expected in (() if is_rin or a.action=='load_base' else (1,2)):
                press(208)
                wait_for(lambda s:proc.read(a.ram+0x141bdf,1)[0]==expected)
            assert proc.read(a.ram+0x141bdf,1)[0]==(0 if is_rin or a.action=='load_base' else 2),'Expected DATA cursor required'
            press(45)
            wait_for(lambda s:s['engine'][:2]==[0,4] and s['transition']==0);press(45)
            wait_for(lambda s:s['engine'][0]==3 and s['transition']==0)
            assert state()['character']==int(is_rin) and state()['armor']==(0 if is_rin or a.action in ('load_preultimate','load_base') else 15) and state()['ultimate']==int(a.action in ('load_ultimate','load_preultimate'))
    elif a.action=='advance_hq':
        assert state()['engine'][:2]==[3,9]
        for _ in range(25):
            s=state();states.append(s)
            if s['engine'][:2]!=[3,9]:break
            press(45);time.sleep(.5)
    elif a.action!='read':
        assert state()['transition']==0,'Menu transition active; action refused'
        press({'confirm':45,'down':208,'up':200,'left':203,'right':205,'cancel':47,'start':53}[a.action])
    states.append(state())
finally:proc.close()
a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps({'session':a.session.as_posix(),'states':states,'events':events,'memory_written':False},indent=2)+'\n','utf8');print(json.dumps(states[-1]))
