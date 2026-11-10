"""Run RXC1's real Vorbis comment parser on original, failed, and fixed tags.

The Vorbis decoder/file I/O is outside this test; libc string conversion and
cleanup functions are stubbed. Native tag parsing and version gate run unchanged.
"""
from pathlib import Path
import argparse,sys,json,struct,hashlib
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32,UC_HOOK_CODE
from unicorn.x86_const import *
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R))
from src.steam_stream import decode_sngw,vorbis_comments
W=R/'work/steam_port_20261109';BASE=0x401000

def main():
 parser=argparse.ArgumentParser(description=__doc__)
 parser.add_argument('--version',choices=['v2','v3'],default='v3')
 version=parser.parse_args().version
 code=(W/'runtime/code/text.bin').read_bytes()
 assert hashlib.sha256(code).hexdigest()=='38ff6b3ca58e7f4119b8ff5082bd0ad68429134eb90ffd3074da77341148e6cc'
 exe=(W/'original/RXC1.exe').read_bytes()
 m=Uc(UC_ARCH_X86,UC_MODE_32);m.mem_map(0x400000,0x1c00000);m.mem_write(BASE,code)
 m.mem_write(0x1a9f2d8,exe[0x1a9f2d8-0x400c00:0x1a9f2d8-0x400c00+0x44])
 m.mem_map(0x3000000,0x20000)
 obj=0x3000000;comments=0x3001000;ptrs=0x3002000;strings=0x3003000;info=0x3005000;sp=0x3010000;stop=0x301f000
 def u32(a):return struct.unpack('<I',m.mem_read(a,4))[0]
 def string(a):return bytes(m.mem_read(a,256)).split(b'\0')[0]
 def ret(value=0):
  stack=m.reg_read(UC_X86_REG_ESP);m.reg_write(UC_X86_REG_EAX,value&0xffffffff)
  m.reg_write(UC_X86_REG_EIP,u32(stack));m.reg_write(UC_X86_REG_ESP,stack+4)
 def hook(machine,a,size,data):
  stack=m.reg_read(UC_X86_REG_ESP)
  if a==0xab1600:
   hay=u32(stack+4);needle=u32(stack+8);index=string(hay).find(string(needle));ret(hay+index if index>=0 else 0)
  elif a==0xab7036:ret(int(string(u32(stack+4))))
  elif a==0xac10ec:ret(int(string(u32(stack+4)),u32(stack+12)))
  elif a in (0x4076c0,0xcce9b0):ret()
 m.hook_add(UC_HOOK_CODE,hook)
 cases=[]
 builds=json.loads((W/f'title_voice_{version}_builds.json').read_text('utf8'))
 for row in builds:
  if not row['relative_path'].endswith('.sngw'):continue
  for label,p,wanted in [('original',W/'original'/row['relative_path'],True),
      ('failed_v1',R/'out/steam_title_voice_20261109_v1'/row['relative_path'],False),('fixed_'+version,R/row['output'],True)]:
   tags=vorbis_comments(decode_sngw(p.read_bytes()))
   m.mem_write(0x3000000,bytes(0x20000))
   # The preceding native instructions initialize both loop endpoints to -1.
   m.mem_write(obj+0x8c,struct.pack('<II',0xffffffff,0xffffffff))
   m.mem_write(comments,struct.pack('<III',ptrs,0,len(tags)))
   for i,t in enumerate(tags):
    m.mem_write(ptrs+i*4,struct.pack('<I',strings+i*256));m.mem_write(strings+i*256,t.encode()+b'\0')
   m.mem_write(info+8,struct.pack('<I',48000));m.mem_write(sp+0x420,struct.pack('<I',stop))
   m.reg_write(UC_X86_REG_ESP,sp);m.reg_write(UC_X86_REG_EDI,obj);m.reg_write(UC_X86_REG_EBP,comments)
   m.reg_write(UC_X86_REG_ESI,info);m.reg_write(UC_X86_REG_EBX,0)
   m.emu_start(0xccf8da,stop,count=10000)
   assert m.reg_read(UC_X86_REG_EIP)==stop
   accepted=bool(m.reg_read(UC_X86_REG_EAX)&255)
   assert accepted==wanted,(label,tags,accepted)
   cases.append({'file':row['relative_path'],'variant':label,'native_parser_accepted':accepted,
    'parsed_version':u32(obj+0xe0),'parsed_loop_start':u32(obj+0x8c),'parsed_loop_end':u32(obj+0x90)})
 report={'passed':True,'native_entry':'0xccf8da','native_version_gate':'0xccfce6',
  'file_io_and_vorbis_decode_tested_here':False,'cases':cases}
 (W/f'title_voice/{version}/native_metadata_verification.json').write_text(json.dumps(report,indent=2)+'\n','utf8')
 print(json.dumps(report))
if __name__=='__main__':main()
