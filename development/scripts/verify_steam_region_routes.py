"""Exercise both native resource lookup functions with every known ID."""
import json,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32
from unicorn.x86_const import *
from src.steam_region_routes import build,routing_data,CONTEXT_POINTER
W=ROOT/'work/steam_port_20261109'
def main():
    exe=(W/'original/RXC1.exe').read_bytes();code=(W/'runtime/code/text.bin').read_bytes();rows,selected=routing_data(exe)
    base=0x3000000;blob,hooks=build(exe,base);u=Uc(UC_ARCH_X86,UC_MODE_32);u.mem_map(0x400000,0x3000000)
    u.mem_write(0x401000,code);u.mem_write(0xf6c000,exe[0xb6b400:0xb6c700]);u.mem_write(base,blob)
    for addr,old,new in hooks:
        assert bytes(u.mem_read(addr,len(old)))==old;u.mem_write(addr,new)
    names={k:(ptr,name) for k,ptr,name in rows};targets={k:name for k,ptr,name in selected};checks=0
    for function in [0x98d490,0x98d4f0]:
        for region in [None,0,1,2,3,4]:
            u.mem_write(CONTEXT_POINTER,struct.pack('<I',0 if region is None else 0x2800000));u.mem_write(0x2800078,struct.pack('<I',region or 0))
            for key in list(names)+[0xffffffff,0x10000]:
                stack=0x2901000;u.mem_write(stack,struct.pack('<II',0x2801000,key));u.reg_write(UC_X86_REG_ESP,stack)
                regs=[UC_X86_REG_EBX,UC_X86_REG_EBP,UC_X86_REG_ESI,UC_X86_REG_EDI]
                for n,r in enumerate(regs):u.reg_write(r,0x11111111+n)
                u.emu_start(function,0x2801000,count=10000);got=u.reg_read(UC_X86_REG_EAX)
                if key not in names:assert got==0
                else:
                    text=bytes(u.mem_read(got,60)).split(b'\0')[0].decode('ascii')
                    expected=('cliche_br_' if function==0x98d490 and key in targets and region not in [None,1] else '')+names[key][1]
                    assert text==expected,(function,region,key,text,expected)
                assert u.reg_read(UC_X86_REG_ESP)==stack+4
                assert all(u.reg_read(r)==0x11111111+n for n,r in enumerate(regs))
                checks+=1
    report={'native_lookup_cases':checks,'all_original_resource_ids_tested':len(names),'shared_names':list(targets.values()),'jp_and_null_keep_original':True,'unrelated_resources_preserved':True,'callee_saved_and_stack_preserved':True}
    (W/'portrait_routes_cpu_verification.json').write_text(json.dumps(report,indent=2)+'\n');print(report)
if __name__=='__main__':main()
