"""Execute the native portrait selection block with isolated MIPS RAM."""
from pathlib import Path
import json, struct, hashlib
import unicorn as uc
from unicorn import mips_const as m

H=Path(__file__).resolve().parent
START,END=0x80022954,0x800229a0
STOP=0x80008000
OBJ,ENGINE,BANK=0x180000,0x1721c0,0x80160000
original=(H/'selector_original.bin').read_bytes()
replacement=(H/'selector_new.bin').read_bytes()
machine=uc.Uc(uc.UC_ARCH_MIPS,uc.UC_MODE_MIPS32|uc.UC_MODE_LITTLE_ENDIAN)
machine.mem_map(0,0x200000)
writes=[];trace=[]
machine.hook_add(uc.UC_HOOK_CODE,lambda u,a,s,d:trace.append(a))
def record(u,access,address,size,value,data):
    address &= 0x1fffffff
    assert (address,size) in [(OBJ+0x54,1),(OBJ+0x3c,4)],(hex(address),size)
    writes.append((address,size))
machine.hook_add(uc.UC_HOOK_MEM_WRITE,record)
def run(code,char,special,armor):
    global machine
    machine=uc.Uc(uc.UC_ARCH_MIPS,uc.UC_MODE_MIPS32|uc.UC_MODE_LITTLE_ENDIAN)
    machine.mem_map(0,0x200000)
    machine.hook_add(uc.UC_HOOK_MEM_WRITE,record)
    def step(u,a,s,d):
        trace.append(a)
        if a==END:u.emu_stop()
    machine.hook_add(uc.UC_HOOK_CODE,step)
    machine.mem_write(START&0x1fffffff,code+bytes(16))
    machine.ctl_remove_cache(START,END+8)
    obj=bytearray([0xa5]*256);struct.pack_into('<I',obj,0x3c,BANK)
    engine=bytearray([0x5a]*256)
    engine[0x43]=char;engine[0x37]=special;engine[0x47]=armor
    machine.mem_write(OBJ,bytes(obj));machine.mem_write(ENGINE,bytes(engine))
    values={'S0':OBJ|0x80000000,'S1':0x80190000,'S2':0x12345678,'SP':0x801ff000,'RA':STOP}
    for reg,value in values.items():machine.reg_write(getattr(m,'UC_MIPS_REG_'+reg),value)
    writes.clear();trace.clear()
    try:machine.emu_start(START,STOP,count=100)
    except uc.UcError:
        print(char,special,armor,[hex(a) for a in trace],hex(machine.reg_read(m.UC_MIPS_REG_PC)))
        raise
    assert trace[-1]==END,hex(machine.reg_read(m.UC_MIPS_REG_PC))
    assert all(machine.reg_read(getattr(m,'UC_MIPS_REG_'+r))==v for r,v in values.items())
    assert machine.mem_read(ENGINE,256)==engine
    actual=bytes(machine.mem_read(OBJ,256))
    for i,(a,b) in enumerate(zip(actual,obj)):
        assert a==b or i==0x54 or 0x3c<=i<0x40
    return struct.unpack_from('<I',actual,0x3c)[0],actual[0x54],list(writes)

rows=[]
for char in [0,1]:
 for special in [0,1,0xff]:
  for armor in range(16):
    before=run(original,char,special,armor)
    after=run(replacement,char,special,armor)
    expected=(BANK+1376,2*bool(armor)) if char==0 and special else (BANK,2*(armor&3))
    assert after[:2]==expected,(char,special,armor,after,expected)
    if not(char==0 and special):assert after[:2]==before[:2] and len(after[2])==1
    else:assert len(after[2])==2
    rows.append({'character':char,'special_flag':special,'owned_armor_mask':armor,'parts_bank':hex(after[0]),'animation':after[1]})
result={'unicorn_version':uc.__version__,'cases':len(rows),'native_equivalence_cases':sum(not(r['character']==0 and r['special_flag'])for r in rows),'engine_and_player_state_unchanged':True,'only_portrait_object_3c_54_written':True,'callee_saved_registers_preserved':True,'original_sha256':hashlib.sha256(original).hexdigest(),'replacement_sha256':hashlib.sha256(replacement).hexdigest(),'runtime_verified':False,'states':rows}
(H/'cpu_verification.json').write_text(json.dumps(result,indent=2)+'\n','utf8')
print(json.dumps({k:v for k,v in result.items() if k!='states'}))
