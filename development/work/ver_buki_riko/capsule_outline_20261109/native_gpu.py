"""Execute US sprite drawing and raster its SPRT_16 commands against an isolated VRAM."""
import sys,json,struct,hashlib
from pathlib import Path
import numpy as np
import unicorn as uc
from unicorn import mips_const as m
ROOT=Path(__file__).resolve().parents[3];D=Path(__file__).resolve().parent;sys.path.insert(0,str(ROOT))
from scripts.prepare_riko_ui import entry
from src.psx_player import graphics_bank,decode_stream,composition_frame,bank_offsets,indexed_atlas
from src.psx_sprite_batch import canvas_from_parts
from src.psx_ui_atlas import local_composition
STOP,GETTYPE=0x80008000,0x800ea0f4
PRIM,MODE,PARTS,OBJ,LINK=0x180000,0x182000,0x184000,0x186000,0x188000
def render(exe,c,frame,face,texture):
 u=uc.Uc(uc.UC_ARCH_MIPS,uc.UC_MODE_MIPS32|uc.UC_MODE_LITTLE_ENDIAN);u.mem_map(0,0x200000);u.mem_map(0x1f800000,4096)
 u.mem_write(0x10000,exe[2048:]);u.mem_write(GETTYPE&0x1fffffff,bytes(32));u.mem_write(PARTS,c)
 obj=bytearray(256);obj[0]=1;obj[3]=1;obj[0x14]=255;obj[0x15]=face;obj[0x47]=frame
 struct.pack_into('<ii',obj,8,80<<16,80<<16);struct.pack_into('<IHH',obj,0x3c,PARTS|0x80000000,0x520,0x7848);u.mem_write(OBJ,bytes(obj))
 for a,v in [(0x1f800100,PRIM),(0x1f800104,MODE),(0x13bc40,LINK),(0x13bc44,LINK),(0x13bc48,LINK),(0x13bc4c,LINK)]:u.mem_write(a,struct.pack('<I',v|0x80000000))
 for k,v in {'A0':OBJ|0x80000000,'SP':0x801ff000,'RA':STOP}.items():u.reg_write(getattr(m,'UC_MIPS_REG_'+k),v)
 def stop(u,a,s,d):u.emu_stop()
 for a in [STOP,GETTYPE]:u.hook_add(uc.UC_HOOK_CODE,stop,begin=a,end=a)
 pc=0x80024334
 for _ in range(100):
  u.emu_start(pc,STOP+4,count=50000);pc=u.reg_read(m.UC_MIPS_REG_PC)
  if pc==STOP:break
  assert pc==GETTYPE,hex(pc);pc=u.reg_read(m.UC_MIPS_REG_RA);u.reg_write(m.UC_MIPS_REG_V0,1)
 else:raise AssertionError('Renderer call budget')
 count=struct.unpack('<I',u.mem_read(0x1f800124,4))[0];prims=bytes(u.mem_read(PRIM,count*40));modes=bytes(u.mem_read(MODE,count*8))
 # The decompressor uploads 64 words by 48 rows at native (320,32).
 vram=np.zeros((512,2048),np.uint8);atlas=np.frombuffer(indexed_atlas(texture,len(texture)//128)[0],np.uint8).reshape(-1,256)
 vram[32:32+len(atlas),320*4:320*4+256]=atlas
 canvas=np.zeros((160,160),np.uint8);records=[]
 for n in range(count):
  q=prims[n*40:n*40+40];mode=struct.unpack_from('<I',modes,n*8+4)[0]
  x,y=struct.unpack_from('<hh',q,8);su,sv=q[12:14];clut=struct.unpack_from('<H',q,14)[0];page=mode&31
  quad=q[7]&0xfc==0x2c
  assert quad or q[7]&0xfc==0x7c,(q.hex(),hex(mode))
  if quad:
   page=struct.unpack_from('<H',q,22)[0]&31;du=int(q[20])-su;dv=int(q[29])-sv
   width=struct.unpack_from('<h',q,16)[0]-x;height=struct.unpack_from('<h',q,26)[0]-y
   assert abs(du)==width and abs(dv)==height,(du,dv,width,height,q.hex())
  else:du=-16 if mode&0x1000 else 16;dv=-16 if mode&0x2000 else 16;width=height=16
  records.append({'x':x,'y':y,'u':su,'v':sv,'page':page,'mode':hex(mode),'clut':clut,'quad':quad,'du':du,'dv':dv})
  for dy in range(height):
   for dx in range(width):
    px=(page&15)*256+((su+dx*(1 if du>0 else -1))&255);py=(page>>4)*256+((sv+dy*(1 if dv>0 else -1))&255)
    value=vram[py,px]
    if value and 0<=x+dx<160 and 0<=y+dy<160:canvas[y+dy,x+dx]=value
 return canvas,records
def main():
 directory=sys.argv[1]if len(sys.argv)>1 else 'before';assert directory in ['before','prepared']
 exe=(D/'before/SLUS_005.61').read_bytes();reports=[];decoded=0;hashes={}
 for name in ['PL00_U.ARC','PL02_U.ARC']:
  b=(D/directory/name).read_bytes();hashes[name]=hashlib.sha256(b).hexdigest();g,c=entry(b,2),entry(b,3);offsets=bank_offsets(c,allow_aliases=True)
  for gb in range(10,14):
   bank=graphics_bank(g,gb,allow_bank_aliases=True);cb=gb+8;compbank=c[offsets[cb]:offsets[cb+1] if cb+1<len(offsets) else len(c)]
   f=bank['frames'][0];assert len({f['offset']for f in bank['frames']})==1
   expected=decode_stream(g,f['offset'],f['limit'],f['tile_count']*128).data
   machine=uc.Uc(uc.UC_ARCH_MIPS,uc.UC_MODE_MIPS32|uc.UC_MODE_LITTLE_ENDIAN);machine.mem_map(0,0x200000);machine.mem_write(0x10000,exe[2048:])
   machine.mem_write(0x180000,g[f['offset']:f['limit']]);machine.mem_write(0x190000,bytes([0xa5])*(len(expected)+32))
   for reg,value in [(m.UC_MIPS_REG_A0,0x80180000),(m.UC_MIPS_REG_A1,0x80190010),(m.UC_MIPS_REG_RA,STOP)]:machine.reg_write(reg,value)
   machine.emu_start(0x80016ff4,STOP,count=2000000);assert machine.reg_read(m.UC_MIPS_REG_PC)==STOP
   assert bytes(machine.mem_read(0x190010,len(expected)))==expected
   assert bytes(machine.mem_read(0x190000,16))+bytes(machine.mem_read(0x190010+len(expected),16))==bytes([0xa5])*32;decoded+=1
   for n,f in enumerate(bank['frames']):
    raw=decode_stream(g,f['offset'],f['limit'],f['tile_count']*128).data
    expected=canvas_from_parts(raw,f['tile_count'],local_composition(composition_frame(c,cb,n)))
    for face in [0,64]:
     actual,records=render(exe,compbank,n,face,raw);target=expected if face==0 else expected[:,::-1]
     diff=int(np.count_nonzero(actual!=target));reports.append({'file':name,'bank':gb,'frame':n,'facing':face,'pixels_differ':diff,'packets':records})
 out={'cases':reports,'archive_sha256':hashes,'all_match':all(q['pixels_differ']==0 for q in reports),'native_decoder_banks_exact_and_guarded':decoded,'actual_emulator':False};(D/f'native_gpu_{directory}.json').write_text(json.dumps(out,indent=2),'utf8')
 assert out['all_match'],'native GPU rendering differs'
 print(json.dumps({'cases':len(reports),'mismatched':[dict((k,v)for k,v in q.items()if k!='packets')for q in reports if q['pixels_differ']][:10]}))
if __name__=='__main__':main()
