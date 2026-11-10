"""Execute HQ outfit routing against real game getters, including invalid states."""
import json,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32
from unicorn.x86_const import *
from src.steam_region_routes import build,routing_data,CONTEXT_POINTER,ENGINE_POINTER,SHARED
W=ROOT/'work/steam_port_20261109'
def main():
    exe=(W/'original/RXC1.exe').read_bytes();code=(W/'runtime/code/text.bin').read_bytes();rows,_=routing_data(exe)
    u=Uc(UC_ARCH_X86,UC_MODE_32);u.mem_map(0x400000,0x3000000);u.mem_write(0x401000,code);u.mem_write(0xf6c000,exe[0xb6b400:0xb6c700])
    blob,hooks=build(exe,0x3000000,True);u.mem_write(0x3000000,blob)
    for a,old,new in hooks:assert bytes(u.mem_read(a,len(old)))==old;u.mem_write(a,new)
    stack=0x2901000;ret=0x2801000;engine=0x2700000;app=0x2800000
    def run(function,key):
        u.mem_write(stack,struct.pack('<II',ret,key));u.reg_write(UC_X86_REG_ESP,stack);u.reg_write(UC_X86_REG_ECX,engine+0x54);u.reg_write(UC_X86_REG_EFLAGS,0x202)
        for r in [UC_X86_REG_EBX,UC_X86_REG_EBP,UC_X86_REG_ESI,UC_X86_REG_EDI]:u.reg_write(r,0x12345678)
        u.emu_start(function,ret,count=10000)
        assert u.reg_read(UC_X86_REG_ESP)==stack+4 and all(u.reg_read(r)==0x12345678 for r in [UC_X86_REG_EBX,UC_X86_REG_EBP,UC_X86_REG_ESI,UC_X86_REG_EDI])
        return u.reg_read(UC_X86_REG_EAX)
    checks=0;getter_checks=0
    for armor in [*range(16),0x80,0xff]:
        for special in [0,1,2]:
            for character in [0,1,2]:
                u.mem_write(engine+0xdf,bytes([special]));u.mem_write(engine+0xeb,bytes([character]));u.mem_write(engine+0xef,bytes([armor]))
                for fn,expected in [(0x986080,armor),(0x9861a0,special),(0x9860d0,character)]:
                    assert run(fn,0)&255==expected;getter_checks+=1
                for region in [0,1,2,3,4,None]:
                    u.mem_write(CONTEXT_POINTER,struct.pack('<I',app if region is not None else 0));u.mem_write(app+0x78,struct.pack('<I',region or 0))
                    for present in [False,True]:
                        u.mem_write(ENGINE_POINTER,struct.pack('<I',engine if present else 0))
                        for key,ptr,name in [q for q in rows if q[2] in ['st0d_0x','st0d_0z']]:
                            original=run(0x98d4f0,key);reference=[u.reg_read(r) for r in [UC_X86_REG_ECX,UC_X86_REG_EDX,UC_X86_REG_EFLAGS]]
                            assert original==ptr
                            result=run(0x98d490,key);assert reference==[u.reg_read(r) for r in [UC_X86_REG_ECX,UC_X86_REG_EDX,UC_X86_REG_EFLAGS]]
                            text=bytes(u.mem_read(result,60)).split(b'\0')[0].decode();expected=('cliche_br_' if region not in [None,1] else '')+name
                            if present and region is not None:
                                mode='rn' if region==1 else 'br'
                                if name=='st0d_0x' and character==0:
                                    state=(16+int(armor!=0)) if special else armor&15
                                    if state:expected=f'cliche_{mode}_hqx_{state:02}'
                                elif name=='st0d_0z' and character==1 and special:expected=f'cliche_{mode}_hqz_01'
                            assert text==expected,(armor,special,character,region,present,name,text,expected);checks+=1
    # All unrelated resources retain the accepted regional v1 behavior.
    for region in [0,1,2,3,4,None]:
        u.mem_write(CONTEXT_POINTER,struct.pack('<I',app if region is not None else 0));u.mem_write(app+0x78,struct.pack('<I',region or 0))
        for key,ptr,name in rows:
            if name in ['st0d_0x','st0d_0z']:continue
            result=run(0x98d490,key);text=bytes(u.mem_read(result,60)).split(b'\0')[0].decode()
            assert text==('cliche_br_' if region not in [None,1] and name in SHARED else '')+name;checks+=1
    result={'native_route_cases':checks,'real_equipment_getter_cases':getter_checks,'register_flags_stack_preserved':True,'internal_resource_names_preserved':True,'source_state_offsets':{'special':'engine+0xdf','character':'engine+0xeb','armor':'engine+0xef'},'runtime_scene_verified':False}
    (W/'hq_variant_cpu_verification.json').write_text(json.dumps(result,indent=2)+'\n');print(result)
if __name__=='__main__':main()
