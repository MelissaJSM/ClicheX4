from pathlib import Path
import sys, struct, re, json
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(R))
from capstone import Cs,CS_ARCH_X86,CS_MODE_32
B=(R/'work/steam_port_20261109/runtime/code/text.bin').read_bytes();BASE=0x401000
md=Cs(CS_ARCH_X86,CS_MODE_32)
def dump(a,n):
 print('\nADDRESS',hex(a))
 for i in md.disasm(B[a-BASE:a-BASE+n],a): print(hex(i.address),i.mnemonic,i.op_str)
if len(sys.argv)>1:
 for a in sys.argv[1:]:
  if ':' in a:
   va,n=a.split(':');dump(int(va,16),int(n,16))
  else:
   target=int(a,16);hits=[]
   for m in re.finditer(b'\xe8',B):
    pos=m.start()
    if pos+5<=len(B) and BASE+pos+5+struct.unpack_from('<i',B,pos+1)[0]==target:hits.append(hex(BASE+pos))
   print(hex(target),'callers',hits)
