"""fresh Riko 체이서 F1의 음향 로딩과 실제 SDK 호출을 읽기 전용 검증한다."""
import gzip,hashlib,json,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.discover_inputs import DiscReader
from scripts.overhaul_audio_verify_cpu import banks
from scripts.overhaul_nana_progress_refresh import loaded_vab_header
from src.psx_spu_audio import decode_spu
from unicorn import Uc,UC_ARCH_MIPS,UC_MODE_MIPS32,UC_MODE_LITTLE_ENDIAN,UC_HOOK_CODE
from unicorn import mips_const as m
SOURCE=ROOT/'work/overhaul_20261105/runtime/riko_chaser_fresh_state/SLUS_005.61.000'
STATE_SHA='d392bf6b3d9421512b867985b3f0b44bd0958dc0d3f2a4eda7e1d33f4f2274d7'
BIN=ROOT/'out/ver_buki_riko/overhaul_20261105_candidate03/shibuki_riko.bin'
BIN_SHA='be4468029fe2941a840b9693558cbaccc980b7519e6df2f2af9f66f208506c1e'
OUT=ROOT/'work/overhaul_20261105/audio/riko_fresh_sound_v1'
PREPARED=ROOT/'work/overhaul_20261105/audio/prepared/ver_buki_riko'

def sha(b):return hashlib.sha256(b).hexdigest()
def digest(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(8388608),b''):h.update(b)
    return h.hexdigest()
def require(x,msg):
    if not x:raise ValueError(msg)

