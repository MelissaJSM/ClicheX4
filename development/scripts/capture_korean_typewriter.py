"""Observe Korean typewriter timing in a verified emulator, without RAM writes.

Optional input is one focused X-key press after 200 ms, only if AbcObj.unkD
still reports the native page-wait state (3). No emulator save/load keys are
sent. Capture decisions are recorded; the evidence is not a pass/fail verdict.
"""
import argparse
import ctypes
from ctypes import wintypes
from datetime import datetime,timezone
import json
from pathlib import Path
import struct
import sys
import time

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts.emulator_session import checked_window
from scripts.emulator_probe import Input,KeyInput
from scripts.prepare_riko_ui import entry
from scripts.project import digest,new_run
from src.epsxe_state import framebuffer

ABC_OFFSET=0x13BC28
COUNT_OFFSET=0x1397E0
PAD_OFFSET=0x166C08
SAMPLE_INTERVAL=0.006
ADVANCE_DELAY=0.2
ADVANCE_HOLD=0.04
SNAPSHOT_EVENTS={1,2,3,4,8,12,20,30}


def abc_fields(raw):
    return {'raw_hex':raw.hex(),'pointer':struct.unpack_from('<I',raw)[0],
            'word':struct.unpack_from('<H',raw,4)[0],
            'x':struct.unpack_from('<h',raw,6)[0],
            'y':struct.unpack_from('<h',raw,8)[0],
            'timer_a':struct.unpack_from('<H',raw,10)[0],
            'active_c':raw[12],'state_d':raw[13],'state_e':raw[14],
            'typewriter_f':raw[15],'field_10':struct.unpack_from('<h',raw,16)[0]}


def read_draw_infos(read,ram_base):
    result=[]
    for address in (0x166C10,0x166CB0):
        raw=read(ram_base+address,40)
        display=struct.unpack_from('<4h',raw,0)
        clip=struct.unpack_from('<4h',raw,20)
        offset=struct.unpack_from('<2h',raw,28)
        x,y,w,h=clip
        if w!=320 or h!=240 or not 0<=x<=704 or display[2:]!=(320,240):
            raise ValueError('Unexpected native DrawInfo geometry')
        result.append({'struct_address':hex(address|0x80000000),
                       'raw_hex':raw.hex(),'draw_clip':list(clip),
                       'draw_offset':list(offset),'display_rect':list(display)})
    if sorted(d['draw_clip'][1] for d in result)!=[0,240]:
        raise ValueError('Expected verified native framebuffer pages y=0 and y=240')
    return result


def observations(samples,transitions,key_events):
    increases=[t for t in transitions if t['count_delta']>0]
    # A sampled delta greater than one can include instant speaker headers or
    # missed polling intervals. Report it without declaring a renderer fault.
    body=[s for s in samples if s['abc']['word']&0xB000==0x1000]
    episodes=[]
    for s in samples:
        pressed=s['pad']['pressed']
        if pressed:
            if not episodes or episodes[-1]['last_sample']!=s['i']-1 or episodes[-1]['bits']!=pressed:
                episodes.append({'bits':pressed,'first_ms':s['t_ms'],'last_ms':s['t_ms'],'last_sample':s['i'],'samples':1})
            else:
                episodes[-1].update(last_ms=s['t_ms'],last_sample=s['i'],samples=episodes[-1]['samples']+1)
    down=next((e['t_ms'] for e in key_events if e['action']=='keydown'),None)
    up=next((e['t_ms'] for e in key_events if e['action']=='keyup'),None)
    gaps=[b['t_ms']-a['t_ms'] for a,b in zip(samples,samples[1:])]
    return {'sample_count':len(samples),'count_increase_events':len(increases),
            'unit_count_increase_events':sum(t['count_delta']==1 for t in increases),
            'count_increase_delta_histogram':{str(d):sum(t['count_delta']==d for t in increases) for d in sorted({t['count_delta'] for t in increases})},
            'body_word_0x1000_samples':len(body),
            'body_word_0x1000_f_nonzero_samples':sum(s['abc']['typewriter_f']!=0 for s in body),
            'body_word_0x1000_f_zero_samples':sum(s['abc']['typewriter_f']==0 for s in body),
            'pressed_episodes':episodes,'expected_advance_pressed_bit':0x40,
            'pressed_non_x_samples':[s['i'] for s in samples if s['pad']['pressed']&~0x40],
            'pressed_samples_before_input':[s['i'] for s in samples if s['pad']['pressed'] and (down is None or s['t_ms']<down)],
            'pressed_samples_after_release_150ms':[s['i'] for s in samples if s['pad']['pressed'] and up is not None and s['t_ms']>up+150],
            'actual_key_hold_ms':None if down is None or up is None else up-down,
            'sample_gap_ms':{'minimum':min(gaps,default=0),'maximum':max(gaps,default=0),'average':sum(gaps)/len(gaps) if gaps else 0},
            'interpretation':'Measurements only; frame sampling is not atomic and may miss transitions. Root reviews timing, flags, input episodes and images.'}


