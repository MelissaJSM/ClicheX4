"""Execute the proposed MIPS routine against mocked PS1 GPU SDK calls.

Requires the isolated work/tools/korean_env Python (Unicorn 2.1.4).
This validates emitted CPU code, not an actual PlayStation GPU.
"""
import random
import struct
import unittest
try:
    from unicorn import Uc, UC_ARCH_MIPS, UC_MODE_MIPS32, UC_MODE_LITTLE_ENDIAN, UC_HOOK_CODE
    from unicorn import mips_const as m
except ImportError:
    raise unittest.SkipTest('Use work/tools/korean_env for the actual MIPS CPU tests')
from src.psx_korean_font import emit_cache_code, emit_hook

def run_glyph(glyph, count, pixels, through_hook=False):
    u=Uc(UC_ARCH_MIPS,UC_MODE_MIPS32|UC_MODE_LITTLE_ENDIAN)
    # Unicorn MIPS maps KSEG0/KSEG1 aliases to these physical pages.
    u.mem_map(0,0x200000);u.mem_map(0x1f800000,0x1000)
    class PhysicalMemory:
        def write(self,address,data):u.mem_write(address&0x1fffffff,data)
        def read(self,address,size):return u.mem_read(address&0x1fffffff,size)
    memory=PhysicalMemory()
    base=0x80180000;obj=0x80170000;code=base+512;stop=0x80008000
    memory.write(0x1f800048,struct.pack('<I',base))
    memory.write(base+128,b'KOR1'+struct.pack('<III',1024,1,512))
    bits=sum(bool(v)<<i for i,v in enumerate(pixels))
    memory.write(base+1024,bits.to_bytes(18,'little'))
    memory.write(code,emit_cache_code())
    memory.write(obj+4,struct.pack('<HH',glyph,0xff88))
    memory.write(0x801397e0,struct.pack('<H',count))
    record=0x801396cc+count*4;memory.write(record,b'\xAB\xCD\x56\x78')
    saved={m.UC_MIPS_REG_S0:obj if through_hook else 0x51234,m.UC_MIPS_REG_S1:0x61234,m.UC_MIPS_REG_S2:0x71234,m.UC_MIPS_REG_SP:0x801ff000,m.UC_MIPS_REG_RA:stop}
    for reg,value in saved.items():u.reg_write(reg,value)
    u.reg_write(m.UC_MIPS_REG_A0,obj);u.reg_write(m.UC_MIPS_REG_A1,record)
    u.reg_write(m.UC_MIPS_REG_V0,count*4)
    calls=[]
    # SDK functions are replaced by jr ra; their inputs are captured first.
    for address in (0x800ea20c,0x800ea4d0):memory.write(address,struct.pack('<II',0x03e00008,0))
    def observe(cpu,address,size,data):
        if address==end:
            cpu.emu_stop();return
        physical=address&0x1fffffff
        if physical==0xea4d0:
            rect=struct.unpack('<4H',memory.read(cpu.reg_read(m.UC_MIPS_REG_A0),8))
            tile=bytes(memory.read(cpu.reg_read(m.UC_MIPS_REG_A1),128))
            calls.append(('upload',rect,tile))
        elif physical==0xea20c:calls.append(('sync',cpu.reg_read(m.UC_MIPS_REG_A0)))
    u.hook_add(UC_HOOK_CODE,observe)
    if through_hook:
        start=0x800233c8;end=start+len(emit_hook());memory.write(start,emit_hook())
    else:start=code|0x20000000;end=stop
    u.emu_start(start,0,count=20000)
    if u.reg_read(m.UC_MIPS_REG_PC)!=end:raise AssertionError(f'CPU did not return: PC={u.reg_read(m.UC_MIPS_REG_PC):x}, expected={end:x}, RA={u.reg_read(m.UC_MIPS_REG_RA):x}, calls={len(calls)}')
    for reg,value in saved.items():
        if through_hook and reg==m.UC_MIPS_REG_RA:continue
        if u.reg_read(reg)!=value:raise AssertionError(f'Register {reg} not preserved')
    return calls,bytes(memory.read(record,4)),u.reg_read(m.UC_MIPS_REG_V0),u.reg_read(m.UC_MIPS_REG_V1)

class KoreanFontCpuTests(unittest.TestCase):
    def test_hangul_all_cache_edges_and_source_bits(self):
        rng=random.Random(824)
        for count in (0,1,15,16,31,32,47,48,59):
            pixels=[rng.randrange(2) for _ in range(144)]
            for hook in (False,True):
                calls,record,v0,v1=run_glyph(0x1900,count,pixels,hook)
                self.assertEqual([c[0] for c in calls],['sync','upload','sync'])
                tile=192+count
                self.assertEqual(calls[1][1],(960+(tile%16)*4,256+(tile//16)*16,4,16))
                expected=bytearray(128)
                for index,bit in enumerate(pixels):
                    y,x=divmod(index,12);expected[(y+2)*8+x//2]|=(14*bit)<<((x%2)*4)
                self.assertEqual(calls[1][2],expected)
                self.assertEqual(record,bytes([0,tile,0x56,0x78]))
                self.assertEqual((v0,v1),(count*4,0xff88))
    def test_ascii_and_invalid_never_upload(self):
        for glyph,count,expected in ((64,0,64),(0x1888,59,0x88),(257,0,0x88),(256,60,0x88)):
            calls,record,_,_=run_glyph(glyph,count,[1]*144,True)
            self.assertFalse(calls);self.assertEqual(record[:2],bytes([0,expected]))

if __name__=='__main__':unittest.main()
