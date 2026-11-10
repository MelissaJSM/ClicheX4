"""Execute the actual US text emitter in Unicorn, with GPU/audio calls mocked.

No game process or files are modified. This tests native control flow and its
unchanged Korean hook; it is not a PlayStation GPU or emulator runtime test.
"""
import argparse
import json
import struct
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from unicorn import Uc,UC_ARCH_MIPS,UC_MODE_MIPS32,UC_MODE_LITTLE_ENDIAN,UC_HOOK_CODE
from unicorn import mips_const as m
from scripts.prepare_riko_ui import entry


def first_page_offsets(text,message,page=0):
    start=struct.unpack_from('<H',text,message*2)[0]
    for _ in range(page):
        while not struct.unpack_from('<H',text,start)[0]&0xa000:
            start+=2
        start+=2
    pos=start
    while not struct.unpack_from('<H',text,pos)[0]&0x4000:
        pos+=2
    return start,pos+2


def run_emitter(candidate,archive,message,body_only,page=0):
    exe=(candidate/'SLUS_005.61').read_bytes()
    text=entry((candidate/archive).read_bytes(),0x15)
    page_start,body_start=first_page_offsets(text,message,page)
    offset=body_start if body_only else page_start
    u=Uc(UC_ARCH_MIPS,UC_MODE_MIPS32|UC_MODE_LITTLE_ENDIAN)
    u.mem_map(0,0x200000);u.mem_map(0x1f800000,0x1000)
    load=struct.unpack_from('<I',exe,0x18)[0]&0x1fffffff
    u.mem_write(load,exe[2048:])
    base=0x180000;obj=0x170000;stop=0x80008000
    u.mem_write(base,text)
    u.mem_write(0x1f800048,struct.pack('<I',base|0x80000000))
    u.mem_write(obj,struct.pack('<IHHHhBBBB',(base+offset)|0x80000000,0,0xff88,29,0,0,1,0,2))
    # A pre-existing glyph object avoids unrelated object allocation. The
    # emitted word count is measured from the actual native text pointer.
    u.mem_write(0x1397e0,struct.pack('<H',1))
    u.mem_write(0x1396c8,struct.pack('<HH',1,1))
    for address in (0xea20c,0xea4d0,0x1540c):
        u.mem_write(address,struct.pack('<II',0x03e00008,0))
    u.mem_write(0x2ae50,struct.pack('<III',0x24020000,0x03e00008,0))
    preserved={m.UC_MIPS_REG_S0:0x13579,m.UC_MIPS_REG_S1:0x24680,
               m.UC_MIPS_REG_S2:0x35813,m.UC_MIPS_REG_SP:0x801ff000,
               m.UC_MIPS_REG_RA:stop}
    for reg,value in preserved.items():u.reg_write(reg,value)
    u.reg_write(m.UC_MIPS_REG_A0,obj|0x80000000)
    uploads=[]
    def observe(cpu,address,size,data):
        if address==stop:cpu.emu_stop()
        elif address&0x1fffffff==0xea4d0:
            uploads.append(cpu.reg_read(m.UC_MIPS_REG_A0))
    u.hook_add(UC_HOOK_CODE,observe)
    u.emu_start(0x8002328c,0,count=500000)
    if u.reg_read(m.UC_MIPS_REG_PC)!=stop:raise ValueError('Native emitter did not return')
    if any(u.reg_read(reg)!=value for reg,value in preserved.items()):raise ValueError('Native emitter corrupted caller registers')
    state=bytes(u.mem_read(obj,16))
    final_pointer=struct.unpack_from('<I',state)[0]&0x1fffffff
    words=(final_pointer-base-offset)//2
    glyphs=struct.unpack('<H',u.mem_read(0x1397e0,2))[0]-1
    return {'archive':archive,'message':message,'page':page,'start':'body' if body_only else 'header',
            'input_word_offset':offset,'words_consumed':words,'glyphs_added':glyphs,
            'native_state':state[13],'countdown':struct.unpack_from('<h',state,10)[0],
            'glyph_uploads':len(uploads),'caller_registers_preserved':True,
            'header_word_count':(body_start-page_start)//2,
            'original_header_ends_with_yield':bool(struct.unpack_from('<H',text,body_start-2)[0]&0x1000)}


def verify(candidate,previous):
    cases=[]
    for archive,message in (('PL00_U.ARC',30),('PL01_U.ARC',25),('PL00_U.ARC',25)):
        for body_only in (False,True):
            after=run_emitter(candidate,archive,message,body_only)
            before=run_emitter(previous,archive,message,body_only)
            expected=1 if body_only else after['header_word_count']+(not after['original_header_ends_with_yield'])
            if after['words_consumed']!=expected or after['native_state']!=2 or after['countdown']!=4:
                raise ValueError(f'Native typewriter yield failed: {after}')
            if before['native_state']!=3 or before['words_consumed']<=after['words_consumed']:
                raise ValueError('Previous instant-page regression was not reproduced')
            cases.append({'before':before,'after':after,'expected_words_consumed':expected,'verified':True})
    return {'kind':'native_us_typewriter_cpu_verification','candidate':str(candidate),'previous':str(previous),
            'native_function':'0x8002328c','cases':cases,'all_cases_verified':True,
            'sdk_gpu_audio_allocation_calls_mocked':True,'game_runtime_verified':False,
            'scope':'Actual candidate EXE plus unchanged embedded Korean helper, native AbcObj state/pointer and glyph count. GPU/audio and allocation calls are mocked; no elapsed PS1 frame timing claim.',
            'emulator_accessed':False,'process_memory_written':False,'keys_sent':False}


if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--candidate',type=Path,required=True)
    p.add_argument('--previous',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();result=verify(a.candidate,a.previous)
    with a.output.open('x',encoding='utf-8') as stream:json.dump(result,stream,ensure_ascii=False,indent=2)
    print(json.dumps(result,ensure_ascii=False))
