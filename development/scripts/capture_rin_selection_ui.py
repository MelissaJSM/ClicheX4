"""검증된 두 번째 모드 세션에서 선택 그림 팔레트/화면을 읽기 전용 대조한다."""
import argparse,ctypes,json,sys,time
from ctypes import wintypes
from pathlib import Path
from PIL import Image
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import scripts.emulator_session as session_control
from scripts.capture_poc_memory import Region
from scripts.project import digest,new_run
from src.epsxe_state import framebuffer,match_sprite

def main(session,build,region=None):
    session=session.resolve();build=build.resolve()
    if not session.is_relative_to(ROOT/'work/ver_rin_nana/emulator_sessions') or not build.is_relative_to(ROOT/'out/ver_rin_nana'):raise ValueError('Unexpected UI verification path')
    s=json.loads((session/'session.local.json').read_text('utf8'));m=json.loads((build/'manifest.json').read_text('utf8'))
    if s['bin_sha256']!=m['modified_bin']['sha256'] or digest(build/'rin_nana.bin')!=s['bin_sha256']:raise ValueError('Session BIN differs')
    session_control.EMULATOR=ROOT/'work/ver_rin_nana/emulator/ePSXe.exe';session_control.checked_window(s['pid'])
    pal=(build/'portrait/palette.bin').read_bytes();expected=Image.open(build/'portrait/portrait.png').convert('RGBA')
    palette_row=4 if m['kind']=='nana_selection_portrait' else 5
    palette_offset=480*2048+palette_row*32
    if region:
        x,y,w,h=region
        if min(x,y)<0 or min(w,h)<=0 or x+w>expected.width or y+h>expected.height:raise ValueError('Invalid UI verification region')
        expected=expected.crop((x,y,x+w,y+h))
    if len(pal)!=32:raise ValueError('Unexpected portrait palette')
    k=ctypes.WinDLL('kernel32',use_last_error=True)
    k.OpenProcess.argtypes=[wintypes.DWORD,wintypes.BOOL,wintypes.DWORD];k.OpenProcess.restype=wintypes.HANDLE
    k.ReadProcessMemory.argtypes=[wintypes.HANDLE,ctypes.c_void_p,ctypes.c_void_p,ctypes.c_size_t,ctypes.POINTER(ctypes.c_size_t)]
    k.VirtualQueryEx.argtypes=[wintypes.HANDLE,ctypes.c_void_p,ctypes.POINTER(Region),ctypes.c_size_t]
    k.CloseHandle.argtypes=[wintypes.HANDLE];h=k.OpenProcess(0x410,False,s['pid'])
    if not h:raise ctypes.WinError(ctypes.get_last_error())
    def read(addr,size):
        buf=ctypes.create_string_buffer(size);got=ctypes.c_size_t()
        return buf.raw if k.ReadProcessMemory(h,addr,buf,size,ctypes.byref(got)) and got.value==size else b''
    candidates=set();out=new_run(ROOT,'ver_rin_nana','selection_live');found=[];expected.save(out/'expected.png')
    try:
        address=0
        while address<0x100000000:
            reg=Region()
            if not k.VirtualQueryEx(h,address,ctypes.byref(reg),ctypes.sizeof(reg)):break
            start=reg.base or 0;end=start+reg.size
            if end<=address:break
            if reg.state==0x1000 and not reg.protect&0x100 and reg.protect&0xff in (2,4,8,0x20,0x40,0x80):
                for off in range(start,end,1048576):
                    blob=read(off,min(1048576+32,end-off));pos=blob.find(pal)
                    while pos>=0:
                        base=off+pos-palette_offset
                        if base>0:candidates.add(base)
                        pos=blob.find(pal,pos+1)
            address=end
        for addr in candidates:
            raw=read(addr,1048576)
            if len(raw)!=1048576 or raw[palette_offset:palette_offset+32]!=pal:continue
            for page in (0,256):
                screen=framebuffer(raw,0,page);matches=match_sprite(screen,expected)
                if matches:
                    screen.save(out/f'framebuffer_{page}.png');(out/'vram.bin').write_bytes(raw)
                    found.extend({'vram_host_address':addr,'page_y':page,**q} for q in matches)
    finally:k.CloseHandle(h)
    report={'pid':s['pid'],'session':str(session),'bin_sha256':s['bin_sha256'],
            'expected_sha256':digest(out/'expected.png'),'region':region,'palette_row':palette_row,'candidate_count':len(candidates),
            'matches':found,'verified':bool(found),'process_memory_written':False,'keys_sent':False,
            'scope':'specified visible portrait region and palette' if region else 'selection portrait opaque pixels and palette, not all UI animations'}
    (out/'verification.json').write_text(json.dumps(report,indent=2)+'\n','utf8')
    print(json.dumps({'output':str(out),'verified':bool(found),'matches':found}))
    if not found:raise RuntimeError('Selection portrait not found in current framebuffer')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--session',type=Path,required=True);p.add_argument('--build',type=Path,required=True);p.add_argument('--region',type=int,nargs=4);a=p.parse_args();main(a.session,a.build,a.region)
