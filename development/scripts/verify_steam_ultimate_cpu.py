"""Execute the native X draw wrapper and the local equipment-mask adapters."""
import hashlib,json,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32,UC_HOOK_CODE,UC_HOOK_MEM_WRITE
from unicorn.x86_const import *
from src.steam_ultimate import build,SIGNATURES,GETTER
W=ROOT/'work/steam_port_20261109'

def main():
    code=(W/'runtime/code/text.bin').read_bytes()
    assert hashlib.sha256(code).hexdigest()=='38ff6b3ca58e7f4119b8ff5082bd0ad68429134eb90ffd3074da77341148e6cc'
    for a,s in SIGNATURES.items():assert code[a-0x401000:a-0x401000+len(bytes.fromhex(s))]==bytes.fromhex(s)
    u=Uc(UC_ARCH_X86,UC_MODE_32);u.mem_map(0x400000,0x3000000);u.mem_write(0x401000,code)
    engine=0x2700000;actor=engine+0x834;obj=0x2800000;stack=0x2901000;stop=0x2801000;base=0x3000000
    blob,hooks=build(base);u.mem_write(base,blob);u.mem_write(0x1b9b140,struct.pack('<I',engine));u.mem_write(obj+0x38,struct.pack('<I',actor))
    calls=[];writes=[]
    def intercept(m,a,size,data):
        if a in (0xaa2d20,0xaa8a20):
            sp=m.reg_read(UC_X86_REG_ESP);n=1 if a==0xaa2d20 else 3;v=struct.unpack('<'+'I'*(n+1),m.mem_read(sp,4*(n+1)))
            calls.append((a,m.reg_read(UC_X86_REG_ECX),*v[1:]));m.reg_write(UC_X86_REG_ESP,sp+4*(n+1));m.reg_write(UC_X86_REG_EIP,v[0])
            for r in [UC_X86_REG_EAX,UC_X86_REG_ECX,UC_X86_REG_EDX]:m.reg_write(r,0xbadbad00)
    u.hook_add(UC_HOOK_CODE,intercept);u.hook_add(UC_HOOK_MEM_WRITE,lambda m,k,a,n,v,d:writes.append((a,n)))
    saved=[UC_X86_REG_EBX,UC_X86_REG_EBP,UC_X86_REG_ESI,UC_X86_REG_EDI]
    def run(patched,special,owned,transient,arm,frame,char=0):
        for a,old,new in hooks:u.mem_write(a,new if patched else old)
        u.ctl_remove_cache(0xaa8570,0xaa8628)
        u.mem_write(engine,bytes(0xb00));u.mem_write(engine+0xdf,bytes([special]));u.mem_write(engine+0xeb,bytes([char]));u.mem_write(engine+0xef,bytes([owned]))
        u.mem_write(actor+0x190,bytes([transient]));u.mem_write(actor+0x1a1,bytes([arm]));u.mem_write(actor+0x66,bytes([frame]))
        before=bytes(u.mem_read(engine,0xb00));u.mem_write(stack,struct.pack('<II',stop,0x12345678));u.reg_write(UC_X86_REG_ESP,stack);u.reg_write(UC_X86_REG_ECX,obj)
        for r in saved:u.reg_write(r,0x778899aa)
        calls.clear();writes.clear();u.emu_start(0xaa8570,stop,count=10000)
        assert u.reg_read(UC_X86_REG_ESP)==stack+8 and all(u.reg_read(r)==0x778899aa for r in saved)
        assert bytes(u.mem_read(engine,0xb00))==before
        assert all(stack-128<=a and a+n<=stack+8 for a,n in writes),writes
        return list(calls)
    count=0
    for transient in range(16):
        for arm in range(256):
            old=run(False,0,15,transient,arm,0);new=run(True,0,15,transient,arm,0)
            assert new==old;count+=1
    for owned in (0,1,15,255):
        for transient in (0,15):
            for arm in (0,1,2):
                for frame in range(256):
                    got=run(True,1,owned,transient,arm,frame)
                    mask=15 if owned==0 or 217<=frame<=230 else 0
                    expected=[(0xaa2d20,obj,0x12345678)]+[(0xaa8a20,obj,0x12345678,part,20 if part==2 and arm==2 else 19) for bit,part in [(8,3),(1,0),(4,2),(2,1)] if mask&bit]
                    assert got==expected,(owned,transient,arm,frame,got,expected);count+=1
    # Hook must be native-equivalent for non-X even if special state is set.
    for char in (1,2):
        for transient in range(16):assert run(True,1,0,transient,2,0,char)==run(False,1,0,transient,2,0,char);count+=1
    # Direct helper verifies native ECX/EFLAGS/high EAX preservation and null fallback.
    direct=0
    for present in (False,True):
        u.mem_write(0x1b9b140,struct.pack('<I',engine if present else 0))
        for special in (0,1):
            u.mem_write(engine+0xdf,bytes([special]));u.mem_write(engine+0xeb,b'\0');u.mem_write(engine+0xef,b'\x0f');u.mem_write(actor+0x66,b'\0');u.mem_write(actor+0x190,b'\x07')
            outputs=[]
            for target in (GETTER,base):
                u.mem_write(stack,struct.pack('<I',stop));u.reg_write(UC_X86_REG_ESP,stack);u.reg_write(UC_X86_REG_ECX,actor);u.reg_write(UC_X86_REG_EAX,0x12345678);u.reg_write(UC_X86_REG_EDX,0xabcdef01);u.reg_write(UC_X86_REG_ESI,obj);u.reg_write(UC_X86_REG_EFLAGS,0x246)
                u.emu_start(target,stop,count=500);outputs.append([u.reg_read(r) for r in (UC_X86_REG_EAX,UC_X86_REG_ECX,UC_X86_REG_EDX,UC_X86_REG_EFLAGS,UC_X86_REG_ESP)])
            assert outputs[0][1:]==outputs[1][1:]
            assert outputs[1][0]==(0x12345600 if present and special else outputs[0][0]);direct+=1
    report={'native_draw_cases':count,'getter_contract_cases':direct,'normal_force_calls_preserved':True,'persistent_ownership_used':True,'hover_nova_effect_layers_preserved':True,'game_state_unchanged':True,'writes_only_local_stack':True,'native_callees_for_drawing_mocked':True,'runtime_scene_verified':False}
    (W/'ultimate_cpu_verification.json').write_text(json.dumps(report,indent=2)+'\n');print(report)
if __name__=='__main__':main()
