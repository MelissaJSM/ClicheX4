"""지정한 로컬 ePSXe의 RAM/VRAM만 읽어 PoC 표시를 검사. 입력·포커스·메모리 쓰기 없음."""
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
from scripts.project import new_run,write_json,digest
from scripts.discover_inputs import psx_arc
from src.psx_player import graphics_bank,decode_stream,composition_frame,compose_indices
from src.epsxe_state import framebuffer,match_sprite
from scripts.extract_zero import save_image


class Region(ctypes.Structure):
    _fields_=[('base',ctypes.c_void_p),('allocation',ctypes.c_void_p),
              ('allocation_protect',wintypes.DWORD),('size',ctypes.c_size_t),
              ('state',wintypes.DWORD),('protect',wintypes.DWORD),('type',wintypes.DWORD)]


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project',choices=['ver_buki_riko','ver_rin_nana'],default='ver_buki_riko')
    parser.add_argument('--pid',type=int,required=True)
    parser.add_argument('--build',type=Path,required=True)
    parser.add_argument('--frame',type=int,choices=range(254),default=147)
    parser.add_argument('--animation',type=int,choices=range(144),default=5)
    parser.add_argument('--timeout',type=float,default=10)
    parser.add_argument('--discover-only',action='store_true',help='검증된 RAM/VRAM 후보만 기록; UI 대조용')
    parser.add_argument('--character',choices=['zero','x'],default='zero')
    args=parser.parse_args()
    character_id=0 if args.character=='x' else 1
    if not 1 <= args.timeout <= 60: raise ValueError('Capture timeout must be 1..60 seconds')
    frame_number=args.frame
    build=args.build.resolve()
    if not build.is_relative_to((ROOT/'out'/args.project).resolve()):raise ValueError('Unexpected build directory')
    manifest=json.loads((build/'manifest.json').read_text(encoding='utf-8'))
    if args.character=='x' and manifest.get('task') not in ('x_shibuki','fourth_armor_shibuki','ultimate_armor_shibuki','x_nana','fourth_armor_nana','ultimate_armor_nana'):raise ValueError('X capture requires an X build')
    if args.character=='zero' and manifest.get('task') in ('x_shibuki','fourth_armor_shibuki','ultimate_armor_shibuki','x_nana','fourth_armor_nana','ultimate_armor_nana'):raise ValueError('X build cannot be inspected as Zero')
    if manifest.get('task') in ('fourth_armor_shibuki','fourth_armor_nana') and not args.discover_only:raise ValueError('Armor overlays require the dedicated armor display verifier')
    ultimate=manifest.get('task') in ('ultimate_armor_shibuki','ultimate_armor_nana')
    arc=(build/('PL02_U.ARC' if ultimate else 'modified.arc')).read_bytes()
    import hashlib
    if hashlib.sha256(arc).hexdigest()!=manifest['modified_archive_sha256']:raise ValueError('Changed build archive')
    entries=psx_arc(arc)
    def entry(kind):
        e=next(x for x in entries if x['type']==hex(kind));return arc[e['offset']:e['offset']+e['size']]
    gfx=entry(2);parts=entry(3);palette_bytes=entry(9)[:32];palette=struct.unpack('<16H',palette_bytes)
    bank=graphics_bank(gfx,0,allow_bank_aliases=args.character=='x')
    target=bank['frames'][frame_number];expected=decode_stream(gfx,target['offset'],target['limit'],target['tile_count']*128).data
    composition=composition_frame(parts,0,frame_number)
    indices,size,_,_=compose_indices(expected,target['tile_count'],composition)
    anchor=bytes.fromhex('150001000c0001922a0001930c00019436000100')
    kernel=ctypes.WinDLL('kernel32',use_last_error=True)
    kernel.OpenProcess.argtypes=[wintypes.DWORD,wintypes.BOOL,wintypes.DWORD];kernel.OpenProcess.restype=wintypes.HANDLE
    kernel.ReadProcessMemory.argtypes=[wintypes.HANDLE,ctypes.c_void_p,ctypes.c_void_p,ctypes.c_size_t,ctypes.POINTER(ctypes.c_size_t)]
    kernel.VirtualQueryEx.argtypes=[wintypes.HANDLE,ctypes.c_void_p,ctypes.POINTER(Region),ctypes.c_size_t]
    kernel.QueryFullProcessImageNameW.argtypes=[wintypes.HANDLE,wintypes.DWORD,wintypes.LPWSTR,ctypes.POINTER(wintypes.DWORD)]
    kernel.CloseHandle.argtypes=[wintypes.HANDLE]
    handle=kernel.OpenProcess(0x410,False,args.pid) # QUERY_INFORMATION | VM_READ only
    if not handle:raise OSError(ctypes.get_last_error(),'Cannot read emulator process')
    def read(address,length):
        buf=ctypes.create_string_buffer(length);received=ctypes.c_size_t()
        ok=kernel.ReadProcessMemory(handle,address,buf,length,ctypes.byref(received))
        return buf.raw[:received.value] if ok else b''
    try:
        path=ctypes.create_unicode_buffer(32768);length=wintypes.DWORD(len(path))
        if not kernel.QueryFullProcessImageNameW(handle,0,path,ctypes.byref(length)):raise OSError('Cannot verify executable')
        executable=Path(path.value).resolve()
        allowed=[(ROOT/'ePSXe2018/ePSXe.exe').resolve(),(ROOT/'work/ver_buki_riko/baseline/20261023T054951214649Z/emulator/ePSXe.exe').resolve()]
        if args.project=='ver_rin_nana':allowed=[(ROOT/'work/ver_rin_nana/emulator/ePSXe.exe').resolve()]
        if executable not in allowed or digest(executable)!='a266ee19bbeba0da38ffbaa8b02b89fe2524af7a45a13ea9ff37feab7423986d':
            raise ValueError('Process is not the provided ePSXe binary')
        ram_candidates=set();vram_candidates=set();address=0;scanned=0
        while address<0x100000000:
            region=Region()
            if not kernel.VirtualQueryEx(handle,address,ctypes.byref(region),ctypes.sizeof(region)):break
            start=region.base or 0;end=start+region.size
            if end<=address:break
            if region.state==0x1000 and not region.protect&0x100 and region.protect&0xff in (2,4,8,0x20,0x40,0x80):
                for offset in range(start,end,1024*1024):
                    blob=read(offset,min(1024*1024+64,end-offset));scanned+=len(blob)
                    for needle,collection,relative in [(anchor,ram_candidates,0x11a2f8),(palette_bytes,vram_candidates,480*2048)]:
                        pos=blob.find(needle)
                        while pos>=0:
                            if offset+pos>=relative:collection.add(offset+pos-relative)
                            pos=blob.find(needle,pos+1)
            address=end
        ram_bases=[]
        for base in ram_candidates:
            ram=read(base,2097152)
            if len(ram)!=2097152:continue
            player=ram[0x1418c8:0x1418c8+0xe4]
            ptr=struct.unpack_from('<I',player,0x38)[0]&0x1fffff
            if player[2]==character_id and (not ultimate or (ram[0x1721f7]==1 and (args.discover_only or player[0xa7]==0))) and ram[ptr:ptr+bank['end']-bank['base']]==gfx[bank['base']:bank['end']]:ram_bases.append(base)
        if not ram_bases:raise ValueError('No matching patched player RAM found')
        out=new_run(ROOT,args.project,'live_poc')
        sprite=save_image(indices,size,palette,out/f'expected_frame{frame_number}.png')
        deadline=time.monotonic()+args.timeout
        write_json(out/'discovery.local.json',{'pid':args.pid,'ram_candidates':ram_bases,
            'vram_candidates':sorted(vram_candidates),'source_build':str(build),
            'modified_bin_sha256':manifest['modified_bin']['sha256'],'process_memory_written':False})
        if args.discover_only:
            print(json.dumps({'output':str(out),'discovery_only':True,'frame_verified':False}))
            return
        while time.monotonic()<deadline:
            for base in ram_bases:
                player=read(base+0x1418c8,0xe4)
                if len(player)!=0xe4 or player[2]!=character_id or player[0x17]!=args.animation or player[0x47]!=frame_number:continue
                if read(base+0x16dea8,len(expected))!=expected:continue
                for video in vram_candidates:
                    raw=read(video,1048576)
                    if len(raw)!=1048576:continue
                    if raw[480*2048:480*2048+32]!=palette_bytes:continue
                    cursor=0;valid=True
                    for first in range(0,target['tile_count'],16):
                        row_bytes=min(16,target['tile_count']-first)*8
                        for row in range(16):
                            pos=(first//16*16+row)*2048+640
                            if raw[pos:pos+row_bytes]!=expected[cursor:cursor+row_bytes]:valid=False
                            cursor+=row_bytes
                    if not valid:continue
                    after=read(base+0x1418c8,0xe4)
                    if len(after)!=0xe4 or (after[2],after[0x17],after[0x47])!=(character_id,player[0x17],frame_number):continue
                    matches=[]
                    for page in (0,240,256):
                        picture=framebuffer(raw,0,page)
                        found=match_sprite(picture,sprite)
                        if found:
                            picture.save(out/f'actual_framebuffer_{page}.png')
                            matches.extend({'page_y':page,**m} for m in found)
                    if matches:
                        (out/'vram.bin').write_bytes(raw)
                        (out/'player.bin').write_bytes(player)
                        write_json(out/'verification.local.json',{'pid':args.pid,'executable':str(executable),
                            'ram_host_address':base,'vram_host_address':video,'scanned_bytes':scanned,
                            'source_build':str(build),'modified_bin_sha256':manifest['modified_bin']['sha256'],
                            'character':character_id,'animation':player[0x17],'frame':frame_number,'modified_ram_buffer_matches':True,
                            'modified_vram_upload_matches':True,'framebuffer_matches':matches,
                            'input_sent':False,'focus_changed':False,'process_memory_written':False})
                        print(json.dumps({'output':str(out),'verified':True,'matches':matches}));return
            time.sleep(0.03)
        write_json(out/'timeout.local.json',{'pid':args.pid,'verified':False,
            'players':{str(base):read(base+0x1418c8,0xe4).hex() for base in ram_bases},
            'requested_animation':args.animation,'requested_frame':args.frame})
        raise RuntimeError(f'No matching display captured within {args.timeout} seconds; diagnostics: {out}')
    finally:
        kernel.CloseHandle(handle)


if __name__=='__main__':main()
