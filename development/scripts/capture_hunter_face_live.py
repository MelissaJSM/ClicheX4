"""Read-only Hunter HQ expression capture; never sends keys or changes focus."""
import argparse,ctypes,json,time
from ctypes import wintypes
from pathlib import Path
from PIL import Image
from scripts.capture_poc_memory import Region
from scripts.emulator_session import checked_window
from scripts.prepare_riko_ui import entry
from scripts.project import digest
from src.epsxe_state import framebuffer,match_sprite


def capture(session,recipe,output,seconds):
    rec=json.loads((session/'session.local.json').read_text('utf8'));checked_window(rec['pid'])
    if not 1<=seconds<=30:raise ValueError('Capture must last 1..30 seconds')
    config=json.loads((recipe/'recipe.json').read_text('utf8'))
    for item in config['files']:
        if digest(recipe/item['file'])!=item['sha256']:raise ValueError('Candidate hash mismatch')
    palette=entry((recipe/'COL0D_0Z.ARC').read_bytes(),5)[35*32:36*32]
    texture=entry((recipe/'ST0D_0Z.ARC').read_bytes(),0x10102)[63488:81920]
    parts=entry((recipe/'ST0D_0Z.ARC').read_bytes(),10)
    k=ctypes.WinDLL('kernel32',use_last_error=True)
    k.OpenProcess.argtypes=[wintypes.DWORD,wintypes.BOOL,wintypes.DWORD];k.OpenProcess.restype=wintypes.HANDLE
    k.ReadProcessMemory.argtypes=[wintypes.HANDLE,ctypes.c_void_p,ctypes.c_void_p,ctypes.c_size_t,ctypes.POINTER(ctypes.c_size_t)]
    k.VirtualQueryEx.argtypes=[wintypes.HANDLE,ctypes.c_void_p,ctypes.POINTER(Region),ctypes.c_size_t]
    k.QueryFullProcessImageNameW.argtypes=[wintypes.HANDLE,wintypes.DWORD,wintypes.LPWSTR,ctypes.POINTER(wintypes.DWORD)]
    k.CloseHandle.argtypes=[wintypes.HANDLE]
    handle=k.OpenProcess(0x410,False,rec['pid'])
    if not handle:raise OSError('Cannot read verified emulator')
    def read(addr,size):
        buf=ctypes.create_string_buffer(size);got=ctypes.c_size_t()
        return buf.raw if k.ReadProcessMemory(handle,addr,buf,size,ctypes.byref(got)) and got.value==size else b''
    try:
        path=ctypes.create_unicode_buffer(32768);length=wintypes.DWORD(len(path))
        if not k.QueryFullProcessImageNameW(handle,0,path,ctypes.byref(length)):raise OSError('Process identity unavailable')
        if Path(path.value).resolve()!=Path(rec['executable']).resolve() or digest(Path(path.value))!=rec['exe_sha256']:
            raise ValueError('Emulator identity differs')
        address=0;candidates=set();parts_hits=set();relative=482*2048+3*32
        while address<0x100000000:
            region=Region()
            if not k.VirtualQueryEx(handle,address,ctypes.byref(region),ctypes.sizeof(region)):break
            start=region.base or 0;end=start+region.size
            if end<=address:break
            if region.state==0x1000 and not region.protect&0x100 and region.protect&0xff in (2,4,8,0x20,0x40,0x80):
                for offset in range(start,end,1048576):
                    blob=read(offset,min(1048576+len(parts),end-offset))
                    for pattern,collection,adjust in [(palette,candidates,relative),(parts,parts_hits,0)]:
                        pos=0
                        while (pos:=blob.find(pattern,pos))>=0:
                            if offset+pos>=adjust:collection.add(offset+pos-adjust)
                            pos+=1
            address=end
        videos=[]
        for base in candidates:
            data=read(base,1048576)
            if len(data)!=1048576:continue
            if all(data[(144+r)*2048+1024:(144+r)*2048+1152]==texture[r*128:(r+1)*128] if r<32 else
                   data[(r-32)*2048+1152:(r-32)*2048+1280]==texture[r*128:(r+1)*128] for r in range(144)):
                videos.append(base)
        if not videos or not parts_hits:raise ValueError('Corrected HQ texture/parts not found')
        output.mkdir(exist_ok=False);groups={}
        for n in range(14):
            im=Image.open(recipe/f'base_{n:02d}.png').convert('RGBA');cx=48 if 10<=n<=12 else 40
            head=im.crop((cx-14,4,cx+18,32));key=head.tobytes()
            if key not in groups:groups[key]={'frames':[],'image':head}
            groups[key]['frames'].append(n)
        seen={};samples=0;start=time.monotonic()
        while time.monotonic()-start<seconds:
            for video in videos:
                raw=read(video,1048576)
                if len(raw)!=1048576:continue
                for page in (0,256):
                    screen=framebuffer(raw,0,page)
                    for group in groups.values():
                        key=','.join(map(str,group['frames']))
                        if key in seen:continue
                        hits=match_sprite(screen,group['image'])
                        if hits:
                            label='_'.join(map(str,group['frames']))
                            screen.save(output/f'frames_{label}.png');(output/f'frames_{label}_vram.bin').write_bytes(raw)
                            seen[key]={'appearance_matches_frames':group['frames'],'seconds':time.monotonic()-start,'matches':hits,'page':page}
            samples+=1;time.sleep(.05)
        report={'session':str(session),'bin_sha256':rec['bin_sha256'],'vram_addresses':videos,
            'parts_host_addresses':sorted(parts_hits),'texture_rows_verified':144,
            'observed_appearances':list(seen.values()),'samples':samples,
            'keys_sent':False,'focus_changed':False,'process_memory_written':False,
            'checkpoint_preview_not_fresh_disk_load':True}
        (output/'verification.local.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
        print(json.dumps(report))
    finally:k.CloseHandle(handle)


if __name__=='__main__':
    p=argparse.ArgumentParser()
    for n in ('session','recipe','output'):p.add_argument('--'+n,type=Path,required=True)
    p.add_argument('--seconds',type=float,default=20);a=p.parse_args()
    capture(a.session,a.recipe,a.output,a.seconds)
