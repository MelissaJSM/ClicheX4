"""실제 미국판 문자/반복 배경 CPU 경로를 실행한다. GPU SDK만 모의 처리."""
import argparse,json,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from unicorn import Uc,UC_ARCH_MIPS,UC_MODE_MIPS32,UC_MODE_LITTLE_ENDIAN,UC_HOOK_CODE
from unicorn import mips_const as m
from scripts.verify_korean_typewriter_cpu import run_emitter
from scripts.discover_inputs import sha256

def verify(candidate):
    cases=[]
    for name,msg in [('PL00_U.ARC',30),('PL01_U.ARC',25),('PL00_U.ARC',25)]:
        for body in (False,True):
            r=run_emitter(candidate,name,msg,body);expected=1 if body else r['header_word_count']+(not r['original_header_ends_with_yield'])
            if r['words_consumed']!=expected or r['native_state']!=2 or r['countdown']!=4:raise ValueError('Typewriter native control mismatch')
            cases.append(r)
    exe=(candidate/'SLUS_005.61').read_bytes();draws=[]
    for index in (0,1):
        u=Uc(UC_ARCH_MIPS,UC_MODE_MIPS32|UC_MODE_LITTLE_ENDIAN);u.mem_map(0,0x200000);u.mem_map(0x1f800000,0x1000)
        load=struct.unpack_from('<I',exe,0x18)[0]&0x1fffffff;u.mem_write(load,exe[2048:]);u.mem_write(0x1f800000,struct.pack('<I',index))
        u.mem_write(0x142f80,struct.pack('<I',0x80180000))
        for address in (0xe9460,0xeb118):u.mem_write(address,struct.pack('<III',0x24021f00,0x03e00008,0))
        stop=0x80008000;u.reg_write(m.UC_MIPS_REG_SP,0x801ff000);u.reg_write(m.UC_MIPS_REG_RA,stop)
        def watch(cpu,addr,size,data):
            if addr==stop:cpu.emu_stop()
        u.hook_add(UC_HOOK_CODE,watch);u.emu_start(0x80016124,0,count=100000)
        if u.reg_read(m.UC_MIPS_REG_PC)!=stop:raise ValueError('Native background did not return')
        for i in range(17):
            b=bytes(u.mem_read(0x139268+index*340+i*20,20));x,y=struct.unpack_from('<hh',b,8);uv=list(b[12:14]);w,h=struct.unpack_from('<HH',b,16)
            if (*uv,w,h) not in ((0,208,112,48),(112,208,96,48),(0,208,16,48)):raise ValueError('Unexpected background UV')
            draws.append({'buffer':index,'index':i,'xy':[x,y],'uv':uv,'size':[w,h]})
    r={'kind':'native_cpu_not_gpu_runtime','typewriter_cases':cases,'background_draws':draws,'background_texture_bounds':[0,208,208,256],
       'exe_sha256':sha256(exe),'background_function_sha256':sha256(exe[0x6124+2048:0x6334+2048]),'game_process_modified':False}
    (candidate/'native_cpu_verification.json').write_text(json.dumps(r,indent=2)+'\n','utf8');print(json.dumps({'typewriter_cases':len(cases),'background_draws':len(draws)}))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--candidate',type=Path,required=True);verify(p.parse_args().candidate)
