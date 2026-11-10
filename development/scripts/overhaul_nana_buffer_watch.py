"""검증 BIN의 Nana 29..32타일 디코딩 경계와 실제 RAM/GPU를 읽기 전용 검사한다."""
import argparse,ctypes,hashlib,json,struct,sys,time
from ctypes import wintypes
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.discover_inputs import DiscReader,psx_arc
from src.psx_player import graphics_bank,bank_offsets,decode_stream
BUILD=ROOT/'out/ver_rin_nana/overhaul_20261105_review03/rin_nana.bin'
BIN_SHA='1e2089b31543244befe6c4ffc8aae9ac6a532c7e9a82ea20b8781a2fd63eece2'
BUF=0x16dea8;CAPACITY=4096;PLAYER=0x1418c8

def sha(b):return hashlib.sha256(b).hexdigest()
def require(ok,msg):
    if not ok:raise ValueError(msg)
def digest(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(8388608),b''):h.update(b)
    return h.hexdigest()
def load():
    require(digest(BUILD)==BIN_SHA,'Unexpected review BIN')
    with BUILD.open('rb') as f:
        d=DiscReader(f,BUILD.stat().st_size);rs={r['name'].split(';')[0]:r for r in d.inspect()['files'] if r['name'].split(';')[0] in ('PL02_U.ARC','SLUS_005.61')}
        arc=d.read(rs['PL02_U.ARC']['lba'],rs['PL02_U.ARC']['size']);exe=d.read(rs['SLUS_005.61']['lba'],rs['SLUS_005.61']['size'])
    es={int(e['type'],16):arc[e['offset']:e['offset']+e['size']] for e in psx_arc(arc)}
    bank=graphics_bank(es[2],0,allow_bank_aliases=True);frames={}
    for f in bank['frames']:
        if f['tile_count']<=32:frames[f['index']]=(f,decode_stream(es[2],f['offset'],f['limit'],f['tile_count']*128).data)
    require(len(frames)==len(bank['frames']),'Frame exceeds 32-tile native buffer')
    return arc,exe,es,bank,frames

def cpu_checks(exe,es,bank,frames,observe_writes=True,targets=None):
    from unicorn import Uc,UC_ARCH_MIPS,UC_MODE_MIPS32,UC_MODE_LITTLE_ENDIAN,UC_HOOK_CODE,UC_HOOK_MEM_WRITE
    from unicorn import mips_const as m
    checks=[];targets=targets if targets is not None else [n for n,(f,b) in frames.items() if f['tile_count']>=29 or n==0]
    for n in targets:
        f,expected=frames[n];u=Uc(UC_ARCH_MIPS,UC_MODE_MIPS32|UC_MODE_LITTLE_ENDIAN);u.mem_map(0,0x200000)
        load_addr=struct.unpack_from('<I',exe,0x18)[0]&0x1fffffff;load_size=struct.unpack_from('<I',exe,0x1c)[0]
        u.mem_write(load_addr,exe[2048:2048+load_size]);gaddr=0x1789a0;u.mem_write(gaddr,es[2])
        obj=bytearray(228);struct.pack_into('<I',obj,0x38,0x80000000+gaddr+bank['base']);obj[0x47]=n;obj[0x48]=255 if n!=255 else 254;obj[0x49]=3
        u.mem_write(PLAYER,bytes(obj));u.mem_write(0x141f68,struct.pack('<I',0x801659d0));u.mem_write(0x1659d0,b'\0'*108)
        sentinel=bytes((i*73+11)&255 for i in range(CAPACITY+128));u.mem_write(BUF-64,sentinel)
        u.reg_write(m.UC_MIPS_REG_SP,0x801ff000);u.reg_write(m.UC_MIPS_REG_RA,0x80008000)
        for reg,value in ((m.UC_MIPS_REG_A0,0x80000000+PLAYER),(m.UC_MIPS_REG_A1,320),(m.UC_MIPS_REG_A2,0)):u.reg_write(reg,value)
        writes=[]
        def on_write(cpu,access,address,size,value,user):
            at=address&0x1fffffff
            if BUF-64<=at<BUF+CAPACITY+64:writes.append((at,size))
        def on_code(cpu,address,size,user):
            if address==0x80008000:cpu.emu_stop()
        # Scope the write observer to the decompression buffer. A global Unicorn
        # MIPS write hook changes the queue loop's branch-delay-slot behaviour.
        if observe_writes:u.hook_add(UC_HOOK_MEM_WRITE,on_write,begin=BUF-64,end=BUF+CAPACITY+63)
        u.hook_add(UC_HOOK_CODE,on_code);u.emu_start(0x80015ecc,0,count=1000000)
        require(u.reg_read(m.UC_MIPS_REG_PC)==0x80008000,f'Native decompressor did not return: frame {n}, PC {u.reg_read(m.UC_MIPS_REG_PC):08X}, RA {u.reg_read(m.UC_MIPS_REG_RA):08X}')
        after=bytes(u.mem_read(BUF-64,CAPACITY+128));require(after[64:64+len(expected)]==expected,'Native and Python decoder differ')
        require(after[:64]==sentinel[:64] and after[64+len(expected):]==sentinel[64+len(expected):],'Native decoder touched out-of-frame/buffer bytes')
        if observe_writes:require(writes and min(a for a,s in writes)==BUF and max(a+s for a,s in writes)==BUF+len(expected),'Unexpected native write bounds')
        q=bytes(u.mem_read(0x1659d0,108));rects=[];collected=bytearray();pixels=0
        for i in range(9):
            x,y,w,h,p=struct.unpack_from('<hhhhI',q,i*12)
            if p==0:break
            address=p&0x1fffffff;require(BUF<=address and address+w*h*2<=BUF+CAPACITY,'GPU DMA region outside player buffer')
            rects.append(dict(x=x,y=y,width_words=w,height=h,ram_address=hex(p),bytes=w*h*2));collected+=u.mem_read(address,w*h*2);pixels+=w*h*2
        require(bytes(collected)==expected and pixels==len(expected),'Native queued GPU transfers differ from decoded image')
        require(struct.unpack('<I',u.mem_read(0x141f68,4))[0]==0x801659d0+len(rects)*12,'Native queue pointer wrong')
        require(u.mem_read(PLAYER+0x48,1)==bytes([n]),'Native frame update missing')
        checks.append(dict(frame=n,tiles=f['tile_count'],bytes=len(expected),remaining_buffer_bytes=CAPACITY-len(expected),native_write_start=hex(BUF),native_write_end_exclusive=hex(BUF+len(expected)),buffer_outside_and_unused_tail_preserved=True,decoded_sha256=sha(expected),gpu_rectangles=rects))
    return checks

