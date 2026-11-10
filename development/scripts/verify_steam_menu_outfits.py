"""Execute native save constructors and the pause display selector under x86."""
import hashlib,json,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32,UC_HOOK_CODE,UC_HOOK_MEM_WRITE
from unicorn.x86_const import *
from src.steam_menu_outfits import build,SIGNATURES,PAUSE
W=ROOT/'work/steam_port_20261109'

def main():
    code=(W/'runtime/code/text.bin').read_bytes()
    assert hashlib.sha256(code).hexdigest()=='38ff6b3ca58e7f4119b8ff5082bd0ad68429134eb90ffd3074da77341148e6cc'
    for a,h in SIGNATURES.items():assert code[a-0x401000:a-0x401000+len(bytes.fromhex(h))]==bytes.fromhex(h),(hex(a),h)
    u=Uc(UC_ARCH_X86,UC_MODE_32);u.mem_map(0x400000,0x3000000);u.mem_write(0x401000,code)
    base=0x3000000;engine=0x2700000;app=0x2710000;obj=0x2800000;stack=0x2901000;stop=0x280f000
    blob,hooks=build(base);u.mem_write(base,blob)
    for a,b,c in hooks:assert bytes(u.mem_read(a,len(b)))==b
    u.mem_write(0x1b9b140,struct.pack('<I',engine));u.mem_write(0x1b43a08,struct.pack('<I',app))
    # The region resolver and all slot-record lookups execute native code.
    allocations=[];writes=[];failed=False
    def intercept(m,a,n,d):
        if a not in (0x97f980,0x7ae440):return
        sp=m.reg_read(UC_X86_REG_ESP);ret,arg=struct.unpack('<II',m.mem_read(sp,8))
        if a==0x97f980:
            value=0 if failed else obj+len(allocations)*512;allocations.append(value)
            if value:m.mem_write(value+0x7c,struct.pack('<I',value+0x100))
            m.reg_write(UC_X86_REG_EAX,value)
        else:
            m.mem_write(m.reg_read(UC_X86_REG_ECX),struct.pack('<I',arg))
        m.reg_write(UC_X86_REG_ESP,sp+8);m.reg_write(UC_X86_REG_EIP,ret)
    u.hook_add(UC_HOOK_CODE,intercept)
    u.hook_add(UC_HOOK_MEM_WRITE,lambda m,k,a,n,v,d:writes.append((a,n)))
    saved=[UC_X86_REG_EBX,UC_X86_REG_EBP,UC_X86_REG_ESI,UC_X86_REG_EDI]
    def patch(enabled):
        for a,b,c in hooks:u.mem_write(a,c if enabled else b)
        u.ctl_remove_cache(0x983f00,0x984400);u.ctl_remove_cache(0xa9fc70,0xaa0050)
    def run(enabled,character,special,mask,slot,region,mode,func,fail):
        nonlocal failed
        failed=fail;patch(enabled);allocations.clear();writes.clear()
        u.mem_write(engine,bytes(0x1000));u.mem_write(app,bytes(0x100));u.mem_write(app+0x78,struct.pack('<I',region))
        u.mem_write(engine+0x39c,struct.pack('<I',slot))
        # Every other slot deliberately has a different state.
        for area in (0x3a0,0x4c0):
            for n in range(6):
                data=bytearray(48);data[0]=1;data[3]=15;data[0x29]=1
                u.mem_write(engine+area+48*n,bytes(data))
        addr=engine+(0x3a0 if region==1 else 0x4c0)+48*min(slot,5)
        data=bytearray(48);data[0]=character;data[3]=mask;data[2]=2;data[0x29]=special
        u.mem_write(addr,bytes(data));state=bytes(u.mem_read(engine,0x1000))
        u.mem_write(obj,bytes(4096));u.mem_write(stack,struct.pack('<5I',stop,77,123,mode,9))
        u.reg_write(UC_X86_REG_ESP,stack);u.reg_write(UC_X86_REG_ECX,0x12345678)
        for r in saved:u.reg_write(r,0x778899aa)
        u.emu_start(func,stop,count=5000)
        assert u.reg_read(UC_X86_REG_ESP)==stack+4 and all(u.reg_read(r)==0x778899aa for r in saved)
        assert bytes(u.mem_read(engine,0x1000))==state
        assert all(obj<=a and a+n<=obj+4096 or stack-512<=a and a+n<=stack+20 for a,n in writes),writes
        return bytes(u.mem_read(obj,4096)),list(allocations)
    checks=0
    for region in (0,1):
        for slot in range(6):
            for char in (0,1,255):
                for special in (0,1):
                    for mask in range(16):
                        for mode in (0,1):
                            for fail in (False,True):
                                for func in (0xa9fec0,0xa9fc70):
                                    old,oa=run(False,char,special,mask,slot,region,mode,func,fail)
                                    new,na=run(True,char,special,mask,slot,region,mode,func,fail)
                                    if char==0 and special:
                                        if func==0xa9fec0:
                                            expected=bytearray(old)
                                            if not fail:expected[0x66]=52+bool(mask);struct.pack_into('<H',expected,0x5e,30+bool(mask))
                                            assert new==expected and na==oa
                                        else:assert new==bytes(4096) and not na
                                    else:assert (old,oa)==(new,na)
                                    checks+=1
    patch(True)
    # Only BL changes for item30; all flags/other registers and widgets survive.
    regs=[UC_X86_REG_EAX,UC_X86_REG_EBX,UC_X86_REG_ECX,UC_X86_REG_EDX,UC_X86_REG_ESI,UC_X86_REG_EDI,UC_X86_REG_EBP,UC_X86_REG_ESP,UC_X86_REG_EFLAGS]
    layout=bytes((i*7+3)%38 for i in range(39))
    for i,v in enumerate(layout):u.mem_write(0xf5d8f4+i*8,bytes([v]))
    pcases=0
    for char in (0,1):
        for special in (0,1,255):
            for armor in range(16):
                for item in range(39):
                    u.mem_write(engine+0xeb,bytes([char]));u.mem_write(engine+0xdf,bytes([special]));u.mem_write(engine+0xef,bytes([armor]))
                    for i,r in enumerate(regs):u.reg_write(r,0x12345000+i)
                    u.reg_write(UC_X86_REG_ESP,stack);u.reg_write(UC_X86_REG_ESI,item);u.reg_write(UC_X86_REG_EFLAGS,0x246)
                    before=[u.reg_read(r) for r in regs];writes.clear();u.emu_start(PAUSE,PAUSE+7,count=150)
                    after=[u.reg_read(r) for r in regs];idx=(bool(special) if char else (4+bool(armor) if special else armor&3))
                    before[1]=(before[1]&~255)|(38+idx if item==30 else layout[item])
                    assert after==before and all(stack-12<=a and a+n<=stack for a,n in writes)
                    pcases+=1
    report={'native_save_constructor_cases':checks,'pause_selector_cases':pcases,'all_six_slots_both_regions':True,'native_slot_lookup_executed':True,'save_data_unchanged':True,'normal_force_zero_empty_and_allocation_failure_preserved':True,'mocks':['display object allocator','coordinate numeric setter'],'pause_selector_only_not_full_gpu_draw':True,'runtime_scene_verified':False}
    (W/'menu_outfits_cpu_verification.json').write_text(json.dumps(report,indent=2)+'\n');print(report)
if __name__=='__main__':main()
