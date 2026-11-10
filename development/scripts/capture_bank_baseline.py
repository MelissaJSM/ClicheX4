"""기존 읽기 전용 검색 후보에서 현재 그래픽 은행·RAM·VRAM 일치 기준점을 만든다."""
import argparse,ctypes,json,struct,sys
from ctypes import wintypes
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.emulator_session import checked_window
from scripts.discover_inputs import psx_arc,sha256
from scripts.project import write_json
from src.psx_player import graphics_bank,decode_stream,composition_frame,compose_indices
from src.epsxe_state import framebuffer,match_sprite
from scripts.extract_zero import save_image

def capture(discovery):
    discovery=discovery.resolve()
    if not discovery.is_relative_to(ROOT/'work/ver_buki_riko/live_poc'):raise ValueError('Unexpected discovery path')
    prior=json.loads(discovery.read_text('utf8'));checked_window(prior['pid'])
    build=Path(prior['source_build']).resolve()
    if not build.is_relative_to(ROOT/'out/ver_buki_riko'):raise ValueError('Unexpected build')
    manifest=json.loads((build/'manifest.json').read_text('utf8'));arc=(build/'modified.arc').read_bytes()
    if sha256(arc)!=manifest['modified_archive_sha256'] or prior['modified_bin_sha256']!=manifest['modified_bin']['sha256']:
        raise ValueError('Discovery/build hash mismatch')
    entries=psx_arc(arc)
    def entry(kind):
        r=next(e for e in entries if e['type']==hex(kind));return arc[r['offset']:r['offset']+r['size']]
    gfx,parts,pal=entry(2),entry(3),entry(9)[:32]
    kernel=ctypes.WinDLL('kernel32',use_last_error=True)
    kernel.OpenProcess.argtypes=[wintypes.DWORD,wintypes.BOOL,wintypes.DWORD];kernel.OpenProcess.restype=wintypes.HANDLE
    kernel.ReadProcessMemory.argtypes=[wintypes.HANDLE,ctypes.c_void_p,ctypes.c_void_p,ctypes.c_size_t,ctypes.POINTER(ctypes.c_size_t)]
    kernel.CloseHandle.argtypes=[wintypes.HANDLE];handle=kernel.OpenProcess(0x410,False,prior['pid'])
    if not handle:raise OSError('Cannot open process read-only')
    def read(address,length):
        buf=ctypes.create_string_buffer(length);got=ctypes.c_size_t()
        if not kernel.ReadProcessMemory(handle,address,buf,length,ctypes.byref(got)) or got.value!=length:raise OSError('Short read')
        return buf.raw
    candidates=[]
    try:
        for base in prior['ram_candidates']:
            player=read(base+0x1418c8,0xe4)
            if player[2]!=1:continue
            ptr=struct.unpack_from('<I',player,0x38)[0]&0x1fffff
            for bi in (0,1) if manifest.get('bank1_frame_inputs') else (0,):
                bank=graphics_bank(gfx,bi)
                if read(base+ptr,bank['end']-bank['base'])!=gfx[bank['base']:bank['end']]:continue
                n=player[0x47];f=bank['frames'][n];expected=decode_stream(gfx,f['offset'],f['limit'],f['tile_count']*128).data
                if read(base+0x16dea8,len(expected))!=expected:continue
                for video in prior['vram_candidates']:
                    vram=read(video,1048576);cursor=0;valid=vram[480*2048:480*2048+32]==pal
                    for first in range(0,f['tile_count'],16):
                        width=min(16,f['tile_count']-first)*8
                        for y in range(16):
                            pos=(first//16*16+y)*2048+640
                            valid=valid and vram[pos:pos+width]==expected[cursor:cursor+width];cursor+=width
                    if valid:candidates.append((base,video,bi,n,player,vram))
        if len(candidates)!=1:raise ValueError(f'Expected unique RAM/VRAM pair; found {len(candidates)}')
        base,video,bi,n,player,vram=candidates[0]
        after=read(base+0x1418c8,0xe4)
        if (after[0x17],after[0x47])!=(player[0x17],n):raise ValueError('Pose changed while probing; retry')
        target=discovery.parent/'bank_baseline.local.json'
        write_json(target,{**prior,'ram_host_address':base,'vram_host_address':video,'observed_bank':bi,
            'observed_animation':player[0x17],'observed_frame':n,'full_bank_equal':True,
            'decoded_ram_equal':True,'vram_upload_equal':True,'palette_equal':True,'frame_render_verified':False})
        for page in (0,256):framebuffer(vram,0,page).save(discovery.parent/f'baseline_page{page}.png')
        print(json.dumps({'baseline':str(target),'bank':bi,'animation':player[0x17],'frame':n}))
    finally:kernel.CloseHandle(handle)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--discovery',type=Path,required=True)
    capture(p.parse_args().discovery)
