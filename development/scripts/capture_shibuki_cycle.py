"""일반 방향키로 Shibuki 이동을 실행하고 RAM/VRAM/화면을 읽기 전용 대조한다."""
import argparse,ctypes,json,struct,sys,time
from ctypes import wintypes
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.emulator_session import checked_window,Input,KeyInput
from scripts.project import new_run,write_json,digest
from scripts.discover_inputs import psx_arc
from scripts.extract_zero import save_image
from src.psx_player import graphics_bank,composition_frame,decode_stream,compose_indices
from src.epsxe_state import framebuffer,match_sprite

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--evidence',type=Path,required=True)
    p.add_argument('--direction',choices=['left','right'],required=True);p.add_argument('--hold',type=float,default=.8)
    p.add_argument('--idle',action='store_true');p.add_argument('--shoot',action='store_true');p.add_argument('--hold-fire',action='store_true')
    p.add_argument('--standing',action='store_true',help='Tap facing direction, then shoot and recover without moving')
    p.add_argument('--air',action='store_true',help='Three vertical jumps with the ordinary jump key')
    p.add_argument('--dash',action='store_true',help='Two ground dashes with the ordinary dash key')
    p.add_argument('--wall',action='store_true',help='Observe/control twelve wall poses near an already reached wall')
    p.add_argument('--diagnostic-screens',action='store_true',help='Save distinct captured framebuffers for offline mismatch analysis')
    p.add_argument('--fire-delay',type=float,default=.45);p.add_argument('--fire-period',type=float,default=.18);args=p.parse_args()
    if args.idle and args.shoot:raise ValueError('Choose idle or moving fire')
    if args.hold_fire and not args.shoot:raise ValueError('Hold-fire requires shooting')
    if args.standing and (not args.shoot or args.idle or args.hold_fire):raise ValueError('Standing requires --shoot without idle/hold-fire')
    if args.air and (args.idle or args.standing or args.hold_fire):raise ValueError('Air cannot combine idle, standing or hold-fire')
    if args.dash and (args.air or args.idle or args.standing or args.hold_fire):raise ValueError('Dash requires its own ordinary input mode')
    if args.wall and (args.dash or args.air or args.idle or args.standing or args.hold_fire):raise ValueError('Wall requires its own ordinary input mode')
    if args.dash and args.hold>.5:raise ValueError('Dash hold limited to .5 seconds for local traversal')
    if not .15<=args.hold<=2:raise ValueError('Hold must be .15..2 seconds')
    if not .15<=args.fire_delay<=2 or not .1<=args.fire_period<=2:raise ValueError('Invalid firing interval')
    evidence=args.evidence.resolve()
    if not evidence.is_relative_to(ROOT/'work/ver_buki_riko/live_poc'):raise ValueError('Unexpected baseline')
    prior=json.loads(evidence.read_text());build=Path(prior['source_build']);manifest=json.loads((build/'manifest.json').read_text())
    if manifest.get('task')!='x_shibuki' or prior['modified_bin_sha256']!=manifest['modified_bin']['sha256'] or digest(build/'modified.arc')!=manifest['modified_archive_sha256']:raise ValueError('Baseline build mismatch')
    arc=(build/'modified.arc').read_bytes();entries=psx_arc(arc)
    def entry(t):
        e=next(e for e in entries if int(e['type'],16)==t);return arc[e['offset']:e['offset']+e['size']]
    gfx,parts,palette=entry(2),entry(3),entry(9)[:32];words=struct.unpack('<16H',palette);bank=graphics_bank(gfx,0,allow_bank_aliases=True)
    numbers=[85,86,87,92] if args.standing else ([0,115,116,117,118,119] if args.idle else list(range(2 if args.shoot else 1,33,2)))
    if args.air:numbers=list(range(34 if args.shoot else 33,55,2))
    if args.dash:numbers=list(range(68 if args.shoot else 67,85,2))
    if args.wall:numbers=list(range(56 if args.shoot else 55,67,2))
    out=new_run(ROOT,'ver_buki_riko','shibuki_run_runtime');expected={};pictures={}
    for n in numbers:
        f=bank['frames'][n];raw=decode_stream(gfx,f['offset'],f['limit'],f['tile_count']*128).data;expected[n]=raw
        indices,size,_,_=compose_indices(raw,f['tile_count'],composition_frame(parts,0,n));pictures[n]=save_image(indices,size,words,out/f'expected_{n:03d}.png')
    user,window=checked_window(prior['pid']);kernel=ctypes.WinDLL('kernel32',use_last_error=True)
    kernel.OpenProcess.argtypes=[wintypes.DWORD,wintypes.BOOL,wintypes.DWORD];kernel.OpenProcess.restype=wintypes.HANDLE
    kernel.ReadProcessMemory.argtypes=[wintypes.HANDLE,ctypes.c_void_p,ctypes.c_void_p,ctypes.c_size_t,ctypes.POINTER(ctypes.c_size_t)]
    kernel.CloseHandle.argtypes=[wintypes.HANDLE];handle=kernel.OpenProcess(0x410,False,prior['pid'])
    if not handle:raise OSError('Cannot open read-only process')
    def read(address,size):
        buf=ctypes.create_string_buffer(size);count=ctypes.c_size_t()
        if not kernel.ReadProcessMemory(handle,address,buf,size,ctypes.byref(count)) or count.value!=size:raise OSError('Short process read')
        return buf.raw
    base,video=prior['ram_host_address'],prior['vram_host_address'];held=False;shot_held=False;jump_held=False;dash_held=False
    def key(down,shoot=False,jump=False,dash=False):
        scan=0x2d if dash else (0x2c if jump else (0x1f if shoot else (0x4b if args.direction=='left' else 0x4d)))
        ev=Input();ev.type=1;ev.data.key=KeyInput(0,scan,(8 if shoot or jump or dash else 9)|(0 if down else 2),0,0)
        if user.SendInput(1,ctypes.byref(ev),ctypes.sizeof(ev))!=1:raise OSError('Input failed')
    samples={n:[] for n in numbers};trace=[]
    try:
        player=read(base+0x1418c8,0xe4);ptr=struct.unpack_from('<I',player,0x38)[0]&0x1fffff
        if player[2]!=0 or read(base+ptr,bank['end']-bank['base'])!=gfx[bank['base']:bank['end']]:raise ValueError('Current RAM is not patched X')
        user.ShowWindowAsync(window,9);user.SetForegroundWindow(window);time.sleep(.15)
        if user.GetForegroundWindow()!=window:raise RuntimeError('No emulator focus')
        start=time.monotonic();last_wall_jump=-10;wall_jump_until=0
        while time.monotonic()-start<(10.0 if args.wall else (4.2 if args.dash else (7.1 if args.air else (8.5 if args.idle else args.hold+1)))):
            elapsed=time.monotonic()-start;wanted=not args.idle and .15<=elapsed<.15+args.hold
            if args.standing:wanted=.05<=elapsed<.10
            if args.air:wanted=.05<=elapsed<.10
            if args.dash:wanted=.05<=elapsed<.10
            if args.wall:wanted=.15<=elapsed<9.5
            if user.GetForegroundWindow()!=window:raise RuntimeError('Focus changed; stop input')
            if wanted!=held:key(wanted);held=wanted
            # Fire just before movement so the short startup poses are observable
            # after the muzzle flash, then pulse again during the running cycle.
            fire=args.shoot and (elapsed<.03 or (wanted and elapsed>=args.fire_delay and (elapsed-args.fire_delay)%args.fire_period<.04))
            if args.hold_fire:fire=elapsed<.15+args.hold
            if args.standing:fire=.40<=elapsed and (elapsed-.40)%1.10<.08
            if args.air:
                phase=(elapsed-.25)%2.1
                jump=elapsed>=.25 and phase<args.hold
                if jump!=jump_held:key(jump,jump=True);jump_held=jump
                fire=args.shoot and elapsed>=.15 and ((elapsed-.15)%args.fire_period<.04)
            if args.dash:
                dash=elapsed>=.25 and (elapsed-.25)%2.1<args.hold
                if dash!=dash_held:key(dash,dash=True);dash_held=dash
                fire=args.shoot and elapsed>=.15 and ((elapsed-.15)%args.fire_period<.04)
            if args.wall:
                wall_player=read(base+0x1418c8,0xe4)
                grounded=bool(wall_player[0x89]&8);aid_now=wall_player[0x17]
                if wall_player[2]!=0 or not 0<wall_player[0x5c]<=32:raise RuntimeError('Wall trial lost active living X')
                if elapsed>.4 and elapsed-last_wall_jump>2.0 and (grounded or aid_now in (13,15,125,127)):
                    last_wall_jump=elapsed;wall_jump_until=elapsed+.28
                jump=elapsed<wall_jump_until
                if jump!=jump_held:key(jump,jump=True);jump_held=jump
                fire=args.shoot and elapsed>=.15 and ((elapsed-.15)%args.fire_period<.05)
            if fire!=shot_held:key(fire,True);shot_held=fire
            player=read(base+0x1418c8,0xe4);n,aid=player[0x47],player[0x17]
            row=[player[2],aid,n,bool(player[0x15]&0x40),player[0x44],struct.unpack_from('<i',player,8)[0],struct.unpack_from('<i',player,12)[0]]
            if not trace or trace[-1][1:]!=row:trace.append([round(elapsed,5),*row])
            accepted_animations=(88,94) if args.standing else ((5,) if args.idle else ((119,120) if args.shoot else (7,8)))
            if args.air:accepted_animations=(122,123,124) if args.shoot else (10,11,12)
            if args.dash:accepted_animations=(128,129) if args.shoot else (16,17)
            if args.wall:accepted_animations=(125,126,127) if args.shoot else (13,14,15)
            if n in expected and aid in accepted_animations and len(samples[n])<64:
                decoded=read(base+0x16dea8,len(expected[n]));vram=read(video,1048576);after=read(base+0x1418c8,0xe4)
                if (after[2],after[0x17],after[0x47])==(0,aid,n):samples[n].append((elapsed,player,decoded,vram))
            time.sleep(.003)
    finally:
        try:
            if held:key(False)
            if shot_held:key(False,True)
            if jump_held:key(False,jump=True)
            if dash_held:key(False,dash=True)
        finally:kernel.CloseHandle(handle)
    results={};wanted_flip=args.direction==('left' if args.wall else 'right')
    for n,group in samples.items():
        diagnostics=[];success=None
        for elapsed,player,decoded,vram in group:
            cursor=0;upload=True;count=bank['frames'][n]['tile_count']
            for first in range(0,count,16):
                width=min(16,count-first)*8
                for y in range(16):
                    pos=(first//16*16+y)*2048+640
                    if vram[pos:pos+width]!=expected[n][cursor:cursor+width]:upload=False
                    cursor+=width
            ram=decoded==expected[n];pal=vram[480*2048:480*2048+32]==palette;matches=[]
            if upload and pal and ram:
                for page in (0,256):
                    picture=framebuffer(vram,0,page);found=[m for m in match_sprite(picture,pictures[n]) if m['flip_x']==wanted_flip]
                    if found:
                        picture.save(out/f'actual_{n:03d}_{page}.png');matches.extend({'page_y':page,**m} for m in found)
            if upload and pal and ram and not (out/f'diagnostic_vram_{n:03d}.bin').exists():
                (out/f'diagnostic_vram_{n:03d}.bin').write_bytes(vram)
                (out/f'diagnostic_player_{n:03d}.bin').write_bytes(player)
                for page in (0,256):framebuffer(vram,0,page).save(out/f'diagnostic_{n:03d}_{page}.png')
            diagnostics.append({'seconds':elapsed,'ram_equal':ram,'vram_equal':upload,'palette_equal':pal,'render_matches':len(matches)})
            if matches:
                (out/f'vram_{n:03d}.bin').write_bytes(vram);(out/f'player_{n:03d}.bin').write_bytes(player);success=matches;break
        results[str(n)]={'verified':bool(success),'matches':success or [],'observed':bool(group),'samples':diagnostics}
    # GPU buffers can display the preceding pose while RAM already contains the next.
    # Require a valid RAM/upload observation for the target, then match its exact
    # opaque pixels against separately captured buffers. Record this distinction.
    buffers=[];seen_buffers=set();observed_palettes={palette}
    import hashlib
    for source_n,group in samples.items():
        if args.shoot:
            observed_palettes.update(v[480*2048:480*2048+32] for _,_,_,v in group)
            for _,player,_,v in group:
                clut=struct.unpack_from('<H',player,0x42)[0]
                if clut&0x8000:clut=0x7840
                pos=(clut>>6)*2048+(clut&63)*32
                observed_palettes.add(v[pos:pos+32])
        for elapsed,player,decoded,vram in group[::3]:
            if not args.shoot and vram[480*2048:480*2048+32]!=palette:continue
            for page in (0,256):
                picture=framebuffer(vram,0,page);key=hashlib.sha256(picture.tobytes()).digest()
                if key not in seen_buffers:buffers.append((source_n,elapsed,player,vram,page,picture));seen_buffers.add(key)
    for n in numbers:
        record=results[str(n)]
        if record['verified'] or not any(s['ram_equal'] and s['vram_equal'] for s in record['samples']):continue
        for palette_variant in [palette]+sorted(observed_palettes-{palette}):
            target_picture=pictures[n].copy();rgb=[]
            for word in struct.unpack('<16H',palette_variant):rgb.extend(((word&31)*255//31,((word>>5)&31)*255//31,((word>>10)&31)*255//31))
            target_picture.putpalette(rgb+[0]*(768-len(rgb)))
            for source_n,elapsed,player,vram,page,picture in buffers:
                matches=[m for m in match_sprite(picture,target_picture) if m['flip_x']==wanted_flip]
                if not matches:continue
                picture.save(out/f'actual_{n:03d}_{page}.png');(out/f'vram_{n:03d}.bin').write_bytes(vram);(out/f'player_{n:03d}.bin').write_bytes(player)
                record.update(verified=True,matches=[{'page_y':page,**m} for m in matches],display_and_upload_observed_separately=True,display_snapshot_ram_frame=source_n,display_snapshot_seconds=elapsed,render_palette_hex=palette_variant.hex(),render_palette_is_base=palette_variant==palette)
                break
            if record['verified']:break
    if args.diagnostic_screens:
        screens=[]
        for i,(source_n,elapsed,player,vram,page,picture) in enumerate(buffers):
            name=f'buffer_{i:03d}.png';picture.save(out/name)
            screens.append({'image':name,'source_ram_frame':source_n,'seconds':elapsed,'page_y':page})
        write_json(out/'diagnostic_screens.json',screens)
    write_json(out/'trace.json',{'columns':['seconds','character','animation','frame','facing_right','remaining_ticks','x_fixed16','y_fixed16'],'rows':trace})
    report={'source_build':str(build),'modified_bin_sha256':manifest['modified_bin']['sha256'],'pid':prior['pid'],
            'baseline':str(evidence),'direction':args.direction,'idle':args.idle,'shoot':args.shoot,'hold_fire':args.hold_fire,'input_hold':0 if args.idle else args.hold,
            'fire_delay':args.fire_delay,'fire_period':args.fire_period,'standing':args.standing,'air':args.air,'dash':args.dash,'wall':args.wall,
            'process_memory_written':False,'frames':results,'verified_frames':[int(n) for n,r in results.items() if r['verified']],
            'unverified_frames':[int(n) for n,r in results.items() if not r['verified']],
            'observed_palette_hex':[q.hex() for q in sorted(observed_palettes)]}
    report['observed_player_cluts']=sorted({struct.unpack_from('<H',player,0x42)[0] for group in samples.values() for _,player,_,_ in group})
    write_json(out/'verification.local.json',report);print(json.dumps({'output':str(out),'verified':report['verified_frames'],'unverified':report['unverified_frames']}))

if __name__=='__main__':main()
