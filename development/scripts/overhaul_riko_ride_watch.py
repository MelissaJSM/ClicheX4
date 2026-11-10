"""실제 RideArmor 머리 전환의 RAM/GPU 일치를 짧게 읽기 전용 관측한다."""
import argparse,ctypes,gzip,hashlib,json,struct,sys,time
from ctypes import wintypes
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from src.psx_player import graphics_bank,decode_stream
def sha(b):return hashlib.sha256(b).hexdigest()
def main(a):
    out=a.out.resolve();reference=a.reference_state.resolve()
    if not out.is_relative_to(ROOT/'work/overhaul_20261105/audio') or out.exists() or not reference.is_relative_to(ROOT/'work/overhaul_20261105/audio'):raise ValueError('Fresh isolated output and authenticated clone required')
    if not 0<a.seconds<=30:raise ValueError('Watch 1..30 seconds')
    packed=reference.read_bytes();manifest=json.loads((reference.parent/'manifest.json').read_text(encoding='utf8'))
    if sha(packed)!=manifest['output_sha256']:raise ValueError('Reference clone SHA differs')
    ref=gzip.decompress(packed)[442:442+0x200000];g=ref[0x1789a0:0x1789a0+205768];frames={};counts={}
    for n in range(66,86):
        f=graphics_bank(g,1)['frames'][n]
        if not 1<=f['tile_count']<=16:raise ValueError('Unsupported vehicle head upload')
        counts[n]=f['tile_count'];frames[n]=decode_stream(g,f['offset'],f['limit'],f['tile_count']*128).data
    k=ctypes.WinDLL('kernel32',use_last_error=True)
    k.OpenProcess.argtypes=[wintypes.DWORD,wintypes.BOOL,wintypes.DWORD];k.OpenProcess.restype=wintypes.HANDLE
    k.ReadProcessMemory.argtypes=[wintypes.HANDLE,ctypes.c_void_p,ctypes.c_void_p,ctypes.c_size_t,ctypes.POINTER(ctypes.c_size_t)];k.CloseHandle.argtypes=[wintypes.HANDLE]
    h=k.OpenProcess(0x410,False,a.pid)
    if not h:raise OSError('Read-only process open failed')
    def read(at,n):
        b=ctypes.create_string_buffer(n);got=ctypes.c_size_t()
        if not k.ReadProcessMemory(h,at,b,n,ctypes.byref(got)) or got.value!=n:raise OSError('Process region unreadable')
        return b.raw
    try:
        ram=read(a.ram_base,0x200000)
        for pos in (0x1540c,0x3dc1c,0x233c8):
            if ram[pos:pos+64]!=ref[pos:pos+64]:raise ValueError('Source native EXE anchor differs')
        assets={}
        for name,at,size in (('graphics',0x1789a0,205768),('parts',0x1ace9c,28616),('palettes',0x178000,2464)):
            if ram[at:at+size]!=ref[at:at+size]:raise ValueError('Resident asset differs: '+name)
            assets[name]=dict(ram_offset=at,size=size,sha256=sha(ram[at:at+size]))
        out.mkdir(parents=True);(out/'running.json').write_text(json.dumps({'pid':a.pid,'seconds':a.seconds}),encoding='utf8')
        print(json.dumps({'ready':True,'pid':a.pid,'seconds':a.seconds,'output':str(out)}),flush=True)
        start=time.monotonic();events=[];key=None;active=None;polls=0;skipped=0;matched=set()
        while time.monotonic()-start<a.seconds:
            now=time.monotonic()-start;p=read(a.ram_base+0x1418c8,228);frame=p[0x47]
            if p[2]!=1 or p[5]!=18 or p[0xc5]==0 or frame not in frames:
                skipped+=1;time.sleep(.004);continue
            sample_key=(frame,p[0x17],p[0xd4],p[0x16])
            if sample_key!=key:
                if active:active['last_seen_seconds']=now
                active=dict(first_seen_seconds=now,last_seen_seconds=now,frame=frame,animation=p[0x17],ride_animation=p[0xd4],facing_raw=p[0x16],world=[struct.unpack_from('<i',p,o)[0]/65536 for o in (8,12)],attempts=0,consistent_frame_samples=0,verified=False,ram_mismatch_samples=0,gpu_mismatch_samples=0)
                events.append(active);key=sample_key
            width=counts[frame]*8;decoded=read(a.ram_base+0x16dea8,counts[frame]*128)
            gpu=b''.join(read(a.vram_base+y*2048+640,width) for y in range(16))
            again=read(a.ram_base+0x1418c8,228);expected=frames[frame];active['attempts']+=1;polls+=1;active['last_seen_seconds']=time.monotonic()-start
            if (again[0x47],again[0x17],again[0xd4],again[0x16])==sample_key:
                active['consistent_frame_samples']+=1
                active['ram_mismatch_samples']+=decoded!=expected;active['gpu_mismatch_samples']+=gpu!=expected
                if decoded==gpu==expected and not active['verified']:
                    active.update(verified=True,verified_seconds=time.monotonic()-start,expected_sha256=sha(expected),ram_sha256=sha(decoded),gpu_sha256=sha(gpu));matched.add(frame)
                    file=out/f'head_{frame:02d}_{len(events):03d}.bin';file.write_bytes(gpu);active['gpu_capture']=file.name
            time.sleep(.004)
        final=read(a.ram_base,0x200000)
        after={name:final[q['ram_offset']:q['ram_offset']+q['size']]==ref[q['ram_offset']:q['ram_offset']+q['size']] for name,q in assets.items()}
        report=dict(pid=a.pid,ram_host_base=a.ram_base,vram_host_base=a.vram_base,reference_state=reference.relative_to(ROOT).as_posix(),reference_state_sha256=sha(packed),scope=manifest['scope'],seconds=time.monotonic()-start,polls=polls,nonride_or_nonhead_samples_skipped=skipped,assets=assets,assets_unchanged_at_end=after,head_upload_tile_counts=counts,verified_head_frames=sorted(matched),events=events,unverified_transitions=[n for n,e in enumerate(events) if not e['verified']],keys_sent=False,process_memory_written=False,active_state_file_modified=False,limitation='RAM decode and GPU upload are not atomic. Intermediate mismatches are recorded but are not automatically classified as game bugs. Only native observed poses are claimed; this does not verify unobserved Hawk/Chaser frames or fresh BIN loading.')
        (out/'evidence.json').write_text(json.dumps(report,indent=2),encoding='utf8');print(json.dumps({k:report[k] for k in ('seconds','polls','verified_head_frames','unverified_transitions','assets_unchanged_at_end')}),flush=True)
    finally:k.CloseHandle(h)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--pid',type=int,required=True);p.add_argument('--ram-base',type=lambda x:int(x,0),required=True);p.add_argument('--vram-base',type=lambda x:int(x,0),required=True);p.add_argument('--reference-state',type=Path,required=True);p.add_argument('--seconds',type=float,default=15);p.add_argument('--out',type=Path,required=True);main(p.parse_args())
