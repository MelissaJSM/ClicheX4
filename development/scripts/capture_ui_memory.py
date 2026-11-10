"""Read-only framebuffer match for a native UI asset in the verified emulator."""
import argparse,ctypes,json,sys
from pathlib import Path
from ctypes import wintypes
from PIL import Image
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.emulator_session import checked_window
from scripts.project import digest,new_run,write_json
from src.epsxe_state import framebuffer,match_sprite

def main():
    p=argparse.ArgumentParser()
    for name in ('session','discovery','image'):p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--label',required=True);a=p.parse_args()
    session=json.loads((a.session/'session.local.json').read_text());discovery=json.loads(a.discovery.read_text())
    if session['pid']!=discovery['pid'] or session['bin_sha256']!=discovery['modified_bin_sha256']:raise ValueError('UI memory discovery/session mismatch')
    checked_window(session['pid'])
    kernel=ctypes.WinDLL('kernel32',use_last_error=True)
    kernel.OpenProcess.argtypes=[wintypes.DWORD,wintypes.BOOL,wintypes.DWORD];kernel.OpenProcess.restype=wintypes.HANDLE
    kernel.ReadProcessMemory.argtypes=[wintypes.HANDLE,ctypes.c_void_p,ctypes.c_void_p,ctypes.c_size_t,ctypes.POINTER(ctypes.c_size_t)]
    kernel.CloseHandle.argtypes=[wintypes.HANDLE]
    h=kernel.OpenProcess(0x410,False,session['pid'])
    if not h:raise OSError('Cannot open verified emulator read-only')
    def read(addr,size):
        buf=ctypes.create_string_buffer(size);got=ctypes.c_size_t()
        if not kernel.ReadProcessMemory(h,addr,buf,size,ctypes.byref(got)) or got.value!=size:return b''
        return buf.raw
    out=new_run(ROOT,'ver_buki_riko','ui_live');found=[]
    try:
        expected=Image.open(a.image).convert('RGBA')
        for addr in discovery['vram_candidates']:
            raw=read(addr,1048576)
            if len(raw)!=1048576:continue
            for page in (0,256):
                screen=framebuffer(raw,0,page);hits=match_sprite(screen,expected)
                if hits:
                    screen.save(out/f'framebuffer_{addr}_{page}.png');(out/f'vram_{addr}.bin').write_bytes(raw)
                    found.extend({'vram_host_address':addr,'page_y':page,**x} for x in hits)
        for addr in discovery['ram_candidates']:
            raw=read(addr,2097152)
            if len(raw)==2097152:(out/f'ram_{addr}.bin').write_bytes(raw)
    finally:kernel.CloseHandle(h)
    report={'label':a.label,'session':str(a.session),'pid':session['pid'],'bin_sha256':session['bin_sha256'],
            'expected_image':str(a.image),'expected_sha256':digest(a.image),'matches':found,
            'verified':bool(found),'process_memory_written':False,'keys_sent':False}
    write_json(out/'verification.local.json',report)
    print(json.dumps({'output':str(out),'verified':bool(found),'matches':found}))
    if not found:raise RuntimeError('Native UI pixels not found in framebuffer')
if __name__=='__main__':main()