def main(session,cache,seconds=5,advance_page=False,label='dialogue_typewriter',project='ver_buki_riko'):
    if project not in ('ver_buki_riko','ver_rin_nana'):raise ValueError('Unexpected project')
    session=session.resolve()
    if not session.is_relative_to(ROOT/'work'/project/'emulator_sessions'):raise ValueError('Unexpected session')
    import scripts.emulator_session as control
    if project=='ver_rin_nana':control.EMULATOR=ROOT/'work/ver_rin_nana/emulator/ePSXe.exe'
    if not 0.1<=seconds<=30:raise ValueError('Capture seconds must be between 0.1 and 30')
    if advance_page and seconds<0.3:raise ValueError('At least 0.3 seconds is required for optional page advance')
    rec=json.loads((session/'session.local.json').read_text('utf-8'))
    old=json.loads(cache.read_text('utf-8'))
    if old.get('pid')!=rec['pid'] or old.get('bin_sha256')!=rec['bin_sha256']:
        raise ValueError('Cache/session PID or BIN identity differs')
    if len(old.get('ram_bases',[]))!=1 or len(old.get('vram_bases',[]))!=1:
        raise ValueError('One previously verified RAM and VRAM base is required')
    ram_base=int(old['ram_bases'][0]);vram_base=int(old['vram_bases'][0])
    user,hwnd=checked_window(rec['pid'])
    user.SendInput.argtypes=[wintypes.UINT,ctypes.POINTER(Input),ctypes.c_int]
    user.SendInput.restype=wintypes.UINT
    build=Path(rec['cue']).parent
    game=build/('shibuki_riko.bin' if project=='ver_buki_riko' else 'rin_nana.bin')
    if digest(game)!=rec['bin_sha256']:raise ValueError('Session game hash differs')
    from scripts.prepare_rin_common import read_disc
    assets,_=read_disc(game,['SLUS_005.61','LOAD_U.ARC'])
    exe=assets['SLUS_005.61'];font=entry(assets['LOAD_U.ARC'],0x10001)
    kernel=ctypes.WinDLL('kernel32',use_last_error=True)
    kernel.OpenProcess.argtypes=[wintypes.DWORD,wintypes.BOOL,wintypes.DWORD]
    kernel.OpenProcess.restype=wintypes.HANDLE
    kernel.ReadProcessMemory.argtypes=[wintypes.HANDLE,ctypes.c_void_p,ctypes.c_void_p,ctypes.c_size_t,ctypes.POINTER(ctypes.c_size_t)]
    kernel.CloseHandle.argtypes=[wintypes.HANDLE]
    handle=kernel.OpenProcess(0x410,False,rec['pid'])
    if not handle:raise OSError('Read-only emulator process open failed')
    def read(address,size):
        buffer=ctypes.create_string_buffer(size);actual=ctypes.c_size_t()
        if not kernel.ReadProcessMemory(handle,address,buffer,size,ctypes.byref(actual)) or actual.value!=size:
            raise OSError(f'Incomplete read-only process read at {hex(address)}')
        return buffer.raw
    samples=[];transitions=[];snapshots=[];key_events=[]
    out=None;started=None;key_down=False;key_maybe_down=False;release_at=None
    advance={'requested':advance_page,'attempted':False,'sent':False}
    error=None;anchor_checks=[];initial_draw_infos=[]
    def elapsed_ms():return round((time.perf_counter()-started)*1000,4)
    def send_key(up=False):
        nonlocal key_down,key_maybe_down
        event=Input();event.type=1;event.data.key=KeyInput(0,0x2D,8|(2 if up else 0),0,0)
        if not up:key_maybe_down=True
        result=user.SendInput(1,ctypes.byref(event),ctypes.sizeof(event))
        key_events.append({'action':'keyup' if up else 'keydown','scan_code':0x2D,'t_ms':elapsed_ms(),'accepted':result==1})
        if result!=1:raise OSError('X key release failed' if up else 'X key press failed')
        key_down=not up
        if up:key_maybe_down=False
    try:
        for address,length in ((0x233C8,56),(0x23400,32),(0xEA20C,32)):
            expected=exe[address-0x10000+2048:address-0x10000+2048+length]
            if len(expected)!=length or read(ram_base+address,length)!=expected:
                raise ValueError(f'Cached native EXE anchor differs: {hex(address)}')
            anchor_checks.append({'address':hex(address),'bytes':length,'equal':True})
        for y in (2,3,4,5):
            if read(vram_base+(256+y)*2048+960*2,128)!=font[y*128:(y+1)*128]:
                raise ValueError('Cached VRAM font anchor differs')
        initial_draw_infos=read_draw_infos(read,ram_base)
        out=new_run(ROOT,project,'korean_typewriter')
        started=time.perf_counter();deadline=started+seconds;next_sample=started
        previous=None;increase_events=0
        while time.perf_counter()<deadline:
            now=time.perf_counter()
            if key_down and now>=release_at:send_key(up=True)
            if now<next_sample:
                wake=min(next_sample,deadline,release_at if key_down else deadline)
                time.sleep(max(0,wake-time.perf_counter()));continue
            t0=time.perf_counter();raw=read(ram_base+ABC_OFFSET,20)
            count=struct.unpack('<H',read(ram_base+COUNT_OFFSET,2))[0]
            pad=struct.unpack('<3H',read(ram_base+PAD_OFFSET,6));abc=abc_fields(raw)
            sample={'i':len(samples),'t_ms':round((t0-started)*1000,4),'read_end_ms':elapsed_ms(),
                    'abc':abc,'glyph_count':count,'pad':dict(zip(('held','previous','pressed'),pad)),
                    'emulator_focused':user.GetForegroundWindow()==hwnd}
            samples.append(sample)
            if previous is None or raw.hex()!=previous['abc']['raw_hex'] or count!=previous['glyph_count'] or sample['pad']!=previous['pad']:
                delta=0 if previous is None else count-previous['glyph_count']
                transitions.append({'sample':sample['i'],'t_ms':sample['t_ms'],'count':count,'count_delta':delta,
                                    'state_d':abc['state_d'],'word':abc['word'],'word_typewriter_bit':bool(abc['word']&0x1000),
                                    'typewriter_f':abc['typewriter_f'],'pad':sample['pad']})
                if delta>0:
                    increase_events+=1
                    if increase_events in SNAPSHOT_EVENTS:
                        snap_start=elapsed_ms();draw_infos=read_draw_infos(read,ram_base)
                        vram=read(vram_base,0x100000)
                        glyphs=read(ram_base+0x1396CC,240)
                        snapshots.append({'sample':sample['i'],'count':count,'increase_event':increase_events,
                                          'capture_start_ms':snap_start,'capture_end_ms':elapsed_ms(),
                                          'draw_infos':draw_infos,'glyph_records_hex':glyphs.hex(),'vram':vram})
            previous=sample
            if advance_page and not advance['attempted'] and time.perf_counter()-started>=ADVANCE_DELAY:
                # Re-read at the action boundary; never infer wait state from
                # an older sample or from elapsed time alone.
                check=abc_fields(read(ram_base+ABC_OFFSET,20));check_pad=struct.unpack('<3H',read(ram_base+PAD_OFFSET,6))
                focused=user.GetForegroundWindow()==hwnd
                advance.update(attempted=True,at_ms=elapsed_ms(),state_d=check['state_d'],active_c=check['active_c'],
                               pad=list(check_pad),focused=focused)
                if check['state_d']!=3:advance['skip_reason']='dialogue is not in native page-wait state 3'
                elif check['active_c']==0:advance['skip_reason']='dialogue object is inactive'
                elif not focused:advance['skip_reason']='verified emulator window is not focused'
                elif check_pad[0] or check_pad[2]:advance['skip_reason']='controller held or pressed input is already active'
                else:
                    send_key();advance['sent']=True;release_at=time.perf_counter()+ADVANCE_HOLD
            # An exact scheduling target is recorded separately from actual
            # gaps; OS scheduling and memory snapshots can cause larger gaps.
            next_sample=max(next_sample+SAMPLE_INTERVAL,time.perf_counter())
    except Exception as exc:
        error={'type':type(exc).__name__,'message':str(exc)}
    finally:
        if key_maybe_down:
            try:send_key(up=True)
            except Exception as exc:
                if error is None:error={'type':type(exc).__name__,'message':str(exc)}
                else:error['keyup_error']=str(exc)
        kernel.CloseHandle(handle)
    if out is None:
        raise RuntimeError(error['message'] if error else 'Capture did not initialize')
    capture_end_ms=elapsed_ms()
    for index,snapshot in enumerate(snapshots):
        vram=snapshot.pop('vram');name=f'vram_{index:02d}.bin';(out/name).write_bytes(vram)
        snapshot['vram_file']=name;snapshot['framebuffers']=[]
        for info in snapshot['draw_infos']:
            x,y,_,_=info['draw_clip'];name=f'frame_{index:02d}_y{y}.png'
            framebuffer(vram,x*2,y).save(out/name)
            snapshot['framebuffers'].append({'page_y':y,'image':name,'draw_clip':info['draw_clip']})
    report={'label':label,'created_at_utc':datetime.now(timezone.utc).isoformat(),'session':str(session),'cache':str(cache),
            'pid':rec['pid'],'bin_sha256':rec['bin_sha256'],'ram_bases':[ram_base],'vram_bases':[vram_base],
            'native_exe_anchor_checks':anchor_checks,'native_framebuffer_draw_infos':initial_draw_infos,
            'requested_seconds':seconds,'capture_end_ms':capture_end_ms,'target_sample_interval_ms':SAMPLE_INTERVAL*1000,
            'state_source':{'abc_offset':hex(ABC_OFFSET),'abc_bytes':20,'count_offset':hex(COUNT_OFFSET),
                            'pad_offset':hex(PAD_OFFSET),'pad_words':['held','previous','pressed'],
                            'wait_state_field':'AbcObj + 0x0d','wait_state_value':3,'typewriter_gate_field':'AbcObj + 0x0f'},
            'advance_page':advance,'key_events':key_events,'samples':samples,'transitions':transitions,'snapshots':snapshots,
            'snapshot_policy':{'on_count_increase_events':sorted(SNAPSHOT_EVENTS),'maximum':8,
                               'at_least_four_collected':len(snapshots)>=4,
                               'note':'Fewer than four snapshots means insufficient qualifying count transitions were observed; no extra page input is sent.'},
            'observations':observations(samples,transitions,key_events),'error':error,
            'process_memory_access':'PROCESS_QUERY_INFORMATION | PROCESS_VM_READ (0x410)',
            'process_memory_written':False,'save_or_load_state_keys_sent':False,
            'keys_sent':bool(key_events),'capture_sampling_is_atomic':False,'runtime_verdict':'not_assigned'}
    (out/'evidence.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps({'output':str(out),'samples':len(samples),'snapshots':len(snapshots),'advance_sent':advance['sent'],'error':error}))
    if error:raise RuntimeError(error['message'])


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project',choices=['ver_buki_riko','ver_rin_nana'],default='ver_buki_riko')
    parser.add_argument('--session',type=Path,required=True)
    parser.add_argument('--cache',type=Path,required=True)
    parser.add_argument('--seconds',type=float,default=5)
    parser.add_argument('--advance-page',action='store_true')
    parser.add_argument('--label',default='dialogue_typewriter')
    args=parser.parse_args()
    main(args.session,args.cache,args.seconds,args.advance_page,args.label,args.project)
