"""Run native MIPS init and decompressor; intercept only GPU/animation APIs."""
import sys,struct,json
from pathlib import Path
import unicorn as uc
from unicorn import mips_const as m
from runtime import H,ROOT,HOOK,STACK,SCR,ATLAS,LUT,entry,psx_arc,sha,off
from src.psx_ui_atlas import tile_pixels
from src.psx_player import decode_stream
SET,SCREEN,LOAD,SYNC,STOP=0x80015d60,0x8002b288,0x800ea4d0,0x800ea20c,0x80008000
OBJ,ENGINE,PAL,BASE=0x180000,0x1721c0,0x150000,0x1b9f28

def run(mode,original=False,char=0,special=0,armor=0,partner=0,decoder_cache=None):
 d=H/mode;folder=d/('originals'if original else'prepared');exe=(folder/'SLUS_005.61').read_bytes();arc=(folder/f'ST0D_0{"X"if char==0 else"Z"}.ARC').read_bytes()
 u=uc.Uc(uc.UC_ARCH_MIPS,uc.UC_MODE_MIPS32|uc.UC_MODE_LITTLE_ENDIAN);u.mem_map(0,0x200000);u.mem_map(0x1f800000,4096);u.mem_write(0x10000,exe[2048:])
 for addr in (SET,SCREEN,LOAD,SYNC):u.mem_write(addr&0x1fffffff,bytes(32))
 if decoder_cache is not None:u.mem_write(0x16ff4,bytes(32))
 ptr=BASE;positions={}
 for e in psx_arc(arc):
  k=int(e['type'],16)
  if k<0x10000:
   b=entry(arc,k);positions[k]=ptr;u.mem_write(ptr,b);ptr+=len(b)
 for a,v in [(0x1406a8,positions[12]),(0x1f800020,positions[10]),(0x1f800030,positions[13]),(0x1f800028,PAL)]:u.mem_write(a,struct.pack('<I',v|0x80000000))
 obj=bytearray([0xa5]*256);obj[2]=partner;obj[4]=0;u.mem_write(OBJ,bytes(obj));engine=bytearray([0x5a]*128);engine[0x43]=char;engine[0x37]=special;engine[0x47]=armor;u.mem_write(ENGINE,bytes(engine));u.mem_write(PAL,entry((d/'originals'/f'COL0D_0{"X"if char==0 else"Z"}.ARC').read_bytes(),5));u.mem_write(0x166bb0,b'\x04')
 regs={'SP':0x801ff000,'RA':STOP,'A0':OBJ|0x80000000,'FP':0x01353780,**{'S'+str(n):0x13576000+n for n in range(8)}}
 for k,v in regs.items():u.reg_write(getattr(m,'UC_MIPS_REG_'+k),v)
 vram=bytearray(1024*512*2);uploads=[];calls=[];trace=[];writes=[];lowsp=0x1ff000;pending=[]
 def upload(tile,data):
  for n in range(len(data)//2048):
   t=tile+n*16;x=384+t//176*64;y=t%176
   for row in range(16):vram[(y+row)*2048+x*2:(y+row)*2048+x*2+128]=data[n*2048+row*128:n*2048+row*128+128]
 upload(0,entry(arc,0x10102))
 def code(u,addr,size,data):
  physical=addr&0x1fffffff
  trace.append(addr)
  if len(trace)>80:del trace[:40]
  if physical in {x&0x1fffffff for x in [SET,SCREEN,LOAD,SYNC,STOP,0x80016ff4]}:u.emu_stop()
 def mem(u,access,addr,size,val,data):
  nonlocal lowsp
  addr&=0x1fffffff
  allowed=[(0x1f1000,0x1ff000),(OBJ,OBJ+256),(PAL,PAL+4096),(0x166bb0,0x166bb1),(positions[10],positions[10]+len(entry(arc,10)))]
  assert any(lo<=addr and addr+size<=hi for lo,hi in allowed),(mode,char,partner,hex(addr),size)
  if addr>=0x1f1000:lowsp=min(lowsp,addr)
 for addr in [SET,SCREEN,LOAD,SYNC,STOP]+([0x80016ff4]if decoder_cache is not None else[]):
  for alias in (addr,addr|0x20000000):u.hook_add(uc.UC_HOOK_CODE,code,begin=alias,end=alias)
 u.hook_add(uc.UC_HOOK_MEM_WRITE,mem)
 pc=HOOK
 try:
  for _ in range(200):
   u.emu_start(pc,STOP+4,count=1000000);pc=u.reg_read(m.UC_MIPS_REG_PC);physical=pc&0x1fffffff
   if physical==(STOP&0x1fffffff):break
   args=[u.reg_read(getattr(m,'UC_MIPS_REG_A'+str(n)))for n in range(4)]
   if physical==0x16ff4:
    source=args[0]&0x1fffffff;offset=source-positions[13]-96;expected=decoder_cache[offset];dest=args[1]&0x1fffffff
    assert dest==(u.reg_read(m.UC_MIPS_REG_SP)&0x1fffffff)+SCR
    u.mem_write(dest,expected)
   elif physical==(LOAD&0x1fffffff):
    x,y,w,h=struct.unpack('<4H',u.mem_read(args[0]&0x1fffffff,8));assert w==64 and h==16 and 0<=y<=160
    pending.append((x,y,w,h,args[1]&0x1fffffff,bytes(u.mem_read(args[1]&0x1fffffff,w*h*2))));uploads.append([x,y,w,h])
   elif physical==(SYNC&0x1fffffff):
    for x,y,w,h,p,expected in pending:
     data=bytes(u.mem_read(p,w*h*2));assert data==expected,'GPU data reused before DrawSync'
     for r in range(h):vram[(y+r)*2048+x*2:(y+r)*2048+(x+w)*2]=data[r*w*2:(r+1)*w*2]
    pending.clear()
   elif physical in (SET&0x1fffffff,SCREEN&0x1fffffff):calls.append([physical|0x80000000,args[0],args[1]if physical==(SET&0x1fffffff)else None])
   else:raise AssertionError(('unexpected stop',hex(pc)))
   pc=u.reg_read(m.UC_MIPS_REG_RA)
   for n in ['V0','V1','A0','A1','A2','A3']+['T'+str(x)for x in range(10)]:u.reg_write(getattr(m,'UC_MIPS_REG_'+n),0xdead0000)
  else:raise AssertionError('Call budget')
 except Exception:
  print('TRACE',[hex(x)for x in trace[-40:]],hex(pc));raise
 assert not pending
 for k,v in regs.items():
  if k!='A0':assert u.reg_read(getattr(m,'UC_MIPS_REG_'+k))==v,k
 assert bytes(u.mem_read(ENGINE,128))==engine
 assert ptr<lowsp-32768,(hex(ptr),hex(lowsp))
 # Native decoded output must equal the compiled selected state and static atlas.
 output={'object':bytes(u.mem_read(OBJ,256)),'palette':bytes(u.mem_read(PAL,4096)),'calls':calls,'uploads':uploads,'ram_end':ptr,'stack_low':lowsp,'positions':positions,'parts':bytes(u.mem_read(positions[10],len(entry(arc,10)))),'vram':vram}
 return output

def main():
 for mode in (sys.argv[1:] or ['ver_rin_nana','ver_buki_riko']):
  d=H/mode;cases=[];basic=run(mode,True);atlas=(d/'packing/non_x_texture.bin').read_bytes();states=(d/'compiled/states.bin').read_bytes();dictionary=(d/'compiled/dictionary.bin').read_bytes()
  # Each exact compressed chunk is executed natively once. Reuse those proven
  # outputs in selection cases; do not spend minutes re-decoding identical data.
  container=(d/'compiled/container.bin').read_bytes();decoder_cache={};exe=(d/'prepared/SLUS_005.61').read_bytes()
  for q in json.loads((d/'compiled/container.json').read_text())['chunks']:
   machine=uc.Uc(uc.UC_ARCH_MIPS,uc.UC_MODE_MIPS32|uc.UC_MODE_LITTLE_ENDIAN);machine.mem_map(0,0x200000);machine.mem_write(0x10000,exe[2048:]);packed=container[q['offset']:];machine.mem_write(0x180000,packed);machine.mem_write(0x190000,bytes([0xa5])*(q['raw']+32))
   machine.reg_write(m.UC_MIPS_REG_A0,0x80180000);machine.reg_write(m.UC_MIPS_REG_A1,0x80190010);machine.reg_write(m.UC_MIPS_REG_RA,STOP);machine.emu_start(0x80016ff4,STOP,count=2000000)
   assert machine.reg_read(m.UC_MIPS_REG_PC)==STOP
   expected=decode_stream(packed,0,len(packed),q['raw']).data;assert bytes(machine.mem_read(0x190010,q['raw']))==expected
   assert bytes(machine.mem_read(0x190000,16))+bytes(machine.mem_read(0x190010+q['raw'],16))==bytes([0xa5])*32
   decoder_cache[q['offset']]=expected
  for special,armor in [(0,n)for n in range(16)]+[(1,0),(1,15),(255,15)]:
   b=run(mode,special=special,armor=armor,decoder_cache=decoder_cache);state=16+(armor!=0)if special else armor;expected=states[state*1412:(state+1)*1412];lut=struct.unpack('<176H',expected[:352]);tiledata=bytearray(176*128)
   from src.psx_ui_atlas import write_tile
   for n,t in enumerate(lut):
    if t!=65535:
     raw=dictionary[t*128:t*128+128];px=bytes(v for q in raw for v in(q&15,q>>4));write_tile(tiledata,n,px)
   full=atlas+tiledata
   for t in range(944):
    x=384+t//176*64+t%16*4;y=(t%176)//16*16
    raw=b''.join(b['vram'][(y+r)*2048+x*2:(y+r)*2048+x*2+8]for r in range(16));px=bytes(v for q in raw for v in(q&15,q>>4));assert px==tile_pixels(full,t),(mode,state,t)
   p=b['parts'];offset=struct.unpack_from('<I',p,8)[0];assert p[offset:offset+1060]==expected[352:]
   assert b['calls']==basic['calls']
   obj=bytearray(b['object']);struct.pack_into('<I',obj,0x3c,struct.unpack_from('<I',basic['object'],0x3c)[0]);struct.pack_into('<H',obj,0x40,struct.unpack_from('<H',basic['object'],0x40)[0]);assert obj==basic['object']
   assert b['palette']==basic['palette'];cases.append({'special':special,'armor':armor,'state':state,'uploads':len(b['uploads']),'ram_end':hex(b['ram_end']),'stack_low':hex(b['stack_low'])})
  protected=0
  for char in (0,1):
   for special in (0,1,255):
    for partner in ((1,255)if char==0 else(0,1,255)):
     a=run(mode,True,char,special,partner=partner);b=run(mode,False,char,special,partner=partner)
     assert not b['uploads'] and a['calls']==b['calls'] and a['palette']==b['palette']
     ob=bytearray(b['object']);ob[0x3c:0x42]=a['object'][0x3c:0x42];assert ob==a['object'];protected+=1
  report={'mode':mode,'passed':True,'unicorn':uc.__version__,'cases':cases,'protected_actor_cases':protected,'all_944_texture_tiles_exact_each_state':True,'all_12_selected_frames_exact':True,'native_decompressor_chunks_executed':len(decoder_cache),'selection_tests_reuse_exact_verified_native_decoder_outputs':True,'stack_and_callee_saved_restored':True,'engine_unchanged':True,'GPU_DMA_lifetime_checked':True,'exe_sha256':sha((d/'prepared/SLUS_005.61').read_bytes()),'actual_gameplay_verified':False}
  report['archive_sha256']={n:sha((d/'prepared'/n).read_bytes())for n in ['ST0D_0X.ARC','ST0D_0Z.ARC']};report['container_sha256']=sha(container)
  (d/'prepared/cpu_verification.json').write_text(json.dumps(report,indent=2));print(mode,'PASS',len(cases),protected,flush=True)
if __name__=='__main__':main()
