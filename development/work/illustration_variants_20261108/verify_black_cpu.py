"""Differential native MIPS tests; no emulator, saves, or live RAM access."""
from pathlib import Path
import struct, json, random
import unicorn as uc
from unicorn import mips_const as m
from black_ui import H, ROOT, START, END, OLD_ANIMATE, TABLE, HOOK, off, proposal, words, CHANGES

OBJ, ENGINE, PAL, STOP = 0x180000, 0x1721c0, 0x150000, 0x80008000
SET, ANIM, SCREEN = 0x80015d60, 0x80015dc8, 0x8002b288
def run(exe, address, char, special, partner=0, flags=0, armor=0, row=35, end=STOP):
    u=uc.Uc(uc.UC_ARCH_MIPS,uc.UC_MODE_MIPS32|uc.UC_MODE_LITTLE_ENDIAN)
    u.mem_map(0,0x200000); u.mem_map(0x1f800000,4096)
    u.mem_write(0x10000,exe[2048:])
    for addr in (SET,ANIM,SCREEN):u.mem_write(addr&0x1fffffff,bytes(32))
    obj=bytearray([0xa5]*256); obj[2]=partner; obj[4]=0; struct.pack_into('<H',obj,0x42,0x7800+(row//16)*64+row%16)
    struct.pack_into('<I',obj,0x3c,0x80160000)
    u.mem_write(OBJ,bytes(obj))
    engine=bytearray([0x5a]*256); engine[0x37]=special; engine[0x43]=char; engine[0x40]=flags; engine[0x47]=armor
    u.mem_write(ENGINE,bytes(engine))
    pal=bytes((j*37+17)&255 for j in range(4096)); u.mem_write(PAL,pal)
    u.mem_write(0x166bb0,b'\x04')
    u.mem_write(0x1f800028,struct.pack('<I',PAL|0x80000000))
    u.mem_write(0x1f800020,struct.pack('<I',0x80160000))
    u.mem_write(0x1406a8,struct.pack('<I',0x80161000))
    u.mem_write(0x160000,struct.pack('<5I',20,100,180,280,380))
    u.mem_write(0x161000,struct.pack('<5I',0,32768,63488,75776,92160))
    values={'S0':0x80180000 if address==0x80022954 else 0x12340000,'S1':0x12345678,'S2':0x87654321,'S3':0x01010101,'SP':0x801ff000,'RA':STOP,'A0':OBJ|0x80000000}
    for reg,val in values.items():u.reg_write(getattr(m,'UC_MIPS_REG_'+reg),val)
    calls=[]; written=[]; trace=[]
    def code(u,addr,size,data):
        trace.append(addr)
        if addr==end:u.emu_stop(); return
        if addr in (SET,ANIM,SCREEN):
            a0=u.reg_read(m.UC_MIPS_REG_A0); a1=u.reg_read(m.UC_MIPS_REG_A1)
            assert a0==OBJ|0x80000000
            calls.append((addr,a0,a1 if addr==SET else None))
            u.emu_stop()
    def mem(u,access,addr,size,val,data):
        addr&=0x1fffffff
        assert (OBJ<=addr and addr+size<=OBJ+256) or (PAL<=addr and addr+size<=PAL+4096) or (0x1fefc0<=addr and addr+size<=0x1ff000) or (addr==0x166bb0 and size==1),(hex(addr),size)
        written.append((addr,size))
    u.hook_add(uc.UC_HOOK_CODE,code); u.hook_add(uc.UC_HOOK_MEM_WRITE,mem)
    try:
        pc=address
        for _ in range(5):
            u.emu_start(pc,0x80008004,count=300)
            pc=u.reg_read(m.UC_MIPS_REG_PC)
            if pc==end:break
            assert pc in (SET,ANIM,SCREEN),hex(pc)
            pc=u.reg_read(m.UC_MIPS_REG_RA)
            for n in ('V0','V1','A0','A1','A2','A3','T0','T1','T2','T3','T4','T5','T6','T7','T8','T9'):
                u.reg_write(getattr(m,'UC_MIPS_REG_'+n),0xdead0000)
    except Exception:
        print('TRACE',char,special,partner,flags,[hex(v) for v in trace]); raise
    assert trace[-1]==end,hex(trace[-1])
    for reg,val in values.items():
        if reg.startswith('S') or (reg=='RA' and end==STOP):assert u.reg_read(getattr(m,'UC_MIPS_REG_'+reg))==val,reg
    assert u.mem_read(ENGINE,256)==engine
    result={'obj':bytes(u.mem_read(OBJ,256)),'palette':bytes(u.mem_read(PAL,4096)),'flag':u.mem_read(0x166bb0,1)[0],'calls':calls,'writes':written}
    return result

all_reports=[]
for mode in CHANGES:
    before=(H/mode/'originals/SLUS_005.61').read_bytes(); after, report=proposal(mode)
    normal, black=words(mode)
    def compare(a,b,isblack,row):
        assert a['obj']==b['obj'] and a['calls']==b['calls']
        expected=bytearray(a['palette'])
        if isblack:
            for index in CHANGES[mode]:struct.pack_into('<H',expected,row*32+index*2,black[index])
        assert b['palette']==bytes(expected)
        assert b['flag']==(a['flag']|1 if isblack else a['flag'])
    init_cases=0
    for char in (0,1):
      for special in (0,1,255):
       for partner in (0,1,2,255):
        a=run(before,START,char,special,partner); b=run(after,START,char,special,partner)
        compare(a,b,char==1 and special!=0 and partner==0,35); init_cases+=1
    animation_cases=0
    for partner in (0,1,255):
      for flags in range(256):
        a=run(before,OLD_ANIMATE,1,1,partner,flags); b=run(after,report['animate_address'],1,1,partner,flags)
        compare(a,b,False,35); animation_cases+=1
    dialogue_cases=0
    for char in (0,1):
     for special in (0,1,255):
      for armor in range(16):
       for row in (27,31,35,39,43,47,51,55,59,63,67,71,75,79,83,87,91,95,99,103,107,111,115,119,123,127):
        a=run(before,0x80022954,char,special,armor=armor,row=row,end=0x800229a0)
        b=run(after,0x80022954,char,special,armor=armor,row=row,end=0x800229a0)
        compare(a,b,char==1 and special!=0,row); dialogue_cases+=1
    r={**report,'unicorn_version':uc.__version__,'init_cases':init_cases,'animation_cases':animation_cases,'dialogue_cases':dialogue_cases,'native_object_and_animation_calls_identical':True,'engine_unchanged':True,'only_selected_palette_indices_and_upload_flag_changed':True,'callee_saved_and_stack_restored':True,'passed':True,'actual_gameplay_verified':False}
    (H/mode/'black_proposal/cpu_verification.json').write_text(json.dumps(r,indent=2)+'\n','utf8'); all_reports.append(r)
    print(mode,init_cases,animation_cases,dialogue_cases,'PASS',flush=True)
