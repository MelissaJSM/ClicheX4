"""검증한 원래 체크포인트 EXE 앵커로 탑승 시험 RAM/VRAM을 읽기만 한다."""
import argparse,ctypes,gzip,hashlib,json,struct,sys
from ctypes import wintypes
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from src.psx_player import graphics_bank,decode_stream,composition_frame
from src.epsxe_state import framebuffer
from scripts.verify_korean_runtime_page import native_draw_buffers

def sha(b):return hashlib.sha256(b).hexdigest()
def main(a):
    reference=a.reference_state.resolve();out=a.out.resolve()
    if not reference.is_relative_to(ROOT/'work/overhaul_20261105/audio') or not out.is_relative_to(ROOT/'work/overhaul_20261105/audio') or out.exists():raise ValueError('Isolated authenticated clone and fresh output required')
    packed=reference.read_bytes();manifest=json.loads((reference.parent/'manifest.json').read_text(encoding='utf8'))
    if sha(packed)!=manifest['output_sha256']:raise ValueError('Reference clone SHA differs')
    s=gzip.decompress(packed);ref=s[442:442+0x200000]
    k=ctypes.WinDLL('kernel32',use_last_error=True)
    k.OpenProcess.argtypes=[wintypes.DWORD,wintypes.BOOL,wintypes.DWORD];k.OpenProcess.restype=wintypes.HANDLE
    k.ReadProcessMemory.argtypes=[wintypes.HANDLE,ctypes.c_void_p,ctypes.c_void_p,ctypes.c_size_t,ctypes.POINTER(ctypes.c_size_t)];k.CloseHandle.argtypes=[wintypes.HANDLE]
    h=k.OpenProcess(0x410,False,a.pid)
    if not h:raise OSError('Read-only process open failed')
    def read(at,n):
        b=ctypes.create_string_buffer(n);got=ctypes.c_size_t()
        if not k.ReadProcessMemory(h,at,b,n,ctypes.byref(got)) or got.value!=n:raise OSError('Capture region unreadable')
        return b.raw
    try:ram=read(a.ram_base,0x200000);vram=read(a.vram_base,0x100000)
    finally:k.CloseHandle(h)
    anchors={hex(off):ram[off:off+64]==ref[off:off+64] for off in (0x1540c,0x3dc1c,0x233c8)}
    if not all(anchors.values()):raise ValueError('Native code differs from authenticated source checkpoint')
    player=ram[0x1418c8:0x1418c8+228];frame=player[0x47]
    if player[2]!=1 or player[5]!=18 or not player[0xc5] or not 66<=frame<=85:raise ValueError('Expected genuine character1 RideArmor head pose')
    sizes={2:(0x1789a0,205768),3:(0x1ace9c,28616),9:(0x178000,2464)}
    assets={str(kind):{'ram_offset':at,'size':size,'sha256':sha(ram[at:at+size]),'equals_reference':ram[at:at+size]==ref[at:at+size]} for kind,(at,size) in sizes.items()}
    g=ram[0x1789a0:0x1789a0+205768];f=graphics_bank(g,1)['frames'][frame]
    if f['tile_count']!=1:raise ValueError('Unexpected vehicle head tile count')
    tile=decode_stream(g,f['offset'],f['limit'],128).data
    decoded_ok=ram[0x16dea8:0x16dea8+128]==tile
    gpu_ok=all(vram[y*2048+640:y*2048+648]==tile[y*8:y*8+8] for y in range(16))
    palette=ram[0x178000:0x178020];clut_ok=vram[480*2048:480*2048+32]==palette
    body_parts=ram[0x1ace9c:0x1ace9c+28616];head=composition_frame(body_parts,5,frame)
    out.mkdir(parents=True);(out/'ram.bin').write_bytes(ram);(out/'vram.bin').write_bytes(vram)
    clips=[]
    for draw in native_draw_buffers(ram):
        x,y,w,height=draw['draw_clip']
        if 0<=x and x+320<=1024 and 0<=y and y+240<=512 and (x,y) not in clips:
            framebuffer(vram,x*2,y).save(out/f'frame_{x}_{y}.png');clips.append((x,y))
    proof=dict(pid=a.pid,ram_host_base=a.ram_base,vram_host_base=a.vram_base,reference_state=reference.relative_to(ROOT).as_posix(),reference_state_sha256=sha(packed),scope=manifest['scope'],native_source_code_anchors=anchors,resident_graphic_assets=assets,character=player[2],player_state=list(player[4:8]),animation=player[0x17],frame=frame,ride_state=player[0xc5],ride_animation=player[0xd4],stage=ram[0x1721cc],area=ram[0x1721cd],hp=player[0x5c],world=[struct.unpack_from('<i',player,o)[0]/65536 for o in (8,12)],active_head_sha256=sha(tile),decoded_ram_head_exact=decoded_ok,gpu_head_texture_exact=gpu_ok,gpu_clut_equals_active_palette=clut_ok,head_composition=head,draw_clips=clips,ram_sha256=sha(ram),vram_sha256=sha(vram),keys_sent=False,process_memory_written=False,original_snapshot_modified=False,fresh_bin_loading_verified=False,ui_art_quality_verified=False)
    (out/'evidence.json').write_text(json.dumps(proof,indent=2),encoding='utf8');print(json.dumps(proof))
    if not all(q['equals_reference'] for q in assets.values()) or not(decoded_ok and gpu_ok and clut_ok):raise ValueError('Captured head/resource verification failed; raw evidence retained')
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--pid',type=int,required=True);p.add_argument('--ram-base',type=lambda x:int(x,0),required=True);p.add_argument('--vram-base',type=lambda x:int(x,0),required=True);p.add_argument('--reference-state',type=Path,required=True);p.add_argument('--out',type=Path,required=True);main(p.parse_args())
