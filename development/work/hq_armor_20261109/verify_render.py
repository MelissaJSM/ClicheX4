"""Execute native HQ sprite renderer and inspect its actual GPU commands."""
import sys,json,struct
from pathlib import Path
import numpy as np
from PIL import Image
import unicorn as uc
from unicorn import mips_const as m
from runtime import H,ROOT,entry,sha
from prepare_art import rgba,originals
from src.psx_ui_atlas import write_tile
STOP,GETTYPE=0x80008000,0x800ea0f4
PRIM,MODE,PARTS,OBJ,LINK=0x180000,0x182000,0x184000,0x186000,0x188000

def render(exe,bank,texture,frame):
 u=uc.Uc(uc.UC_ARCH_MIPS,uc.UC_MODE_MIPS32|uc.UC_MODE_LITTLE_ENDIAN);u.mem_map(0,0x200000);u.mem_map(0x1f800000,4096);u.mem_write(0x10000,exe[2048:]);u.mem_write(GETTYPE&0x1fffffff,bytes(32));u.mem_write(PARTS,bank)
 obj=bytearray(256);obj[0]=0x40;obj[0x14]=255;obj[0x16]=3;obj[0x47]=frame;struct.pack_into('<i',obj,8,80<<16);struct.pack_into('<i',obj,12,80<<16);struct.pack_into('<IHH',obj,0x3c,PARTS|0x80000000,768,0x7883);u.mem_write(OBJ,bytes(obj))
 for a,v in [(0x1f800100,PRIM),(0x1f800104,MODE),(0x13bc4c,LINK)]:u.mem_write(a,struct.pack('<I',v|0x80000000))
 for k,v in {'A0':OBJ|0x80000000,'SP':0x801ff000,'RA':STOP}.items():u.reg_write(getattr(m,'UC_MIPS_REG_'+k),v)
 def stop(u,a,s,d):u.emu_stop()
 for a in [STOP,GETTYPE]:u.hook_add(uc.UC_HOOK_CODE,stop,begin=a,end=a)
 pc=0x80024334
 for _ in range(100):
  u.emu_start(pc,STOP+4,count=50000);pc=u.reg_read(m.UC_MIPS_REG_PC)
  if pc==STOP:break
  assert pc==GETTYPE,hex(pc);pc=u.reg_read(m.UC_MIPS_REG_RA);u.reg_write(m.UC_MIPS_REG_V0,1)
 else:raise AssertionError('Renderer call budget')
 count=struct.unpack('<I',u.mem_read(0x1f800124,4))[0];prims=bytes(u.mem_read(PRIM,count*40));modes=bytes(u.mem_read(MODE,count*8));canvas=np.zeros((160,160),np.uint8)
 for n in range(count):
  q=prims[n*40:n*40+40];assert q[7]==0x7d,q.hex();x,y=struct.unpack_from('<hh',q,8);su,sv=q[12:14];clut=struct.unpack_from('<H',q,14)[0];page=struct.unpack_from('<I',modes,n*8+4)[0]&31
  assert clut==0x7883;physx=(page&15)*64+su//4;physy=(page>>4)*256+sv;logical=((physx-384)//64)*176+(physy//16)*16+(physx%64)//4
  assert 768<=logical<944,(logical,physx,physy)
  from src.psx_ui_atlas import tile_pixels
  tile=np.frombuffer(tile_pixels(texture,logical-768),np.uint8).reshape(16,16);target=canvas[y:y+16,x:x+16];target[tile!=0]=tile[tile!=0]
 assert struct.unpack('<I',u.mem_read(0x1f800100,4))[0]==(PRIM|0x80000000)+count*40
 return canvas,count

def main():
 for mode in ['ver_rin_nana','ver_buki_riko']:
  d=H/mode;exe=(d/'prepared/SLUS_005.61').read_bytes();states=(d/'compiled/states.bin').read_bytes();dictionary=(d/'compiled/dictionary.bin').read_bytes();_,words=originals(mode);out=d/'review';out.mkdir(exist_ok=True);counts=[]
  for state in range(18):
   data=states[state*1412:(state+1)*1412];texture=bytearray(176*128)
   for t,j in enumerate(struct.unpack('<176H',data[:352])):
    if j!=65535:write_tile(texture,t,bytes(v for q in dictionary[j*128:j*128+128]for v in(q&15,q>>4)))
   sd=out/f'{state:02}';sd.mkdir(exist_ok=True)
   for frame in range(12):
    a,count=render(exe,data[352:],texture,frame);expected=np.array(Image.open(d/'art'/f'{state:02}'/f'{frame:02}.png'));assert np.array_equal(a,expected),(mode,state,frame);rgba(a,words).save(sd/f'{frame:02}.png');counts.append(count)
  report={'passed':True,'native_renderer':'0x80024334','frames':216,'GPU_opcodes_coordinates_UV_CLUT_verified':True,'min_parts':min(counts),'max_parts':max(counts),'all_pixels_equal_compiled_art':True,'actual_gameplay_verified':False}
  (d/'prepared/render_verification.json').write_text(json.dumps(report,indent=2));print(mode,'native GPU 216 PASS',flush=True)
if __name__=='__main__':main()
