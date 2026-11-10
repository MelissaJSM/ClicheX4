"""Native execution and write-boundary tests for state-dependent portraits."""
import json,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32,UC_HOOK_MEM_WRITE
from unicorn.x86_const import *
from src.steam_dialogue_variants import build,native_sequences
W=ROOT/'work/steam_port_20261109'
def main():
    spec=json.loads((W/'dialogue_variant_runtime.json').read_text('utf8'));base=0x3000000;blob,hooks=build(base,spec['zero_palettes']);u=Uc(UC_ARCH_X86,UC_MODE_32);u.mem_map(0x400000,0x3000000)
    code=(W/'runtime/code/text.bin').read_bytes();u.mem_write(0x401000,code);u.mem_write(base,blob)
    engine=0x2700000;app=0x2800000;palette=0x2500000;actor=0x2600000;stack=0x2901000;ret=0x2801000
    u.mem_write(0x1b9b140,struct.pack('<I',engine));writes=[]
    u.hook_add(UC_HOOK_MEM_WRITE,lambda uc,access,a,size,value,data:writes.append((a,size)))
    def run(function,arg):
        u.mem_write(stack,struct.pack('<II',ret,arg));u.mem_write(actor,bytes(512));u.reg_write(UC_X86_REG_ESP,stack);u.reg_write(UC_X86_REG_ECX,actor);u.reg_write(UC_X86_REG_EAX,0x12340000);u.reg_write(UC_X86_REG_EDX,0x11223344);u.reg_write(UC_X86_REG_EFLAGS,0x202)
        for r in [UC_X86_REG_EBX,UC_X86_REG_EBP,UC_X86_REG_ESI,UC_X86_REG_EDI]:u.reg_write(r,0x778899aa)
        writes.clear();u.emu_start(function,ret,count=10000)
        assert u.reg_read(UC_X86_REG_ESP)==stack+8 and u.reg_read(UC_X86_REG_EDX)==0x11223344
        assert all(u.reg_read(r)==0x778899aa for r in [UC_X86_REG_EBX,UC_X86_REG_EBP,UC_X86_REG_ESI,UC_X86_REG_EDI])
        return [(a,n) for a,n in writes if not stack-512<=a<stack+8]
    animation_cases=palette_cases=0
    for char in [0,1,2]:
        u.mem_write(engine+0xeb,bytes([char]))
        for special in [0,1,2]:
            u.mem_write(engine+0xdf,bytes([special]))
            for armor in [*range(16),255]:
                u.mem_write(engine+0xef,bytes([armor]))
                for arg in [0x1adb108,0x1adb128]:
                    wr=run(base,arg);expected=(base+(0xa00 if armor else 0x800)) if char==0 and special and arg==0x1adb108 else arg
                    assert struct.unpack('<I',u.mem_read(actor+0x4c,4))[0]==expected and wr==[(actor+0x4c,4)];animation_cases+=1
            for region in [0,1,2,3,4,None]:
                u.mem_write(0x1b43a08,struct.pack('<I',app if region is not None else 0));u.mem_write(app+0x78,struct.pack('<I',region or 0))
                for present in [False,True]:
                    u.mem_write(0x1b9b11c,struct.pack('<I',palette if present else 0))
                    for row in [26,30,50,54,58,62,63,127,128]:
                        dest=palette+0x1002c+row*32;u.mem_write(dest,bytes([0x5a])*32);u.mem_write(palette+0x2802c,b'\x08')
                        wr=run(base+0x400,row);enabled=present and char==1 and region is not None and row<128
                        expected=bytes.fromhex(spec['zero_palettes']['rn' if region==1 else 'br']['black_hex' if special else 'normal_hex']) if enabled else bytes([0x5a])*32
                        assert bytes(u.mem_read(dest,32))==expected and u.mem_read(palette+0x2802c,1)==bytes([9 if enabled else 8])
                        allowed={actor+0x5e,actor+0x5f}
                        if enabled:allowed.update(range(dest,dest+32));allowed.add(palette+0x2802c)
                        assert all(set(range(a,a+n))<=allowed for a,n in wr);assert struct.unpack('<H',u.mem_read(actor+0x5e,2))[0]==row;palette_cases+=1
    seq=native_sequences();old=[seq[n*16:n*16+4] if i%2==0 else seq[n*16+4:n*16+16] for n in range(4) for i in range(2)]
    for post,offset in [(False,0x800),(True,0xa00)]:
        for ptr,prior in zip(struct.unpack_from('<8I',blob,offset),old):
            now=blob[ptr-base:ptr-base+len(prior)]
            for p in range(0,len(prior),4):assert now[p:p+3]==prior[p:p+3] and now[p+3]==(9 if post else 8)+(2 if prior[p+3]>=4 else 0)
    result={'animation_selector_cases':animation_cases,'palette_selector_cases':palette_cases,'native_animation_durations_flags_preserved':True,'no_game_state_writes':True,'palette_write_bounds_verified':True,'stack_and_saved_registers_preserved':True}
    (W/'dialogue_variant_cpu_verification.json').write_text(json.dumps(result,indent=2)+'\n');print(result)
if __name__=='__main__':main()
