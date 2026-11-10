"""Read-only Korean EXE/RAM/VRAM capture tied to the verified emulator build."""
import argparse, ctypes, json, struct, sys
from ctypes import wintypes
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.capture_poc_memory import Region
from scripts.emulator_session import checked_window
from scripts.project import digest, new_run
from scripts.prepare_riko_ui import entry
from src.epsxe_state import framebuffer
from scripts.verify_korean_runtime_page import native_draw_buffers

def main(session, label, cache=None,project='ver_buki_riko'):
    if project not in ('ver_buki_riko','ver_rin_nana'):raise ValueError('Unexpected project')
    session=session.resolve()
    if not session.is_relative_to(ROOT/'work'/project/'emulator_sessions'):raise ValueError('Unexpected session')
    import scripts.emulator_session as control
    if project=='ver_rin_nana':control.EMULATOR=ROOT/'work/ver_rin_nana/emulator/ePSXe.exe'
    rec=json.loads((session/'session.local.json').read_text('utf-8'));checked_window(rec['pid'])
    build=Path(rec['cue']).parent
    game=build/('shibuki_riko.bin' if project=='ver_buki_riko' else 'rin_nana.bin')
    if digest(game)!=rec['bin_sha256']:raise ValueError('Build differs')
    from scripts.prepare_rin_common import read_disc
    assets,_=read_disc(game,['SLUS_005.61','LOAD_U.ARC'])
    exe=assets['SLUS_005.61'];font=entry(assets['LOAD_U.ARC'],0x10001)
    ram_anchor=0x233c8;rn=exe[ram_anchor-0x10000+2048:ram_anchor-0x10000+2048+56]
    vn=font[3*128:4*128];va=(256+3)*2048+960*2
    k=ctypes.WinDLL('kernel32',use_last_error=True)
    k.OpenProcess.argtypes=[wintypes.DWORD,wintypes.BOOL,wintypes.DWORD];k.OpenProcess.restype=wintypes.HANDLE
    k.ReadProcessMemory.argtypes=[wintypes.HANDLE,ctypes.c_void_p,ctypes.c_void_p,ctypes.c_size_t,ctypes.POINTER(ctypes.c_size_t)]
    k.VirtualQueryEx.argtypes=[wintypes.HANDLE,ctypes.c_void_p,ctypes.POINTER(Region),ctypes.c_size_t];k.CloseHandle.argtypes=[wintypes.HANDLE]
    handle=k.OpenProcess(0x410,False,rec['pid'])
    if not handle:raise OSError('Read-only open failed')
    def read(addr,size):
        b=ctypes.create_string_buffer(size);got=ctypes.c_size_t()
        return b.raw if k.ReadProcessMemory(handle,addr,b,size,ctypes.byref(got)) and got.value==size else b''
    out=new_run(ROOT,project,'korean_runtime');rams=set();videos=set()
    try:
        if cache:
            old=json.loads(cache.read_text())
            if old['pid']!=rec['pid']:raise ValueError('Cache PID differs')
            rams.update(old['ram_bases']);videos.update(old['vram_bases'])
        else:
            address=0
            while address<0x100000000:
                r=Region()
                if not k.VirtualQueryEx(handle,address,ctypes.byref(r),ctypes.sizeof(r)):break
                lo=r.base or 0;end=lo+r.size
                if end<=address:break
                if r.state==0x1000 and not r.protect&0x100 and r.protect&255 in (2,4,8,32,64,128):
                    for start in range(lo,end,1048576):
                        blob=read(start,min(end-start,1048704))
                        for needle,adjust,found in ((rn,ram_anchor,rams),(vn,va,videos)):
                            pos=blob.find(needle)
                            while pos>=0:
                                base=start+pos-adjust
                                if base>0:found.add(base)
                                pos=blob.find(needle,pos+1)
                address=end
        rams={base for base in rams if all(read(base+a,32)==exe[a-0x10000+2048:a-0x10000+2080] for a in (0x233c8,0x23400,0xea20c))}
        videos={base for base in videos if all(read(base+(256+y)*2048+960*2,128)==font[y*128:(y+1)*128] for y in (2,3,4,5))}
        states=[];draw_buffers=[]
        for base in sorted(rams):
            ram=read(base,2097152)
            if len(ram)!=2097152:continue
            (out/f'ram_{base}.bin').write_bytes(ram)
            draw_buffers=native_draw_buffers(ram)
            states.append({'base':base,'glyph_count':struct.unpack_from('<H',ram,0x1397e0)[0],
                           'glyph_records':ram[0x1396cc:0x1396cc+240].hex(),
                           'player_character':ram[0x1418ca]})
        for base in sorted(videos):
            v=read(base,1048576)
            if len(v)!=1048576:continue
            (out/f'vram_{base}.bin').write_bytes(v)
            for buffer in draw_buffers:
                x,y,_,_=buffer['draw_clip']
                framebuffer(v,x*2,y).save(out/f'frame_{base}_{y}.png')
        report={'label':label,'session':str(session),'pid':rec['pid'],'bin_sha256':rec['bin_sha256'],
                'ram_bases':sorted(rams),'vram_bases':sorted(videos),'states':states,'framebuffer_draw_infos':draw_buffers,'process_memory_written':False,'keys_sent':False}
        (out/'evidence.json').write_text(json.dumps(report,indent=2));print(json.dumps({'output':str(out),'ram':sorted(rams),'vram':sorted(videos),'counts':[s['glyph_count'] for s in states]}))
        if not rams or not videos:raise RuntimeError('Native RAM/VRAM not found')
    finally:k.CloseHandle(handle)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--project',choices=['ver_buki_riko','ver_rin_nana'],default='ver_buki_riko');p.add_argument('--session',type=Path,required=True);p.add_argument('--label',required=True);p.add_argument('--cache',type=Path);a=p.parse_args();main(a.session,a.label,a.cache,a.project)