def native_case(ram,loaded,starts,stage6,slot,command):
    u=Uc(UC_ARCH_MIPS,UC_MODE_MIPS32|UC_MODE_LITTLE_ENDIAN);u.mem_map(0,0x200000);u.mem_map(0x1f801000,0x1000);u.mem_write(0,ram)
    if slot==2:
        h,b,q=banks(stage6)[2];u.mem_write(0x5000,h);u.mem_write(0x141f58,struct.pack('<I',0x80005008));u.mem_write(0x141ef0,struct.pack('<I',0x80005000+q['vab_offset']))
        # The real Chaser scene has no bank2. These ST6 commands cross-reference
        # already-loaded bank3, but the dispatcher first requires source bank2
        # to be registered. This byte is set only in the isolated CPU harness.
        require(ram[0x13e19a]==255,'Expected absent Chaser source bank2')
        u.mem_write(0x13e19a,b'\x02')
    saved={m.UC_MIPS_REG_SP:0x801ff000,m.UC_MIPS_REG_RA:0x80008000}
    for i,reg in enumerate((m.UC_MIPS_REG_S0,m.UC_MIPS_REG_S1,m.UC_MIPS_REG_S2,m.UC_MIPS_REG_S3,m.UC_MIPS_REG_S4,m.UC_MIPS_REG_S5,m.UC_MIPS_REG_S6,m.UC_MIPS_REG_S7,m.UC_MIPS_REG_FP)):saved[reg]=0x123400+i
    for reg,val in saved.items():u.reg_write(reg,val)
    for reg,val in ((m.UC_MIPS_REG_A0,slot),(m.UC_MIPS_REG_A1,command),(m.UC_MIPS_REG_A2,0)):u.reg_write(reg,val)
    calls=[]
    def hook(cpu,address,size,user):
        if address==0x80008000:cpu.emu_stop();return
        if address==0x800dfcfc:
            channel,bank,program,tone=[cpu.reg_read(reg) for reg in (m.UC_MIPS_REG_A0,m.UC_MIPS_REG_A1,m.UC_MIPS_REG_A2,m.UC_MIPS_REG_A3)]
            h,b,q=loaded[bank];at=q['vab_offset']+32+128*16+(program*16+tone)*32;t=h[at:at+32];wave=struct.unpack_from('<H',t,22)[0];w=q['waves'][wave-1]
            encoded=b[w['body_offset']:w['body_offset']+w['bytes']];pcm=decode_spu(encoded).pcm
            calls.append(dict(channel=channel,bank=bank,program=program,tone=tone,wave=wave,expected_start_register=(starts[bank]+w['body_offset'])//8,wave_sha256=sha(encoded),pcm_nonzero=any(pcm),center=t[4],tone_volume=t[2]))
    u.hook_add(UC_HOOK_CODE,hook);u.emu_start(0x8001540c,0,count=200000)
    require(u.reg_read(m.UC_MIPS_REG_PC)==0x80008000 and u.reg_read(m.UC_MIPS_REG_V0)==0,f'Native dispatch/SDK failed: slot={slot}, command={command}, PC={u.reg_read(m.UC_MIPS_REG_PC):08X}, V0={u.reg_read(m.UC_MIPS_REG_V0):08X}, calls={calls}')
    require(all(u.reg_read(reg)==val for reg,val in saved.items()),'Native caller registers not preserved')
    require(len(calls)==1,'Unexpected voice count')
    for c in calls:
        left,right,pitch,start,adsr1,adsr2,envelope,repeat=struct.unpack('<8H',u.mem_read(0x166d90+c['channel']*16,16))
        require(start==c['expected_start_register'] and pitch>0 and left>0 and right>0,'SDK selected incorrect/silent voice registers')
        c.update(start_register=start,left=left,right=right,pitch=pitch,adsr1=adsr1,adsr2=adsr2)
    c=calls[0]
    if slot==2:require(c['bank']==3 and c['tone']==(14 if command==196 else 15) and c['pitch']==0x400 and c['pcm_nonzero'],'Peacock route wrong')
    elif command in (0,1,12):require(c['bank']==0 and c['pitch']==0x800 and c['pcm_nonzero'],'Nonvocal hurt/death route wrong')
    elif command==10:require(c['bank']==1 and c['pcm_nonzero'],'Rakuhouha effect missing')
    else:require(c['bank']==3 and not c['pcm_nonzero'],'Protagonist muted voice restored accidentally')
    return dict(source_slot=slot,command=command,calls=calls,native_sdk_executed=True,sdk_functions_mocked=False,caller_registers_preserved=True,stage6_commands_injected_only_in_cpu_harness=slot==2,stage6_source_bank_registration_byte_set_only_in_harness=slot==2)

def main():
    require(not OUT.exists(),'Fresh isolated output required');packed=SOURCE.read_bytes();require(sha(packed)==STATE_SHA,'Source F1 differs');require(digest(BIN)==BIN_SHA,'Source BIN differs')
    state=gzip.decompress(packed);require(len(state)==4254418 and state.startswith(b'ePSXe\x06\x00SLUS_005.61'),'Unexpected state format');ram=state[442:442+0x200000]
    player=ram[0x1418c8:0x1418c8+228];require(player[2]==1 and player[0x17]==65 and player[0xc5]==255 and ram[0x1721cc]==5,'Expected actual Riko Ride Chaser state')
    with BIN.open('rb') as f:
        d=DiscReader(f,BIN.stat().st_size);rows={r['name'].split(';')[0]:r for r in d.inspect()['files'] if r['name'].split(';')[0] in ('PL01_U.ARC','ST6_1_1.ARC','SLUS_005.61')};files={n:d.read(r['lba'],r['size']) for n,r in rows.items()}
    loaded=banks(files['PL01_U.ARC']);planned=banks((PREPARED/'PL01_U.ARC').read_bytes());require(set(loaded)==set(planned)=={0,1,3},'Unexpected player bank set')
    for addr in (0x1540c,0xdfcfc,0xe43f8):require(ram[addr:addr+64]==files['SLUS_005.61'][addr-0x10000+2048:addr-0x10000+2112],'EXE anchor not loaded')
    starts=struct.unpack_from('<4I',ram,0x141f30);cmds=struct.unpack_from('<4I',ram,0x141f50)
    b0=loaded[0][1];needle=b0[64:192];pos=state.find(needle);candidates=[]
    while pos>=0:
        base=pos-starts[0]-64
        if 0<=base and base+0x80000<=len(state) and all(state[base+starts[s]:base+starts[s]+len(b)]==b for s,(h,b,q) in loaded.items()):candidates.append(base)
        pos=state.find(needle,pos+1)
    require(len(candidates)==1,'SPURAM not uniquely identified from all three banks');spu=candidates[0];results=[]
    for slot,(h,b,q) in loaded.items():
        require(h==planned[slot][0] and b==planned[slot][1],'Prepared audio differs in integrated disc')
        at=(cmds[slot]&0x1fffffff)-8;expected=loaded_vab_header(h,b,starts[slot]);require(ram[at:at+len(expected)]==expected,'Native loaded VAB/SDK cache mismatch')
        for table,want in ((0x141840,at+q['vab_offset']),(0x1406b8,at+q['vab_offset']+32),(0x141888,at+q['vab_offset']+32+2048)):
            require(struct.unpack_from('<I',ram,table+slot*4)[0]&0x1fffffff==want,'SDK VAB pointer cache differs')
        require(struct.unpack_from('<I',ram,0x175ea8+slot*4)[0]==starts[slot] and struct.unpack_from('<I',ram,0x175e58+slot*4)[0]==len(b),'SDK transfer state differs')
        results.append(dict(bank=slot,spu_start=starts[slot],body_bytes=len(b),body_sha256=sha(b),vab_ram_address=hex(0x80000000+at),loaded_header_sha256=sha(expected),wave_count=q['wave_count'],all_spuram_bytes_equal_prepared=True,all_vab_header_and_sdk_program_wave_cache_bytes_equal=True,sdk_pointer_and_transfer_caches_equal=True))
    native=[native_case(ram,loaded,starts,files['ST6_1_1.ARC'],3,n) for n in range(13)]+[native_case(ram,loaded,starts,files['ST6_1_1.ARC'],2,n) for n in (196,199)]
    require(SOURCE.read_bytes()==packed and digest(BIN)==BIN_SHA,'Source changed during read-only verification')
    report=dict(source_state=SOURCE.relative_to(ROOT).as_posix(),source_state_sha256=STATE_SHA,source_bin=BIN.relative_to(ROOT).as_posix(),source_bin_sha256=BIN_SHA,source_player_sha256=sha(player),character=1,stage=5,area=ram[0x1721cd],animation=player[0x17],frame=player[0x47],spu_state_offset=spu,loaded_banks=results,native_sdk_checks=native,all_native_sdk_checks_passed=True,protagonist_voice_mute_preserved=True,rakuhouha_effect_preserved=True,actual_process_opened=False,keys_sent=False,source_files_modified=False,scope='루트 새 부팅 Riko 체이서 F1에서 Zero 계열 음향 전체 로딩과 native SDK 실행 검증. 체이서 상태의 일반 피격·사망 게임플레이 재생 성공이나 피콕 실전 발화로 주장하지 않음.',limitations=['실제 피격/사망은 CPU 시험 메모리에서 명령을 호출했다.','체이서 스테이지에는 boss bank2가 없다. 피콕 ST6 명령표/포인터와 source bank2 등록 바이트(0x13E19A: FF→02)를 CPU 시험에만 임시 배치했다. 등록 바이트가 FF인 원래 상태에서는 디스패처가 -1을 반환하며 재생하지 않는다. 실제 F1/카드는 수정하지 않았다.','청취 품질·하드웨어 출력·보스 실제 호출 타이밍은 이 검사로 확인하지 않았다.'])
    OUT.mkdir(parents=True);(OUT/'evidence.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps(dict(output=str(OUT),banks=len(results),native_calls=len(native),source_preserved=True)))
if __name__=='__main__':main()
