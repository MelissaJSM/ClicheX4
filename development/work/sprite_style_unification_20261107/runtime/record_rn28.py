"""Play bounded ordinary inputs and record the actual focused game window."""
import argparse,ctypes,json,sys,time,winreg
from datetime import datetime,timezone
from pathlib import Path
from ctypes import wintypes
from PIL import ImageGrab,Image,ImageDraw
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
import scripts.emulator_session as control

def main(a):
    session=a.session.resolve();out=a.output.resolve()
    modes=[m for m in ('ver_buki_riko','ver_rin_nana') if session.is_relative_to(ROOT/'work'/m/'emulator_sessions')]
    if len(modes)!=1 or not any(out.is_relative_to(ROOT/p) for p in ('work/sprite_consistency_20261105/runtime','work/sprite_reaudit_20261106/runtime','work/sprite_style_unification_20261107/runtime')) or out.exists():raise ValueError('Invalid session/output')
    mode=modes[0];rec=json.loads((session/'session.local.json').read_text('utf8'))
    current=json.loads((ROOT/'projects'/mode/'current_build.json').read_text('utf8'))
    if rec['bin_sha256']!={'ver_buki_riko': '0000000000000000000000000000000000000000000000000000000000000000', 'ver_rin_nana': '9ea0cc759b2884d026a305b45ce21a2d97f78aa2682f27b6349b864039784f58'}[mode]:raise ValueError('Not the hash-bound RN checkpoint28 build')
    if mode=='ver_rin_nana':control.EMULATOR=ROOT/'work/ver_rin_nana/emulator/ePSXe.exe'
    plan=json.loads(a.plan.read_text('utf8'));duration=float(plan['duration'])
    if not 0<duration<=30:raise ValueError('Clip duration out of range')
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER,r'Software\epsxe\config') as reg:pad=list(map(int,winreg.QueryValueEx(reg,'Pad1')[0].split(',')))
    names=['left','right','up','down','triangle','circle','cross','square','l1','l2','r1','r2','start','select']
    keys=dict(zip(names,pad));events=plan['events']
    for e in events:
        if not 0<=e['at']<e['at']+e['hold']<=duration or e['hold']>3 or any(k not in keys or k in ('start','select') for k in e['keys']):raise ValueError('Invalid bounded input')
        if any((keys[k]&127) in range(0x3b,0x45) for k in e['keys']):raise ValueError('Function key mapping is not allowed')
    user,hwnd=control.checked_window(rec['pid']);user.ShowWindowAsync(hwnd,9);user.SetForegroundWindow(hwnd);time.sleep(.2)
    if user.GetForegroundWindow()!=hwnd:raise RuntimeError('No game focus; no inputs sent')
    out.mkdir(parents=True);held=set();frames=[];stamps=[];trace=[];error=None
    def send(key,down):
        scan=keys[key];event=control.Input();event.type=1;event.data.key=control.KeyInput(0,scan&127,8|int(bool(scan&128))|(0 if down else 2),0,0)
        if user.SendInput(1,ctypes.byref(event),ctypes.sizeof(event))!=1:raise OSError('SendInput failed')
        trace.append({'seconds':time.monotonic()-start,'button':key,'down':down})
    start=time.monotonic();start_ns=time.monotonic_ns();start_utc=datetime.now(timezone.utc).isoformat();next_capture=0
    try:
        while (elapsed:=time.monotonic()-start)<duration:
            if user.GetForegroundWindow()!=hwnd:raise RuntimeError('Focus changed; stopped input')
            wanted={k for e in events if e['at']<=elapsed<e['at']+e['hold'] for k in e['keys']}
            for k in sorted(held-wanted):send(k,False);held.remove(k)
            for k in sorted(wanted-held):send(k,True);held.add(k)
            if elapsed>=next_capture:
                rect=wintypes.RECT();point=wintypes.POINT();user.GetClientRect(hwnd,ctypes.byref(rect));user.ClientToScreen(hwnd,ctypes.byref(point))
                frames.append(ImageGrab.grab(bbox=(point.x,point.y,point.x+rect.right,point.y+rect.bottom)).convert('RGB'));stamps.append(elapsed);next_capture=elapsed+.05
            time.sleep(.005)
    except Exception as e:error=str(e)
    finally:
        for k in list(held):send(k,False);held.remove(k)
    end_ns=time.monotonic_ns();end_utc=datetime.now(timezone.utc).isoformat()
    if frames:
        durations=[max(1,round((b-a)*1000)) for a,b in zip(stamps,stamps[1:])]+[100]
        frames[0].save(out/'play.webp',save_all=True,append_images=frames[1:],duration=durations,loop=0,lossless=True,method=0)
        frames[0].save(out/'first.png');frames[-1].save(out/'last.png')
        chosen=[round(i*(len(frames)-1)/11) for i in range(12)]
        cw,ch=frames[0].size;board=Image.new('RGB',(cw*3,(ch+24)*4),'#202630');draw=ImageDraw.Draw(board)
        for j,n in enumerate(chosen):
            x,y=j%3*cw,j//3*(ch+24);board.paste(frames[n],(x,y+24));draw.text((x+8,y+5),f'{stamps[n]:.2f}s',fill='white')
        board.save(out/'contact.png')
    report={'project':mode,'pid':rec['pid'],'session':session.relative_to(ROOT).as_posix(),'bin_sha256':rec['bin_sha256'],'plan':plan,'pad1':pad,'input_trace':trace,'capture_times':stamps,'frames':len(frames),'error':error,'keys_released':not held,'actual_window_recording':True,'simulated_video':False,'memory_written':False,'save_keys_sent':False}
    report.update(record_start_utc=start_utc,record_end_utc=end_utc,record_start_monotonic_ns=str(start_ns),record_end_monotonic_ns=str(end_ns))
    (out/'evidence.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf8')
    print(json.dumps({'output':str(out),'frames':len(frames),'error':error}))
    if error:raise RuntimeError(error)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--session',type=Path,required=True);p.add_argument('--plan',type=Path,required=True);p.add_argument('--output',type=Path,required=True);main(p.parse_args())
