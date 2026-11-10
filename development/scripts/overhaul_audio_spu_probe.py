"""지정 ePSXe PID/RAM 기준으로 SPURAM을 읽기만 한다. 입력/메모리 쓰기 없음."""
import argparse,ctypes,hashlib,json,struct,sys,time
from ctypes import wintypes
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.capture_poc_memory import Region
from scripts.overhaul_audio_verify_cpu import banks

def main(a):
    out=a.out.resolve()
    if not out.is_relative_to(ROOT/'work/overhaul_20261105/audio') or out.exists():raise ValueError('Fresh audio output required')
    loaded=banks(a.player.read_bytes())
    if a.boss:loaded.update(banks(a.boss.read_bytes()))
    k=ctypes.WinDLL('kernel32',use_last_error=True)
    k.OpenProcess.argtypes=[wintypes.DWORD,wintypes.BOOL,wintypes.DWORD];k.OpenProcess.restype=wintypes.HANDLE
    k.ReadProcessMemory.argtypes=[wintypes.HANDLE,ctypes.c_void_p,ctypes.c_void_p,ctypes.c_size_t,ctypes.POINTER(ctypes.c_size_t)]
    k.VirtualQueryEx.argtypes=[wintypes.HANDLE,ctypes.c_void_p,ctypes.POINTER(Region),ctypes.c_size_t];k.CloseHandle.argtypes=[wintypes.HANDLE]
    handle=k.OpenProcess(0x410,False,a.pid)
    if not handle:raise OSError('Read-only process access failed')
    def read(address,size):
        b=ctypes.create_string_buffer(size);got=ctypes.c_size_t()
        return b.raw if k.ReadProcessMemory(handle,address,b,size,ctypes.byref(got)) and got.value==size else b''
    try:
        ram=read(a.ram_base,0x200000)
        if len(ram)!=0x200000:raise ValueError('RAM unreadable')
        # Fixed native dispatcher anchor; candidate patches do not change audio code.
        if ram[0x1540c:0x1541c]!=bytes.fromhex('e8ffbd277f0082301000bfaf1480013c'):raise ValueError('Wrong PSX RAM base')
        starts=struct.unpack_from('<4I',ram,0x141f30);tables=struct.unpack_from('<4I',ram,0x141f50)
        evidence={}
        for slot,(h,b,q) in loaded.items():
            p=tables[slot]&0x1fffffff;n=q['command_count']*4
            evidence[str(slot)]=dict(spu_start=starts[slot],body_bytes=len(b),command_table=hex(tables[slot]),command_bytes_match=ram[p:p+n]==h[8:8+n],body_sha256=hashlib.sha256(b).hexdigest())
        # Original common effect anchor, plus complete independent banks as proof.
        h,b,q=loaded[0];w=q['waves'][1];off=w['body_offset']+64;needle=b[off:off+128]
        if len(set(needle))<16:raise ValueError('Weak anchor')
        adjust=starts[0]+off;candidates=set();address=0
        while address<0x100000000:
            r=Region()
            if not k.VirtualQueryEx(handle,address,ctypes.byref(r),ctypes.sizeof(r)):break
            lo=r.base or 0;end=lo+r.size
            if end<=address:break
            if r.state==0x1000 and not r.protect&0x100 and r.protect&255 in (2,4,8,32,64,128):
                for at in range(lo,end,1048576):
                    block=read(at,min(end-at,1048704));pos=block.find(needle)
                    while pos>=0:
                        base=at+pos-adjust
                        if base>0:candidates.add(base)
                        pos=block.find(needle,pos+1)
            address=end
        found=[]
        for base in sorted(candidates):
            data=read(base,0x80000)
            if len(data)!=0x80000:continue
            matches={str(slot):data[starts[slot]:starts[slot]+len(b)]==b for slot,(h,b,q) in loaded.items() if starts[slot]+len(b)<=0x80000}
            # Only label SPURAM when all three independent player banks agree.
            if not all(matches.get(str(slot)) for slot in (0,1,3)):continue
            found.append(dict(host_base=base,body_matches=matches,sha256=hashlib.sha256(data).hexdigest()))
            out.mkdir(parents=True,exist_ok=True);(out/f'spuram_{base}.bin').write_bytes(data)
        events=[];previous=None;start=time.monotonic();limit=max(0,min(a.watch_seconds,30))
        while True:
            current=read(a.ram_base+0x137e08,4)
            if len(current)!=4:break
            pointer=struct.unpack('<I',current)[0]
            if pointer!=previous:
                address=pointer&0x1fffffff;event=dict(seconds=time.monotonic()-start,pointer=hex(pointer),command_hex=read(a.ram_base+address,4).hex())
                for slot,(h,b,q) in loaded.items():
                    diff=address-(tables[slot]&0x1fffffff)
                    if diff>=0 and diff%4==0 and diff//4<q['command_count']:event.update(slot=slot,command=diff//4)
                events.append(event);previous=pointer
            if time.monotonic()-start>=limit:break
            time.sleep(.002)
        report=dict(pid=a.pid,ram_base=a.ram_base,player=str(a.player),boss=str(a.boss) if a.boss else None,bank_metadata=evidence,spu_candidates=found,last_command_events=events,spu_voice_register_host_address=None,keys_sent=False,process_memory_written=False,limitation='SPU resident sample bytes and sampled last-command pointer only. Rapid or repeated identical commands may be missed. No audible-output proof.')
        out.mkdir(parents=True,exist_ok=True);(out/'evidence.json').write_text(json.dumps(report,indent=2),encoding='utf8');print(json.dumps(report))
    finally:k.CloseHandle(handle)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--pid',type=int,required=True);p.add_argument('--ram-base',type=lambda x:int(x,0),required=True);p.add_argument('--player',type=Path,required=True);p.add_argument('--boss',type=Path);p.add_argument('--out',type=Path,required=True);p.add_argument('--watch-seconds',type=float,default=0);main(p.parse_args())