def watch(a,arc,exe,es,bank,frames,out):
    require(a.pid is not None and a.ram_base is not None and a.vram_base is not None,'Live process addresses required')
    require(0<a.seconds<=30,'Watch duration must be 1..30 seconds')
    k=ctypes.WinDLL('kernel32',use_last_error=True)
    k.OpenProcess.argtypes=[wintypes.DWORD,wintypes.BOOL,wintypes.DWORD];k.OpenProcess.restype=wintypes.HANDLE
    k.ReadProcessMemory.argtypes=[wintypes.HANDLE,ctypes.c_void_p,ctypes.c_void_p,ctypes.c_size_t,ctypes.POINTER(ctypes.c_size_t)];k.CloseHandle.argtypes=[wintypes.HANDLE]
    h=k.OpenProcess(0x410,False,a.pid)
    if not h:raise OSError('Read-only process open failed')
    def read(at,n):
        b=ctypes.create_string_buffer(n);got=ctypes.c_size_t()
        if not k.ReadProcessMemory(h,at,b,n,ctypes.byref(got)) or got.value!=n:raise OSError('Read failed')
        return b.raw
    try:
        ram=read(a.ram_base,0x200000);assets={}
        for addr in (0x1540c,0x15ecc,0x16ff4,0x233c8):require(ram[addr:addr+64]==exe[addr-0x10000+2048:addr-0x10000+2112],'Native EXE anchor mismatch')
        for kind in (2,3,9):
            at=ram.find(es[kind]);require(at>=0 and ram.find(es[kind],at+1)<0,'Exact resident asset missing/ambiguous '+str(kind));assets[str(kind)]=dict(ram_offset=at,size=len(es[kind]),sha256=sha(es[kind]))
        gptr=0x80000000+assets['2']['ram_offset']+bank['base'];cptr=0x80000000+assets['3']['ram_offset']+bank_offsets(es[3])[0]
        p=ram[PLAYER:PLAYER+228];require(p[2]==0 and p[0xa7]==0 and ram[0x1721f7]==1,'Expected pre-Ultimate Nana character0 armor0 flag1')
        require(struct.unpack_from('<II',p,0x38)==(gptr,cptr),'Wrong active graphics/composition bank')
        expected_palette=es[9][:32];palette_start=read(a.vram_base+480*2048,32)
        out.mkdir(parents=True);(out/'ram_start.bin').write_bytes(ram)
        print(json.dumps({'ready':True,'pid':a.pid,'seconds':a.seconds,'output':str(out),'body_palette_equals_row0':palette_start==expected_palette}),flush=True)
        start=time.monotonic();events=[];polls=0;skipped=0;key=None;active=None;matched=set();guard_before=read(a.ram_base+BUF-64,64);guard_after=read(a.ram_base+BUF+CAPACITY,64)
        while time.monotonic()-start<a.seconds:
            p=read(a.ram_base+PLAYER,228);n=p[0x47];gp,cp=struct.unpack_from('<II',p,0x38)
            if p[2]!=0 or p[0xa7]!=0 or n not in frames or gp!=gptr or cp!=cptr:skipped+=1;time.sleep(.004);continue
            f,expected=frames[n];sample_key=(n,p[0x17],p[0x15],p[0x93]);now=time.monotonic()-start
            if sample_key!=key:
                active=dict(first_seen_seconds=now,last_seen_seconds=now,frame=n,animation=p[0x17],facing_raw=p[0x15],weapon=p[0x93],tiles=f['tile_count'],hp=p[0x5c],attempts=0,stable_samples=0,ram_mismatch_samples=0,gpu_mismatch_samples=0,verified=False)
                events.append(active);key=sample_key
            decoded=read(a.ram_base+BUF,len(expected));gpu=bytearray()
            for first in range(0,f['tile_count'],16):
                width=min(16,f['tile_count']-first)*8
                for y in range(16):gpu+=read(a.vram_base+(first//16*16+y)*2048+640,width)
            after=read(a.ram_base+PLAYER,228);active['attempts']+=1;active['last_seen_seconds']=time.monotonic()-start;polls+=1
            if (after[0x47],after[0x17],after[0x15],after[0x93])==sample_key and struct.unpack_from('<II',after,0x38)==(gptr,cptr):
                active['stable_samples']+=1;active['ram_mismatch_samples']+=decoded!=expected;active['gpu_mismatch_samples']+=gpu!=expected
                if decoded==gpu==expected and not active['verified']:
                    clut=struct.unpack_from('<H',p,0x42)[0];body_clut=0x7840 if clut&0x8000 else clut;pos=(body_clut>>6)*2048+(body_clut&63)*32;colors=read(a.vram_base+pos,32)
                    active.update(verified=True,verified_seconds=time.monotonic()-start,ram_sha256=sha(decoded),gpu_sha256=sha(gpu),expected_sha256=sha(expected),decoded_end_exclusive=hex(BUF+len(expected)),remaining_buffer_bytes=CAPACITY-len(expected),gpu_rows=16*((f['tile_count']+15)//16),body_clut=hex(body_clut),palette_matching_arc_rows=[i for i in range(len(es[9])//32) if es[9][i*32:(i+1)*32]==colors]);matched.add(n)
                    file=out/f'frame_{n:03}_{len(events):03}.bin';file.write_bytes(gpu);active['gpu_capture']=file.name
            time.sleep(.004)
        final=read(a.ram_base,0x200000);(out/'ram_end.bin').write_bytes(final)
        return dict(pid=a.pid,ram_host_base=a.ram_base,vram_host_base=a.vram_base,seconds=time.monotonic()-start,polls=polls,skipped_samples=skipped,assets=assets,assets_still_exact={kind:final[v['ram_offset']:v['ram_offset']+v['size']]==es[int(kind)] for kind,v in assets.items()},graphics_bank_pointer=hex(gptr),composition_bank_pointer=hex(cptr),verified_frames=sorted(matched),verified_high_tile_frames=sorted(n for n in matched if frames[n][0]['tile_count']>=29),events=events,unverified_transitions=[i for i,e in enumerate(events) if not e['verified']],guard64_before_start_sha256=sha(guard_before),guard64_before_end_sha256=sha(final[BUF-64:BUF]),adjacent_buffer64_start_sha256=sha(guard_after),adjacent_buffer64_end_sha256=sha(final[BUF+CAPACITY:BUF+CAPACITY+64]),keys_sent=False,process_memory_written=False,limitation='Live RAM/GPU samples are not atomic and adjacent buffers may be used by other game objects. Overflow safety is established separately by native isolated-CPU writes; this watch only proves observed frame decode/upload and resident assets. Unobserved frames are not counted as runtime tested.')
    finally:k.CloseHandle(h)

def main(a):
    out=a.out.resolve();require(out.is_relative_to(ROOT/'work/overhaul_20261105/audio') and not out.exists(),'Fresh isolated audio evidence output required')
    arc,exe,es,bank,frames=load();report=dict(bin=BUILD.relative_to(ROOT).as_posix(),bin_sha256=BIN_SHA,arc_sha256=sha(arc),buffer_start=hex(BUF),buffer_end_exclusive=hex(BUF+CAPACITY),buffer_capacity=CAPACITY)
    if a.cpu_only:
        observed=cpu_checks(exe,es,bank,frames)
        unobserved=cpu_checks(exe,es,bank,frames,observe_writes=False)
        require(observed==unobserved,'Memory observer changes native results')
        report.update(cpu_checks=observed,native_results_identical_without_memory_observer=True,actual_process_opened=False);out.mkdir(parents=True)
    else:report.update(watch(a,arc,exe,es,bank,frames,out))
    (out/'evidence.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
    print(json.dumps({'output':str(out),'cpu_checks':len(report.get('cpu_checks',[])),'verified_frames':report.get('verified_frames'),'verified_high_tile_frames':report.get('verified_high_tile_frames')}),flush=True)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--cpu-only',action='store_true');p.add_argument('--pid',type=int);p.add_argument('--ram-base',type=lambda x:int(x,0));p.add_argument('--vram-base',type=lambda x:int(x,0));p.add_argument('--seconds',type=float,default=15);p.add_argument('--out',type=Path,required=True);main(p.parse_args())
