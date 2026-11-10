"""확인된 작업 에뮬레이터에서 좌우 이동·대시·점프를 입력하며 실제 클라이언트를 녹화한다."""
import argparse
import ctypes
from ctypes import wintypes
import json
from pathlib import Path
import sys
import time

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts.emulator_session import checked_window,Input,KeyInput
from scripts.project import write_json


def record(session,hold=.7,fps=20,with_jump=False,with_dash=False):
    if not .15 <= hold <= 1.6 or fps not in (20,40):
        raise ValueError('Expected hold .15..1.6 seconds and fps 20 or 40')
    if with_dash and (with_jump or hold>.25):
        raise ValueError('Dash recording needs a short 0.15..0.25 second direction tap and no jump')
    interval=1/fps
    from PIL import ImageGrab
    session=session.resolve()
    if not session.is_relative_to((ROOT/'work/ver_buki_riko/emulator_sessions').resolve()):
        raise ValueError('Expected a project emulator session')
    metadata=json.loads((session/'session.local.json').read_text(encoding='utf-8'))
    user,window=checked_window(metadata['pid']);user.ShowWindowAsync(window,9);user.SetForegroundWindow(window);time.sleep(.2)
    if user.GetForegroundWindow()!=window:raise RuntimeError('No emulator focus')
    out=session/('dash_recording' if with_dash else 'run_recording');out.mkdir(exist_ok=False)
    event=Input();event.type=1
    def key(scan,down):
        flags=8|int(scan in (0x4b,0x4d))
        event.data.key=KeyInput(0,scan,flags if down else flags|2,0,0)
        if user.SendInput(1,ctypes.byref(event),ctypes.sizeof(event))!=1:raise OSError('Input failed')
    images=[];times=[];events=[];held=None;start=time.monotonic()
    try:
        while time.monotonic()-start<(8 if with_jump else 5):
            now=time.monotonic()-start
            if user.GetForegroundWindow()!=window:raise RuntimeError('Focus changed; recording stopped')
            left_start=max(2.0,1.0+hold)
            wanted=0x4d if .5<=now<.5+hold else 0x4b if left_start<=now<left_start+hold else None
            if with_jump and (4.4<=now<4.9 or 6.4<=now<6.9):wanted=0x2c
            if with_dash and (.9<=now<1.35 or 2.4<=now<2.85):wanted=0x2d
            if wanted!=held:
                if held is not None:key(held,False);events.append([now,held,'up'])
                if wanted is not None:key(wanted,True);events.append([now,wanted,'down'])
                held=wanted
            rect=wintypes.RECT();point=wintypes.POINT()
            user.GetClientRect(window,ctypes.byref(rect));user.ClientToScreen(window,ctypes.byref(point))
            if rect.right<=0 or rect.bottom<=0:raise RuntimeError('Empty client')
            times.append(time.monotonic()-start)
            images.append(ImageGrab.grab(bbox=(point.x,point.y,point.x+rect.right,point.y+rect.bottom)))
            time.sleep(max(0,interval-(time.monotonic()-start-now)))
    finally:
        if held is not None:key(held,False)
    for i,im in enumerate(images):im.save(out/f'client_{i:03d}.png')
    duration=[max(10,round(b*100)*10-round(a*100)*10) for a,b in zip(times,times[1:])]+[max(10,round(interval*100)*10)]
    images[0].save(out/('dash_live.gif' if with_dash else 'run_live.gif'),save_all=True,append_images=images[1:],duration=duration,loop=0,disposal=2)
    write_json(out/'recording.local.json',{'session':str(session),'bin_sha256':metadata['bin_sha256'],
        'capture':'Foreground client ImageGrab, no compositing','frame_times_seconds':times,'input_events':events,
        'requested_interval_seconds':interval,'hold_seconds':hold,'with_jump':with_jump,'with_dash':with_dash,'frame_count':len(images),'process_memory_written':False,
        'gif_palette_conversion':True,'exact_pixel_evidence':'See separate run_runtime RAM/VRAM/framebuffer verification'})
    print(json.dumps({'output':str(out),'frames':len(images),'duration':times[-1]-times[0]}))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--session',type=Path,required=True)
    parser.add_argument('--hold',type=float,default=.7);parser.add_argument('--fps',type=int,choices=(20,40),default=20)
    modes=parser.add_mutually_exclusive_group();modes.add_argument('--with-jump',action='store_true');modes.add_argument('--with-dash',action='store_true')
    args=parser.parse_args();record(args.session,args.hold,args.fps,args.with_jump,args.with_dash)
