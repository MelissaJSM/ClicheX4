"""ePSXe/SPU 레지스터 후보를 읽기 전용으로 폴링한다. 재생 청취 검증 아님."""
import argparse,ctypes,json,struct,time
from ctypes import wintypes
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def main(a):
    out=a.out.resolve()
    if not out.is_relative_to(ROOT/'work/overhaul_20261105/audio') or out.exists():raise ValueError('Fresh audio path required')
    if not 0<=a.seconds<=45:raise ValueError('Watch at most 45 seconds')
    # Reserve the destination before sampling; concurrent watchers must not race.
    out.parent.mkdir(parents=True,exist_ok=True)
    with out.open('x',encoding='utf8') as f:json.dump({'status':'watching','pid':a.pid},f)
    k=ctypes.WinDLL('kernel32',use_last_error=True)
    k.OpenProcess.argtypes=[wintypes.DWORD,wintypes.BOOL,wintypes.DWORD];k.OpenProcess.restype=wintypes.HANDLE
    k.ReadProcessMemory.argtypes=[wintypes.HANDLE,ctypes.c_void_p,ctypes.c_void_p,ctypes.c_size_t,ctypes.POINTER(ctypes.c_size_t)];k.CloseHandle.argtypes=[wintypes.HANDLE]
    h=k.OpenProcess(0x410,False,a.pid)
    if not h:raise OSError('Read-only process open failed')
    def read(at,n):
        b=ctypes.create_string_buffer(n);got=ctypes.c_size_t()
        return b.raw if k.ReadProcessMemory(h,at,b,n,ctypes.byref(got)) and got.value==n else b''
    try:
        bases={'sdk_shadow':a.ram_base+0x166d90,'host_registers':a.register_base}
        previous={};events=[];start=time.monotonic();count=0;prior_command=None
        while True:
            now=time.monotonic()-start;rawptr=read(a.ram_base+0x137e08,4)
            if len(rawptr)!=4:raise ValueError('PSX RAM no longer readable')
            ptr=struct.unpack('<I',rawptr)[0];command=read(a.ram_base+(ptr&0x1fffffff),4)
            event={'seconds':now,'last_command_pointer':hex(ptr),'last_command':command.hex(),'changes':{}}
            for label,base in bases.items():
                raw=read(base,0x200)
                if len(raw)!=0x200:raise ValueError('Register region unreadable')
                old=previous.get(label);changes=[]
                for channel in range(24):
                    x=raw[channel*16:(channel+1)*16]
                    if old is not None and old[channel*16:(channel+1)*16]==x:continue
                    vol_l,vol_r,pitch,address,adsr1,adsr2,current,repeat=struct.unpack('<8H',x)
                    changes.append(dict(channel=channel,left=vol_l,right=vol_r,pitch=pitch,start_register=address,start_byte=address*8,adsr1=adsr1,adsr2=adsr2,current_envelope=current,repeat_register=repeat,raw=x.hex()))
                # 0x188/0x18c: key-on/off; 0x19c: voice end flags. Shadows may retain writes.
                common={name:struct.unpack_from('<I',raw,off)[0]&0xffffff for name,off in (('key_on',0x188),('key_off',0x18c),('end_flags',0x19c))}
                if changes or old is None or old[0x180:]!=raw[0x180:]:event['changes'][label]={'voices':changes,'common':common,'tail_hex':raw[0x180:0x1b0].hex()}
                previous[label]=raw
            if event['changes'] or prior_command!=ptr:events.append(event)
            prior_command=ptr;count+=1
            if now>=a.seconds:break
            time.sleep(.002)
        evidence=dict(pid=a.pid,ram_base=a.ram_base,register_bases=bases,seconds=time.monotonic()-start,polls=count,events=events,keys_sent=False,process_memory_written=False,register_layout='candidate standard 24 voices x 16 bytes; dynamic comparison required',audible_output_verified=False)
        out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(evidence,indent=2),encoding='utf8')
        hits=[]
        for e in events:
            for label,change in e['changes'].items():
                for v in change['voices']:
                    if v['channel']==20 and v['pitch']==0x800 and v['start_register'] in (0x2b7e,0x1114):hits.append({'seconds':e['seconds'],'registers':label,**v})
        print(json.dumps(dict(output=str(out),seconds=evidence['seconds'],polls=count,event_count=len(events),hurt_or_death_matches=hits)))
    finally:k.CloseHandle(h)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--pid',type=int,required=True);p.add_argument('--ram-base',type=lambda v:int(v,0),required=True);p.add_argument('--register-base',type=lambda v:int(v,0),required=True);p.add_argument('--seconds',type=float,default=20);p.add_argument('--out',type=Path,required=True);main(p.parse_args())
