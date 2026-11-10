"""HQ-only costume load at actor initialization; native animations are intact."""
import sys,struct,json,hashlib
from pathlib import Path
H=Path(__file__).resolve().parent;ROOT=H.parents[1];sys.path.insert(0,str(ROOT))
from src.psx_korean_font import Assembly,R
from scripts.prepare_riko_ui import entry
from scripts.discover_inputs import psx_arc
R.update({f's{n}':16+n for n in range(3,8)})
HOOK=0x800c9ee8;CODE=64;STACK=0xdc00;SCR=0x100;ATLAS=0x8100;LUT=0xd900
def off(a):return a-0x80010000+2048
def sha(b):return hashlib.sha256(b).hexdigest()

def program(old):
 a=Assembly();i=a.imm;r=a.reg;s=a.shift;b=a.branch
 def call(addr):a.jump(3,addr);a.nop()
 def bal(label):a.branch(1,'zero','s1',label);a.nop()
 def const(reg,value):i(15,reg,'zero',value>>16);i(13,reg,reg,value&65535)
 def addlarge(dst,base,value):i(13,dst,'zero',value);r(0x21,dst,dst,base)
 # Runs uncached in the stage's table padding; return to the unchanged init body.
 i(15,'t0','zero',0x8017);i(36,'t1','t0',0x2203);i(32,'t2','a0',2);a.nop();r(0x25,'t1','t1','t2')
 b(5,'t1','zero','original');a.nop()
 i(9,'sp','sp',-24);i(43,'ra','sp',20);i(43,'a0','sp',16);bal('load')
 i(35,'a0','sp',16);i(35,'ra','sp',20);i(9,'sp','sp',24)
 a.label('original')
 for w in struct.unpack('<7I',old[off(HOOK):off(HOOK)+28]):a.emit(w)
 const('t9',HOOK+28);r(8,'zero','t9','zero');a.nop()
 a.label('load');i(13,'t0','zero',STACK);r(0x23,'sp','sp','t0')
 for n,reg in enumerate(['ra']+[f's{x}'for x in range(8)]):i(43,reg,'sp',16+n*4)
 i(15,'s0','zero',0x1f80);i(35,'s0','s0',0x30);a.nop();i(9,'s0','s0',96)
 i(35,'t0','s0',0);const('t1',0x52415148);b(5,'t0','t1','return');a.nop()
 i(35,'s2','s0',4);i(9,'s1','s0',16)
 # Clear the destination atlas once. Keep all other stage texture pixels untouched.
 addlarge('t0','sp',ATLAS);i(9,'t1','zero',5632);a.label('clear');i(43,'zero','t0',0);i(9,'t0','t0',4);i(9,'t1','t1',-1);b(5,'t1','zero','clear');a.nop()
 a.label('chunk');i(35,'t0','s1',8);i(9,'a1','sp',SCR);r(0x21,'a0','s0','t0');call(0x80016ff4)
 i(35,'t0','s1',0);a.nop();b(4,'t0','zero','state');i(9,'t1','zero',2)
 b(4,'t0','t1','static');a.nop()
 # Dictionary chunk -> selected atlas. Tiles in the dictionary are tile-major.
 i(35,'s3','s1',4);i(35,'s4','s1',12);a.nop();s(2,'s4','s4',7)
 a.move('s5','zero');addlarge('s6','sp',LUT)
 a.label('tile');i(37,'t0','s6',0);a.nop();r(0x23,'t0','t0','s3');r(0x2b,'t1','t0','s4');b(4,'t1','zero','nexttile');a.nop()
 s(0,'t0','t0',7);i(9,'t1','sp',SCR);r(0x21,'t0','t0','t1')
 s(2,'t1','s5',4);s(0,'t1','t1',11);i(12,'t2','s5',15);s(0,'t2','t2',3);r(0x21,'t1','t1','t2');addlarge('t2','sp',ATLAS);r(0x21,'t1','t1','t2')
 i(9,'t2','zero',16);a.label('tilerow');i(35,'t3','t0',0);i(35,'t4','t0',4);i(43,'t3','t1',0);i(43,'t4','t1',4);i(9,'t0','t0',8);i(9,'t1','t1',128);i(9,'t2','t2',-1);b(5,'t2','zero','tilerow');a.nop()
 a.label('nexttile');i(9,'s5','s5',1);i(9,'s6','s6',2);i(11,'t0','s5',176);b(5,'t0','zero','tile');a.nop();b(4,'zero','zero','next');a.nop()
 a.label('state');i(15,'t0','zero',0x8017);i(36,'t1','t0',0x2207);i(36,'t2','t0',0x21f7);i(12,'t1','t1',15)
 b(4,'t2','zero','statechosen');a.nop();r(0x2b,'t1','zero','t1');i(9,'t1','t1',16)
 a.label('statechosen');i(9,'t2','zero',1412);r(0x19,'zero','t1','t2');a.nop();a.nop();r(0x12,'t1','zero','zero');i(9,'t2','sp',SCR);r(0x21,'t1','t1','t2')
 addlarge('t2','sp',LUT);i(9,'t3','zero',88);a.label('copylut');i(35,'t0','t1',0);i(9,'t1','t1',4);i(43,'t0','t2',0);i(9,'t2','t2',4);i(9,'t3','t3',-1);b(5,'t3','zero','copylut');a.nop()
 i(15,'t2','zero',0x1f80);i(35,'t2','t2',0x20);a.nop();i(35,'t0','t2',8);a.nop();r(0x21,'t2','t2','t0');i(9,'t3','zero',265)
 a.label('copybank');i(35,'t0','t1',0);i(9,'t1','t1',4);i(43,'t0','t2',0);i(9,'t2','t2',4);i(9,'t3','t3',-1);b(5,'t3','zero','copybank');a.nop();b(4,'zero','zero','next');a.nop()
 a.label('static');i(35,'a0','s1',4);i(35,'a2','s1',12);i(9,'a1','sp',SCR);s(2,'a2','a2',11);bal('upload')
 a.label('next');i(9,'s1','s1',16);i(9,'s2','s2',-1);b(5,'s2','zero','chunk');a.nop()
 i(9,'a0','zero',768);addlarge('a1','sp',ATLAS);i(9,'a2','zero',11);bal('upload')
 a.label('return')
 for n,reg in enumerate(['ra']+[f's{x}'for x in range(8)]):i(35,reg,'sp',16+n*4)
 i(13,'t0','zero',STACK);r(8,'zero','ra','zero');r(0x21,'sp','sp','t0')
 # Row uploader. DrawSync guarantees that stack-backed rows live through DMA.
 a.label('upload');i(9,'sp','sp',-48)
 for n,reg in enumerate(['ra','s0','s1','s2']):i(43,reg,'sp',32+n*4)
 a.move('s0','a0');a.move('s1','a1');a.move('s2','a2')
 a.move('a0','zero');call(0x800ea20c)
 a.label('uploadrow');i(9,'t0','zero',176);r(0x1b,'zero','s0','t0');a.nop();a.nop();r(0x12,'t1','zero','zero');r(0x10,'t2','zero','zero')
 s(0,'t1','t1',6);i(9,'t1','t1',384);i(41,'t1','sp',16);i(41,'t2','sp',18);i(9,'t0','zero',64);i(41,'t0','sp',20);i(9,'t0','zero',16);i(41,'t0','sp',22)
 i(9,'a0','sp',16);a.move('a1','s1');call(0x800ea4d0);a.move('a0','zero');call(0x800ea20c)
 i(9,'s0','s0',16);i(9,'s1','s1',2048);i(9,'s2','s2',-1);b(5,'s2','zero','uploadrow');a.nop()
 for n,reg in enumerate(['ra','s0','s1','s2']):i(35,reg,'sp',32+n*4)
 r(8,'zero','ra','zero');i(9,'sp','sp',48)
 code=a.finish();assert CODE+len(code)<=2048,len(code)
 return code, {k:CODE+v*4 for k,v in a.labels.items()}

