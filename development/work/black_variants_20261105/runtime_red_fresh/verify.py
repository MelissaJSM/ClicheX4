"""새 Red Rin 세션의 플래그/팔레트만 읽는다. 키, 저장, 프로세스 쓰기 없음."""
import argparse
import ctypes
from ctypes import wintypes
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import struct
import sys

ROOT=Path(__file__).resolve().parents[3]
OUT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
from scripts.prepare_rin_common import read_disc
from scripts.prepare_riko_ui import entry
from scripts.capture_poc_memory import Region
from src.psx_disc import file_hash

EXPECTED='aca6d7839ad1956ea837b07d1105a7609817cd30fd0e6ceffe13e6dd611ad6fe'

def require(v,reason):
    if not v:raise ValueError(reason)

def all_hits(haystack,needle):
    result=[];p=haystack.find(needle)
    while p>=0:
        result.append(p);p=haystack.find(needle,p+1)
    return result

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--session',required=True,type=Path)
    parser.add_argument('--ram-host',type=int)
    args=parser.parse_args()
    session=args.session.resolve()
    require(session.is_relative_to(ROOT/'work/ver_rin_nana/emulator_sessions'),'Unexpected session')
    record=json.loads((session/'session.local.json').read_text('utf8'))
    game=Path(record['cue']).with_suffix('.bin').resolve()
    require(game==ROOT/'out/ver_rin_nana/black_red_rin_20261105_v1/rin_nana.bin','Unexpected mounted path')
    require(record['bin_sha256']==EXPECTED and file_hash(game)==EXPECTED,'Wrong mounted image')
    ram_base=args.ram_host
    if ram_base is None:
        command=json.loads((session/'black_zero_native_command.json').read_text('utf8'))
        require(command['pid']==record['pid'] and command['source_bin_sha256']==EXPECTED and command['activated'],'Command evidence differs')
        ram_base=command['ram_host_address']
    protected=[]
    for folder,pattern in [('sstates','SLUS_005.61.*'),('memcards','*.mcr')]:
        for p in sorted((ROOT/'work/ver_rin_nana/emulator'/folder).glob(pattern)):
            protected.append(dict(path=str(p.relative_to(ROOT)),sha256=file_hash(p)))
    assets,_=read_disc(game,['PL01_U.ARC','SLUS_005.61','LOAD_U.ARC'])
    pal=entry(assets['PL01_U.ARC'],9);black=pal[13*32:14*32];normal=pal[:32]
    require(len(pal)==2464 and black!=normal,'Expected separately designed Black palette')
    font=entry(assets['LOAD_U.ARC'],0x10001);exe=assets['SLUS_005.61']
    kernel=ctypes.WinDLL('kernel32',use_last_error=True)
    kernel.OpenProcess.argtypes=[wintypes.DWORD,wintypes.BOOL,wintypes.DWORD];kernel.OpenProcess.restype=wintypes.HANDLE
    kernel.ReadProcessMemory.argtypes=[wintypes.HANDLE,ctypes.c_void_p,ctypes.c_void_p,ctypes.c_size_t,ctypes.POINTER(ctypes.c_size_t)]
    kernel.VirtualQueryEx.argtypes=[wintypes.HANDLE,ctypes.c_void_p,ctypes.POINTER(Region),ctypes.c_size_t]
    kernel.CloseHandle.argtypes=[wintypes.HANDLE]
    handle=kernel.OpenProcess(0x410,False,record['pid']);require(handle,'Read-only process open failed')
    def read(address,count):
        b=ctypes.create_string_buffer(count);got=ctypes.c_size_t()
        return b.raw if kernel.ReadProcessMemory(handle,address,b,count,ctypes.byref(got)) and got.value==count else b''
    try:
        require(all(read(ram_base+a,32)==exe[a-0x10000+2048:a-0x10000+2080] for a in (0x233c8,0x23400,0xea20c)),'RAM identity failed')
        engine=read(ram_base+0x1721c0,100);player=read(ram_base+0x1418c8,228)
        require(len(engine)==100 and len(player)==228,'Truncated state read')
        require(engine[0]==6 and engine[0x37]==1 and player[2]==1,'Expected in-game Black Rin')
        clut=struct.unpack_from('<H',player,0x42)[0]
        require(clut==0x7800,'Expected stable non-flashing body CLUT')
        # One transient 2MiB read locates the authenticated resource; it is not saved.
        ram=read(ram_base,0x200000);locations=all_hits(ram,pal)
        require(len(locations)==1,'Palette resource not uniquely equal to new BIN')
        source=locations[0];source_ptr=0x80000000|source
        vn=font[384:512];va=259*2048+1920
        pn=struct.pack('<I',source_ptr);videos=set();scratch=set();address=0;scanned=0
        while address<0x100000000:
            region=Region()
            if not kernel.VirtualQueryEx(handle,address,ctypes.byref(region),ctypes.sizeof(region)):break
            lo=region.base or 0;end=lo+region.size
            if end<=address:break
            if region.state==0x1000 and not region.protect&0x100 and region.protect&255 in (2,4,8,32,64,128):
                for start in range(lo,end,1048576):
                    blob=read(start,min(end-start,1048704));scanned+=len(blob)
                    for pos in all_hits(blob,vn):
                        base=start+pos-va
                        if base>0:videos.add(base)
                    for pos in all_hits(blob,pn):
                        pair=read(start+pos,8)
                        if len(pair)!=8:continue
                        active=struct.unpack_from('<I',pair,4)[0]
                        if 0x80000000<=active<=0x801fffe0 and read(ram_base+(active&0x1fffff),32)==black:
                            scratch.add((start+pos-0x24,active&0x1fffff))
            address=end
        videos={v for v in videos if all(read(v+(256+y)*2048+1920,128)==font[y*128:(y+1)*128] for y in (2,3,4,5))}
        require(len(videos)==1,'VRAM identity is ambiguous')
        # A source/active pair in actual scratchpad is required, not a guessed buffer.
        require(len(scratch)==1,'Active palette scratchpad pair is ambiguous')
        video=next(iter(videos));scratch_host,active=next(iter(scratch))
        gpu=read(video+480*2048,32);filtered=read(ram_base+0x141f70,32)
        require(gpu==black and filtered==black and read(ram_base+active,32)==black,'Red palette was not uploaded consistently')
        after=read(ram_base+0x1721c0,100);afterp=read(ram_base+0x1418c8,228)
        require(after[0]==6 and after[0x37]==1 and afterp[2]==1 and struct.unpack_from('<H',afterp,0x42)[0]==0x7800,'Scene changed during palette audit')
        checks=[]
        for p in protected:
            actual=file_hash(ROOT/p['path']);checks.append(dict(**p,after_sha256=actual,equal=actual==p['sha256']))
        require(all(p['equal'] for p in checks),'Protected file changed during read-only inspection')
        rgb5=[[(w>>shift)&31 for shift in (0,5,10)] for w in struct.unpack('<16H',black)]
        report=dict(passed=True,timestamp_utc=datetime.now(timezone.utc).isoformat(),pid=record['pid'],session=str(session.relative_to(ROOT)),mounted_bin=str(game.relative_to(ROOT)),mounted_bin_sha256=EXPECTED,ram_host_base=ram_base,vram_host_base=video,scratchpad_host_base=scratch_host,black_flag=1,player_character=1,stage=after[12],area=after[13],animation=afterp[0x17],frame=afterp[0x47],hp=afterp[0x5c],world=[struct.unpack_from('<i',afterp,o)[0]/65536 for o in (8,12)],source_palette_ram=hex(source_ptr),source_black_row13_ram=hex(source_ptr+13*32),source_palette_entire_entry_matches=True,active_palette_ram=hex(0x80000000|active),filtered_palette_ram='0x80141F70',body_clut='0x7800',normal_row0_hex=normal.hex(),black_row13_hex=black.hex(),black_rgb5=rgb5,black_differs_from_normal=True,active_filtered_gpu_equal_red_row13=True,protected_files=checks,process_memory_written=False,keys_sent=False,F1_written=False,memory_cards_written=False,large_memory_dump_saved=False,memory_bytes_scanned_transiently=scanned,scope='새 BIN/원작 블랙 커맨드 이후 실제 인게임 source/active/filtered/GPU 적색 팔레트 읽기 대조. 전체 모션·피격/전송/저장 UI 실기 검증과 구분.',limitations=['색상·플래그·리소스 캐시만 검사했다. 화면 전체 이미지 비교는 하지 않았다.','다른 PID나 장면에서 host 주소를 그대로 사용하지 않는다.'])
        (OUT/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf8')
        print(json.dumps({k:report[k] for k in ('passed','pid','black_flag','frame','source_palette_ram','active_palette_ram','vram_host_base')}))
    finally:kernel.CloseHandle(handle)

if __name__=='__main__':main()
