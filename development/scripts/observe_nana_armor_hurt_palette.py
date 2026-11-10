"""사용자 조작 중 피격 화면/CLUT를 읽기 전용 관찰한다. 키·저장·포커스 변경 없음."""
import argparse,ctypes,json,struct,sys,time,hashlib
from ctypes import wintypes
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import scripts.emulator_session as em
from scripts.prepare_nana_fourth_pilot import entry,require,write
from scripts.project import digest,new_run
from src.psx_player import graphics_bank,decode_stream
from src.epsxe_state import framebuffer

def observe(session,discovery,seconds,mode='hurt'):
    require(mode in ('hurt','special','elemental','hover'),'Unsupported observation mode')
    require(1<=seconds<=45,'Observation must be <=45 seconds')
    session,discovery=session.resolve(),discovery.resolve()
    require(session.is_relative_to(ROOT/'work/ver_rin_nana/emulator_sessions') and discovery.is_relative_to(ROOT/'work/ver_rin_nana/live_poc'),'Unexpected paths')
    s=json.loads((session/'session.local.json').read_text('utf8'));d=json.loads(discovery.read_text('utf8'));build=Path(s['cue']).parent
    require(s['pid']==d['pid'] and s['bin_sha256']==d['modified_bin_sha256']==digest(build/'rin_nana.bin'),'Session mismatch')
    arc=(build/'modified.arc').read_bytes();m=json.loads((build/'manifest.json').read_text('utf8'));require(digest(build/'modified.arc')==m['modified_archive_sha256'],'ARC changed')
    em.EMULATOR=ROOT/'work/ver_rin_nana/emulator/ePSXe.exe';em.checked_window(s['pid'])
    k=ctypes.WinDLL('kernel32',use_last_error=True);k.OpenProcess.argtypes=[wintypes.DWORD,wintypes.BOOL,wintypes.DWORD];k.OpenProcess.restype=wintypes.HANDLE
    k.ReadProcessMemory.argtypes=[wintypes.HANDLE,ctypes.c_void_p,ctypes.c_void_p,ctypes.c_size_t,ctypes.POINTER(ctypes.c_size_t)];k.CloseHandle.argtypes=[wintypes.HANDLE]
    h=k.OpenProcess(0x410,False,s['pid']);require(bool(h),'Read-only process unavailable')
    def read(addr,size):
        b=ctypes.create_string_buffer(size);got=ctypes.c_size_t()
        return b.raw if k.ReadProcessMemory(h,addr,b,size,ctypes.byref(got)) and got.value==size else b''
    out=new_run(ROOT,'ver_rin_nana','nana_armor_hover' if mode=='hover' else 'nana_armor_elemental' if mode=='elemental' else ('nana_armor_special' if mode=='special' else 'nana_armor_hurt_palette'));rows=[];trace=[];seen=set();cached={};g=entry(arc,2);bank=graphics_bank(g,0,allow_bank_aliases=True)
    wanted=[93,94]+list(range(221,231)) if mode=='hover' else [95,96,100,101,102,103,104,231,232] if mode=='elemental' else [88,89,90,91,97,98,99] if mode=='special' else list(range(106,115))+list(range(120,126))+list(range(233,237))
    try:
        bases=[b for b in d['ram_candidates'] if all(read(b,0x200000).find(entry(arc,t))>=0 for t in (2,3,9))]
        require(len(bases)==1,'Current RAM assets not unique');base=bases[0];videos=d['vram_candidates'];start=time.monotonic()
        print(json.dumps({'observing':str(out),'seconds':seconds,'input_sent':False}),flush=True)
        while time.monotonic()-start<seconds:
            player=read(base+0x1418c8,0xe4)
            if len(player)!=0xe4:break
            n=player[0x47];clut=struct.unpack_from('<H',player,0x42)[0];item=[player[0x17],n,player[0x5c],player[0xa7],clut]
            if not trace or trace[-1][1:]!=item:trace.append([round(time.monotonic()-start,4),*item])
            if player[2]!=0 or n>=len(bank['frames']) or (rows and n not in wanted):time.sleep(.004);continue
            if n not in cached:
                f=bank['frames'][n];cached[n]=(f,decode_stream(g,f['offset'],f['limit'],f['tile_count']*128).data)
            f,raw=cached[n]
            if read(base+0x16dea8,len(raw))!=raw:time.sleep(.004);continue
            for video in videos:
                vram=read(video,1048576)
                if len(vram)!=1048576:continue
                upload=bytearray()
                for first in range(0,f['tile_count'],16):
                    width=min(16,f['tile_count']-first)*8
                    for y in range(16):pos=(first//16*16+y)*2048+640;upload.extend(vram[pos:pos+width])
                if bytes(upload)!=raw:continue
                after=read(base+0x1418c8,0xe4)
                if after[0x47]!=n or after[0x42:0x44]!=player[0x42:0x44]:continue
                palettes=vram[480*2048:482*2048];tag=(n,player[0xa7],clut,hashlib.sha256(palettes).hexdigest())
                if tag in seen:continue
                seen.add(tag);i=len(rows);prefix=f'{i:02}_{n:03}_clut{clut:04x}'
                (out/(prefix+'_player.bin')).write_bytes(player);(out/(prefix+'_vram.bin')).write_bytes(vram)
                for page in (0,240,256):framebuffer(vram,0,page).save(out/f'{prefix}_page{page}.png')
                rows.append({'prefix':prefix,'seconds':round(time.monotonic()-start,4),'frame':n,'animation':player[0x17],'hp':player[0x5c],'armor':player[0xa7],'arm_type':player[0xb8],'weapon':player[0x93],'body_clut':clut,'ram_vram_texture_equal':True,'ram_host':base,'vram_host':video,'palettes_480_hex':vram[480*2048:480*2048+256].hex()});videos=[video]
                print(json.dumps({'captured':prefix,'hp':player[0x5c]}),flush=True)
                break
            if len(rows)>=40:break
            time.sleep(.004)
    finally:
        k.CloseHandle(h);write(out/'observation.json',{'session':session.relative_to(ROOT).as_posix(),'build':build.relative_to(ROOT).as_posix(),'bin_sha256':s['bin_sha256'],'samples':rows,'trace_columns':['seconds','animation','frame','hp','armor','clut'],'trace':trace,'input_sent':False,'focus_changed':False,'process_memory_written':False,'save_files_written':False,'mode':mode})
    print(json.dumps({'output':str(out),'frames':sorted({q['frame'] for q in rows}),'sample_count':len(rows)}))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--session',type=Path,required=True);p.add_argument('--discovery',type=Path,required=True);p.add_argument('--seconds',type=float,default=30);p.add_argument('--mode',choices=('hurt','special','elemental','hover'),default='hurt');a=p.parse_args();observe(a.session,a.discovery,a.seconds,a.mode)
