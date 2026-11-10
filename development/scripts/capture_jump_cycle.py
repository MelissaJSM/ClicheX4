"""검증된 ePSXe의 점프/대기/이동/대시를 RAM/VRAM/렌더로 대조."""
import argparse
import ctypes
from ctypes import wintypes
import json
from pathlib import Path
import struct
import sys
import time

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts.emulator_session import checked_window, Input, KeyInput
from scripts.project import new_run, write_json, digest
from scripts.discover_inputs import psx_arc
from scripts.extract_zero import save_image
from src.psx_player import graphics_bank,decode_stream,composition_frame,compose_indices
from src.epsxe_state import framebuffer,match_sprite
from src.psx_hurt_launch import compose_launch as compose_indices


def capture(build, evidence, idle=False, run_direction=None, dash=False, run_hold=.75, dash_hold=.45, observe=False, wall=False, ground_slash=False, air_slash=False, wall_saber=False, low_hp_idle=False, hurt=False, hurt_facing=None, mobility=None, launch_hurt=False, air_spin=False, ice=False, rise=False, burst=False, thrust=False, dashslash=False, beam_in=False, victory=False, project='ver_buki_riko'):
    if project not in ('ver_buki_riko','ver_rin_nana'):raise ValueError('Unknown project')
    if project=='ver_rin_nana':
        import scripts.emulator_session as session_control
        session_control.EMULATOR=ROOT/'work/ver_rin_nana/emulator/ePSXe.exe'
    if air_spin and not observe:raise ValueError('Air spin requires --observe and ordinary gameplay')
    if ice and not observe:raise ValueError('Ice requires --observe and ordinary gameplay')
    if rise and not observe:raise ValueError('Rising saber requires --observe and ordinary gameplay')
    if burst and not observe:raise ValueError('Burst requires --observe and ordinary gameplay')
    if thrust and not observe:raise ValueError('Thrust requires --observe and ordinary gameplay')
    if dashslash and not observe:raise ValueError('Dash slash requires --observe and ordinary gameplay')
    if beam_in and not observe:raise ValueError('Arrival capture requires --observe and ordinary stage entry')
    if victory and not observe:raise ValueError('Victory capture requires --observe and ordinary stage completion or exit')
    special_bank=wall_saber or air_spin or ice or rise or burst or thrust or victory
    if mobility not in (None,'double_jump','air_dash'):raise ValueError('Unknown mobility mode')
    if mobility and not observe:raise ValueError('Unlocked mobility requires --observe and an ordinary input plan')
    if hurt_facing not in (None,'left','right') or (hurt_facing and not (hurt or launch_hurt)):raise ValueError('Facing filter requires hurt capture')
    if launch_hurt and not observe:raise ValueError('Launch capture requires ordinary gameplay and --observe')
    if hurt and not observe:raise ValueError('Hurt capture requires --observe; use ordinary gameplay damage')
    if low_hp_idle and not observe:raise ValueError('Low HP idle requires --observe; take damage through ordinary gameplay')
    if wall_saber and not observe:raise ValueError('Wall saber requires --observe; position with ordinary gameplay first')
    if wall and not observe:raise ValueError('Wall capture requires --observe; position with ordinary gameplay first')
    if ground_slash and not observe:raise ValueError('Ground slash capture requires --observe; use a checked input plan')
    if air_slash and not observe:raise ValueError('Air slash capture requires --observe; use a checked input plan')
    if not .15 <= run_hold <= 2.0:
        raise ValueError('Run hold must be between .15 and 2 seconds')
    if not .05 <= dash_hold <= .75:
        raise ValueError('Dash hold must be between .05 and .75 seconds')
    build=build.resolve(); evidence=evidence.resolve()
    if not build.is_relative_to((ROOT/'out'/project).resolve()) or not evidence.is_relative_to((ROOT/'work'/project/'live_poc').resolve()):
        raise ValueError('Unexpected evidence/build path')
    prior=json.loads(evidence.read_text('utf-8')); manifest=json.loads((build/'manifest.json').read_text('utf-8'))
    if prior['source_build']!=str(build) or prior['modified_bin_sha256']!=manifest['modified_bin']['sha256']:
        raise ValueError('Baseline belongs to another build')
    arc=(build/'modified.arc').read_bytes()
    if digest(build/'modified.arc')!=manifest['modified_archive_sha256']:raise ValueError('Changed build archive')
    entries=psx_arc(arc)
    def entry(kind):
        e=next(e for e in entries if e['type']==hex(kind));return arc[e['offset']:e['offset']+e['size']]
    gfx,parts,palette=entry(2),entry(3),entry(9)[:32]; words=struct.unpack('<16H',palette)
    bank_index=1 if special_bank else 0;parts_index=5 if special_bank else 0
    bank=graphics_bank(gfx,bank_index)
    if special_bank and not manifest.get('bank1_frame_inputs'):raise ValueError('Build has no supported bank1 artwork')
    mode=mobility or ('launch_hurt' if launch_hurt else 'hurt' if hurt else 'low_hp_idle' if low_hp_idle else 'wall_saber' if wall_saber else 'air_slash' if air_slash else 'ground_slash' if ground_slash else 'wall' if wall else 'idle' if idle else 'run' if run_direction else 'dash' if dash else 'jump')
    from scripts.build_riko_idle import GROUND_SLASH_BODY_FRAMES,AIR_SLASH_BODY_FRAMES
    if air_spin:mode='air_spin'
    if ice:mode='ice'
    if rise:mode='rise'
    if burst:mode='burst'
    if thrust:mode='thrust'
    if dashslash:mode='dashslash'
    if beam_in:mode='beam_in'
    if victory:mode='victory'
    from scripts.build_riko_idle import SHIPPUUGA_BODY
    from src.psx_raijingeki import BODY as THRUST_BODY
    numbers={'idle':[0,1,2,146,147,148], 'run':[3,4,5,6,*range(7,21),147],
             'dash':[3,4,5,6,*range(44,53),147], 'jump':[5,6,*range(21,35),147],
             'wall':[22,23,*range(35,44),147], 'ground_slash':[*sorted(GROUND_SLASH_BODY_FRAMES),147],
             'air_slash':[21,22,23,32,33,34,*sorted(AIR_SLASH_BODY_FRAMES),147],
             'wall_saber':[50,51,53,54,56,57,59,61,63,65], 'low_hp_idle':list(range(149,155)), 'hurt':[135,136,137,138,147],
             'double_jump':[22,23], 'air_dash':list(range(44,49)), 'launch_hurt':[135,*range(139,146)],
             'air_spin':[132,160,*range(161,176,2)],'ice':[86,87,95,98,*range(132,144)],'rise':[86,87,*range(144,161,2)],'burst':list(range(177,190)),'thrust':sorted(THRUST_BODY),'dashslash':sorted(SHIPPUUGA_BODY),'beam_in':list(range(247,254))+[147],'victory':list(range(9))}[mode]
    if air_spin and not set(map(str,numbers))<=manifest['bank1_frame_inputs'].keys():raise ValueError('Build has no complete spin art')
    animation_ids=(99,) if mobility=='double_jump' else (18,19) if mobility=='air_dash' else (5,33,34,36,37) if hurt else (6,) if low_hp_idle else (94,) if wall_saber else (5,10,11,12,91,92) if air_slash else (5,88,89,90) if ground_slash else (5,7,8,9,10,11,12,13,14,15,16,17,18,19)
    if launch_hurt:animation_ids=(34,)
    if air_spin:animation_ids=(100,)
    if ice:animation_ids=(97,98)
    if rise:animation_ids=(101,102)
    if burst:animation_ids=(103,)
    if thrust:animation_ids=(95,96)
    if dashslash:animation_ids=(104,)
    if beam_in:animation_ids=(2,5)
    if victory:animation_ids=(3,39,40)
    out=new_run(ROOT,project,mode+'_runtime'); expected={}; pictures={}
    for n in numbers:
        f=bank['frames'][n];raw=decode_stream(gfx,f['offset'],f['limit'],f['tile_count']*128).data
        indices,size,_,_=compose_indices(raw,f['tile_count'],composition_frame(parts,parts_index,n))
        expected[n]=raw
        if not launch_hurt:pictures[n]=save_image(indices,size,words,out/f'expected_{n:03d}.png')
    user,window=checked_window(prior['pid'])
    if not observe:
        user.ShowWindowAsync(window,9);user.SetForegroundWindow(window);time.sleep(.2)
        if user.GetForegroundWindow()!=window:raise RuntimeError('No emulator focus')
    kernel=ctypes.WinDLL('kernel32',use_last_error=True)
    kernel.OpenProcess.argtypes=[wintypes.DWORD,wintypes.BOOL,wintypes.DWORD];kernel.OpenProcess.restype=wintypes.HANDLE
    kernel.ReadProcessMemory.argtypes=[wintypes.HANDLE,ctypes.c_void_p,ctypes.c_void_p,ctypes.c_size_t,ctypes.POINTER(ctypes.c_size_t)]
    kernel.CloseHandle.argtypes=[wintypes.HANDLE]
    handle=kernel.OpenProcess(0x410,False,prior['pid'])
    if not handle:raise OSError('Read-only process open failed')
    def read(address,length):
        buffer=ctypes.create_string_buffer(length);count=ctypes.c_size_t()
        if not kernel.ReadProcessMemory(handle,address,buffer,length,ctypes.byref(count)) or count.value!=length:
            raise OSError('Short process memory read')
        return buffer.raw
    base=prior['ram_host_address'];video=prior['vram_host_address']
    scan=0x4b if run_direction=='left' else 0x4d if run_direction=='right' else 0x2d if dash else 0x2c
    input_flags=9 if run_direction else 8
    if project=='ver_rin_nana':
        # This isolated session uses the user's reset pad: cross=jump, circle=dash.
        # Read its actual scan codes; the first project's historical defaults differ.
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER,r'Software\epsxe\config') as reg:
            pad=list(map(int,winreg.QueryValueEx(reg,'Pad1')[0].split(',')))
        if len(pad)<14:raise ValueError('Incomplete controller mapping')
        mapped=pad[0 if run_direction=='left' else 1 if run_direction=='right' else 5 if dash else 6]
        if not 1 <= mapped <= 255:raise ValueError('Unsupported controller scan')
        scan=mapped&127;input_flags=8|int(bool(mapped&128))
    event=Input();event.type=1;event.data.key=KeyInput(0,scan,input_flags,0,0)
    def key(down):
        event.data.key.flags=input_flags if down else input_flags|2
        if user.SendInput(1,ctypes.byref(event),ctypes.sizeof(event))!=1:raise OSError('Key input failed')
    samples={n:[] for n in numbers};trace=[];last_sample={};start=time.monotonic();held=False
    try:
        player=read(base+0x1418c8,0xe4);pointer=struct.unpack_from('<I',player,0x38)[0]&0x1fffff
        starting_boss_flags=player[0xb9]
        if (air_spin or ice or rise or burst or thrust or dashslash or mobility) and not starting_boss_flags & (128 if dashslash else 1 if thrust else 32 if burst else 8 if rise else 2 if ice else 4 if air_spin or mobility=='double_jump' else 0x10):
            raise ValueError('Required mobility technique is not unlocked')
        baseline_banks=[graphics_bank(gfx,0),bank] if special_bank else [bank]
        if player[2]!=1 or not any(read(base+pointer,b['end']-b['base'])==gfx[b['base']:b['end']] for b in baseline_banks):
            raise ValueError('Baseline RAM address no longer matches this build')
        # 이동은 한 번, 점프/대시는 두 번 입력. 충돌 판정/게임 RAM에는 쓰지 않는다.
        while time.monotonic()-start<(15 if observe else 8.5 if idle else 5):
            elapsed=time.monotonic()-start
            hold=run_hold if run_direction else dash_hold if dash else .8
            wanted=not (idle or observe) and ((.15<=elapsed<.15+hold) or (not run_direction and 2.15<=elapsed<2.15+hold))
            if wanted!=held:
                if user.GetForegroundWindow()!=window:raise RuntimeError('Focus changed; stop input')
                key(wanted);held=wanted
            player=read(base+0x1418c8,0xe4);n=player[0x47];aid=player[0x17]
            state=[player[2],player[5],aid,n,player[0x44],player[0x45],struct.unpack_from('<i',player,0x20)[0]]
            if not trace or trace[-1][1:]!=state:trace.append([round(elapsed,5),*state])
            facing_ok=hurt_facing is None or bool(player[0x15]&0x40)==(hurt_facing=='right')
            if facing_ok and n in expected and aid in animation_ids and len(samples[n])<10 and elapsed-last_sample.get(n,-1)>.011:
                decoded=read(base+0x16dea8,len(expected[n]));vram=read(video,1048576)
                after=read(base+0x1418c8,0xe4)
                pointer=struct.unpack_from('<I',player,0x38)[0]&0x1fffff
                bank_ok=not special_bank or read(base+pointer,bank['end']-bank['base'])==gfx[bank['base']:bank['end']]
                if (after[0x17],after[0x47])==(aid,n) and bank_ok:
                    samples[n].append((elapsed,player,decoded,vram));last_sample[n]=elapsed
            time.sleep(.003)
    finally:
        try:
            if not (idle or observe):key(False)
        finally:kernel.CloseHandle(handle)
    write_json(out/'player_trace.json',{'columns':['seconds','character','action','animation','frame','remaining_ticks','event','x_velocity_fixed16'],
                                     'rows':trace,'input_scan':None if idle or observe else scan,
                                     'hold_seconds':0 if idle or observe else hold,'jump_count':2 if mode=='jump' and not observe else 0,
                                     'run_direction':run_direction,'mode':mode})
    results={}
    for n in numbers:
        successes=[];diagnostics=[]
        for i,(elapsed,player,decoded,vram) in enumerate(samples[n]):
            ram_ok=decoded==expected[n];cursor=0;upload_ok=True
            count=bank['frames'][n]['tile_count']
            for first in range(0,count,16):
                width=min(16,count-first)*8
                for y in range(16):
                    pos=(first//16*16+y)*2048+640
                    if vram[pos:pos+width]!=expected[n][cursor:cursor+width]:upload_ok=False
                    cursor+=width
            pal_ok=vram[480*2048:480*2048+32]==palette
            clut_base=struct.unpack_from('<H',player,0x42)[0]
            if launch_hurt:
                pal_ok=pal_ok and clut_base==0x7800
                indices,size,_,_=compose_indices(expected[n],count,composition_frame(parts,parts_index,n))
                live_words=struct.unpack_from('<64H',vram,480*2048)
                pictures[n]=save_image(indices,size,live_words,out/f'expected_{n:03d}.png')
            matches=[]
            if upload_ok and pal_ok:
                for page in (0,256):
                    pic=framebuffer(vram,0,page);found=match_sprite(pic,pictures[n])
                    if hurt_facing:found=[m for m in found if m['flip_x']==(hurt_facing=='right')]
                    if found:
                        pic.save(out/f'actual_{n:03d}_{page}.png')
                        matches.extend({'page_y':page,**m} for m in found)
            diagnostics.append({'seconds':elapsed,'ram_equal':ram_ok,'vram_equal':upload_ok,'palette_equal':pal_ok,
                                'player_clut_base':clut_base,'clut2_words':list(live_words[32:48]) if launch_hurt else None,
                                'ram_different_bytes':sum(a!=b for a,b in zip(decoded,expected[n])),
                                'render_matches':len(matches)})
            if matches:
                (out/f'vram_render_{n:03d}.bin').write_bytes(vram)
                (out/f'vram_render_player_{n:03d}.bin').write_bytes(player)
            if matches and ram_ok:
                (out/f'vram_{n:03d}.bin').write_bytes(vram);(out/f'player_{n:03d}.bin').write_bytes(player)
                successes=matches;break
        if not successes and samples[n]:
            _,player,decoded,vram=samples[n][len(samples[n])//2]
            (out/f'diagnostic_vram_{n:03d}.bin').write_bytes(vram)
            (out/f'diagnostic_player_{n:03d}.bin').write_bytes(player)
            for page in (0,256):framebuffer(vram,0,page).save(out/f'diagnostic_{n:03d}_{page}.png')
        results[str(n)]={'observed':bool(samples[n]),'verified':bool(successes),'matches':successes,'samples':diagnostics,
                        'vram_render_verified':any(d['vram_equal'] and d['palette_equal'] and d['render_matches'] for d in diagnostics)}
    # 짧은 동작은 RAM/텍스처가 다음 자세로 넘어간 뒤 화면 버퍼에 나타날 수 있다.
    # 기존 동시 일치 판정은 유지하고, 같은 실행의 시점이 다른 증거를 따로 기록한다.
    pipeline_verified=[]
    for n in numbers:
        record=results[str(n)]
        if launch_hurt:continue # Dynamic CLUT snapshots must never be mixed across samples.
        if record['verified'] or not any(d['ram_equal'] and d['vram_equal'] and d['palette_equal'] for d in record['samples']):
            continue
        evidence_found=None
        for sampled_frame,group in samples.items():
            for elapsed,player,decoded,vram in group:
                for page in (0,256):
                    pic=framebuffer(vram,0,page);found=match_sprite(pic,pictures[n])
                    if hurt_facing:found=[m for m in found if m['flip_x']==(hurt_facing=='right')]
                    if found:
                        pic.save(out/f'pipeline_actual_{n:03d}_{page}.png')
                        (out/f'pipeline_vram_{n:03d}.bin').write_bytes(vram)
                        (out/f'pipeline_player_{n:03d}.bin').write_bytes(player)
                        evidence_found={'render_seconds':elapsed,'ram_frame_at_render_capture':sampled_frame,
                            'matches':[{'page_y':page,**m} for m in found],
                            'same_sample_ram_upload_render':False,
                            'ram_upload_evidence':'Earlier listed samples in this same verified process/build'}
                        break
                if evidence_found:break
            if evidence_found:break
        record['pipeline_evidence']=evidence_found
        if evidence_found:pipeline_verified.append(n)
    write_json(out/'verification.local.json',{'source_build':str(build),'modified_bin_sha256':manifest['modified_bin']['sha256'],
        'pid':prior['pid'],'baseline':str(evidence),'ram_host_address':base,'vram_host_address':video,
        'frames':results,'verified_frames':[int(n) for n,r in results.items() if r['verified']],
        'unverified_frames':[int(n) for n,r in results.items() if not r['verified']],
        'pipeline_verified_frames':pipeline_verified,
        'vram_render_verified_frames':[int(n) for n,r in results.items() if r['vram_render_verified']],
        'process_memory_written':False,'focus_changed':not observe,'input_sent':not (idle or observe),'observe_only':observe,
        'capture_kind':mode,'graphics_bank':bank_index,'parts_bank':parts_index,'run_direction':run_direction,
        'hurt_facing':hurt_facing,
        'mobility':mobility,'observed_animation_filter':list(animation_ids),'starting_boss_flags':starting_boss_flags,
        'launch_hurt':launch_hurt,'clut2_render_source':'same-sample VRAM x32 y480' if launch_hurt else None,
        'save_state_use':'See emulator session; memory capture alone cannot establish boot history.'})
    print(json.dumps({'output':str(out),'verified':[n for n,r in results.items() if r['verified']],
                      'unverified':[n for n,r in results.items() if not r['verified']],
                      'pipeline_verified':pipeline_verified}))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--build',type=Path,required=True)
    parser.add_argument('--project',choices=['ver_buki_riko','ver_rin_nana'],default='ver_buki_riko')
    parser.add_argument('--baseline',type=Path,required=True)
    modes=parser.add_mutually_exclusive_group();modes.add_argument('--idle',action='store_true')
    modes.add_argument('--run-direction',choices=('left','right'));modes.add_argument('--dash',action='store_true')
    modes.add_argument('--wall',action='store_true',help='Observe original wall animation IDs13..15 without sending input')
    modes.add_argument('--ground-slash',action='store_true',help='Observe original ground saber IDs88..90 without sending input')
    modes.add_argument('--air-slash',action='store_true',help='Observe original airborne/landing saber IDs91/92 without sending input')
    modes.add_argument('--wall-saber',action='store_true',help='Observe bank1/parts5 wall saber ID94 without sending input')
    modes.add_argument('--ice',action='store_true',help='Observe unlocked bank1/parts5 ice body IDs97/98 without sending input')
    modes.add_argument('--rise',action='store_true',help='Observe unlocked bank1/parts5 rising saber IDs101/102 without sending input')
    modes.add_argument('--dashslash',action='store_true',help='Observe Shippuuga animation104 without input')
    modes.add_argument('--victory',action='store_true',help='Observe shared victory and departure body animations3/39/40 without input')
    modes.add_argument('--beam-in',action='store_true',help='Observe arrival animation2 and approved idle recovery without input')
    modes.add_argument('--thrust',action='store_true',help='Observe Raijingeki animations95/96 without input')
    modes.add_argument('--burst',action='store_true',help='Observe unlocked bank1/parts5 Rakuhouha ID103 without sending input')
    modes.add_argument('--air-spin',action='store_true',help='Observe unlocked bank1/parts5 spin ID100 without sending input')
    modes.add_argument('--low-hp-idle',action='store_true',help='Observe bank0 low-health idle ID6 without sending input')
    modes.add_argument('--hurt',action='store_true',help='Observe ordinary hurt/stun IDs33/34/36/37 and normal idle recovery without input')
    modes.add_argument('--launch-hurt',action='store_true',help='Observe launch ID34 with separate same-sample CLUT0/2 colors')
    modes.add_argument('--mobility',choices=('double_jump','air_dash'),help='Observe unlocked ID99 or IDs18/19; requires --observe and original unlock flags')
    parser.add_argument('--hurt-facing',choices=('left','right'),help='Require matching player facing and framebuffer reflection')
    parser.add_argument('--run-hold',type=float,default=.75)
    parser.add_argument('--dash-hold',type=float,default=.45)
    parser.add_argument('--observe',action='store_true',help='Observe gameplay for 15 seconds without focus changes or key input')
    args=parser.parse_args();capture(args.build,args.baseline,args.idle,args.run_direction,args.dash,args.run_hold,args.dash_hold,args.observe,args.wall,args.ground_slash,args.air_slash,args.wall_saber,args.low_hp_idle,args.hurt,args.hurt_facing,args.mobility,args.launch_hurt,args.air_spin,args.ice,args.rise,args.burst,args.thrust,args.dashslash,args.beam_in,args.victory,project=args.project)