def hook():
 a=Assembly();i=a.imm;r=a.reg
 i(15,'t9','zero',0x8014);i(35,'t9','t9',0x6a8);i(15,'t0','zero',0x2000);i(9,'t9','t9',CODE);r(0x25,'t9','t9','t0');r(8,'zero','t9','zero');a.nop()
 return a.finish()

def rebuild(raw,replacements):
 entries=psx_arc(raw);header=bytearray(raw[:2048]);body=bytearray()
 for n,e in enumerate(entries):
  k=int(e['type'],16);data=replacements.get(k,entry(raw,k));struct.pack_into('<I',header,12+n*8,len(data));body.extend(data);body.extend(bytes((-len(data))%2048))
 result=bytes(header+body);assert len(result)==len(raw),(len(result),len(raw));psx_arc(result);return result

def make(mode):
 d=H/mode;old=(d/'originals/SLUS_005.61').read_bytes();code,labels=program(old);patched=bytearray(old);patched[off(HOOK):off(HOOK)+28]=hook()
 out=d/'prepared';out.mkdir(exist_ok=True);(out/'SLUS_005.61').write_bytes(patched)
 report={'mode':mode,'code_size':len(code),'labels':labels,'source_exe_sha256':sha(old),'exe_sha256':sha(patched),'files':[]}
 for char in 'XZ':
  name=f'ST0D_0{char}.ARC';raw=(d/'originals'/name).read_bytes();table=entry(raw,12).ljust(2048,b'\0');table=bytearray(table);table[CODE:CODE+len(code)]=code;repl={12:bytes(table)}
  if char=='X':
   table[:20]=struct.pack('<5I',0,0,768*128,0,0);repl[12]=bytes(table);repl[0x10102]=(d/'packing/non_x_texture.bin').read_bytes()[:256*128];repl[10]=(d/'packing/parts.bin').read_bytes()
   blob=(d/'compiled/container.bin').read_bytes();repl[13]=(entry(raw,13)+blob).ljust(90112,b'\0')
  result=rebuild(raw,repl);(out/name).write_bytes(result);report['files'].append({'file':name,'size':len(result),'before':sha(raw),'after':sha(result),'changed_entries':list(repl)})
 (out/'program.bin').write_bytes(code);(out/'preparation.json').write_text(json.dumps(report,indent=2));print(mode,len(code),'prepared')
if __name__=='__main__':
 for mode in ['ver_rin_nana','ver_buki_riko']:make(mode)
