"""격리 선택창의 RAM/VRAM을 읽기 전용 수집한다."""
import ctypes,json,runpy,sys
from ctypes import wintypes
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from scripts.capture_poc_memory import Region
from scripts.hud_underlay_verify import read_assets,digest
from scripts.prepare_riko_ui import entry
from scripts.verify_korean_runtime_page import native_draw_buffers
from src.epsxe_state import framebuffer

def capture():
    ctl=runpy.run_path(str(Path(__file__).with_name('runtime_control.py'))); m=ctl['m'];project=ctl['PROJECT']
    session=Path(json.loads((m.OUT/'session.json').read_text('utf8'))['session'])
    rec=json.loads((session/'session.local.json').read_text('utf8'))
    m.control.EMULATOR=m.EXE;m.control.checked_window(rec['pid'])
    game=m.CUE.with_suffix('.bin');assert digest(game)==rec['bin_sha256']==m.GAME_SHA
    assets=read_assets(game,['SLUS_005.61','LOAD_U.ARC']);exe=assets['SLUS_005.61'];font=entry(assets['LOAD_U.ARC'],0x10001)
    rn=exe[0x233c8-0x10000+2048:0x233c8-0x10000+2104];vn=font[384:512];va=259*2048+1920
    k=ctypes.WinDLL('kernel32',use_last_error=True)
    k.OpenProcess.argtypes=[wintypes.DWORD,wintypes.BOOL,wintypes.DWORD];k.OpenProcess.restype=wintypes.HANDLE
    k.ReadProcessMemory.argtypes=[wintypes.HANDLE,ctypes.c_void_p,ctypes.c_void_p,ctypes.c_size_t,ctypes.POINTER(ctypes.c_size_t)]
    k.VirtualQueryEx.argtypes=[wintypes.HANDLE,ctypes.c_void_p,ctypes.POINTER(Region),ctypes.c_size_t];k.CloseHandle.argtypes=[wintypes.HANDLE]
    handle=k.OpenProcess(0x410,False,rec['pid']);assert handle
    def read(addr,size):
        b=ctypes.create_string_buffer(size);got=ctypes.c_size_t()
        return b.raw if k.ReadProcessMemory(handle,addr,b,size,ctypes.byref(got)) and got.value==size else b''
    out=Path(__file__).parent/'after_runtime'/(project+'_dump_'+m.GAME_SHA[:8]);out.mkdir(parents=True,exist_ok=False)
    rams=set();videos=set()
    try:
        address=0
        while address<0x100000000:
            reg=Region()
            if not k.VirtualQueryEx(handle,address,ctypes.byref(reg),ctypes.sizeof(reg)):break
            lo=reg.base or 0;end=lo+reg.size
            if end<=address:break
            if reg.state==0x1000 and not reg.protect&0x100 and reg.protect&255 in (2,4,8,32,64,128):
                for start in range(lo,end,1048576):
                    blob=read(start,min(end-start,1048704))
                    for needle,adjust,found in ((rn,0x233c8,rams),(vn,va,videos)):
                        pos=blob.find(needle)
                        while pos>=0:
                            base=start+pos-adjust
                            if base>0:found.add(base)
                            pos=blob.find(needle,pos+1)
            address=end
        rams={b for b in rams if all(read(b+a,32)==exe[a-0x10000+2048:a-0x10000+2080]for a in (0x233c8,0x23400,0xea20c))}
        videos={b for b in videos if all(read(b+(256+y)*2048+1920,128)==font[y*128:(y+1)*128]for y in (2,3,4,5))}
        assert len(rams)==len(videos)==1
        ram=read(next(iter(rams)),2097152);vram=read(next(iter(videos)),1048576)
        (out/'ram.bin').write_bytes(ram);(out/'vram.bin').write_bytes(vram)
        buffers=native_draw_buffers(ram)
        for b in buffers:
            x,y,_,_=b['draw_clip'];framebuffer(vram,x*2,y).save(out/f'framebuffer_{y}.png')
        report={'project':project,'mounted_bin':game.relative_to(ROOT).as_posix(),'mounted_bin_sha256':m.GAME_SHA,'session':session.relative_to(ROOT).as_posix(),'pid':rec['pid'],'RAM_host':list(rams),'VRAM_host':list(videos),'draw_buffers':buffers,'process_memory_written':False,'keys_sent':False}
        (out/'capture.json').write_text(json.dumps(report,indent=2)+'\n','utf8');print(json.dumps(report))
    finally:k.CloseHandle(handle)
if __name__=='__main__':capture()
