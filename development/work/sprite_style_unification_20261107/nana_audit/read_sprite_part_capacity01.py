"""원 US sprite/GPU pool 코드 읽기만. MIPS 실행/게임자원 수정 없음."""
from pathlib import Path
import hashlib,json,sys,struct
N=Path(__file__).resolve().parent;ROOT=N.parents[2];O=N/'sprite_part_capacity_read01';sys.path.insert(0,str(ROOT))
from scripts.c01_audio_build import read_disc
from capstone import Cs,CS_ARCH_MIPS,CS_MODE_MIPS32,CS_MODE_LITTLE_ENDIAN
exe=read_disc(ROOT/'MegaMan X4.bin',('SLUS_005.61',))[0]['SLUS_005.61'];load,size=struct.unpack_from('<II',exe,24);sha=lambda b:hashlib.sha256(b).hexdigest();cs=Cs(CS_ARCH_MIPS,CS_MODE_MIPS32|CS_MODE_LITTLE_ENDIAN)
assert not O.exists();O.mkdir()
regions=[('draw_dispatch',0x80023db8,0x80024000),('sprite_routines',0x80024000,0x8002588c),('armor',0x8002588c,0x80025cdc)]
for name,start,end in regions:
 b=exe[start-load+2048:end-load+2048];(O/f'{name}.txt').write_text('\n'.join(f'{q.address:08x} {q.bytes.hex()} {q.mnemonic:8} {q.op_str}'for q in cs.disasm(b,start))+'\n','utf8')
instructions=list(cs.disasm(exe[2048:2048+size],load));contexts=[]
for i,q in enumerate(instructions):
 if q.mnemonic=='lui' and q.op_str.endswith('0x1f80'):
  tail=instructions[i+1:i+5]
  if any(any(v in z.op_str for v in('0x100(','0x104(','0x124('))for z in tail):
   contexts.append({'address':hex(q.address),'context':[f'{z.address:08x} {z.mnemonic} {z.op_str}'for z in instructions[max(0,i-4):i+12]]})
(O/'pool_pointer_contexts.json').write_text(json.dumps(contexts,indent=2)+'\n','utf8')
(O/'source.json').write_text(json.dumps({'original_exe_sha256':sha(exe),'source':'MegaMan X4.bin','load_address':hex(load),'regions':[{'name':name,'start':hex(start),'end':hex(end),'sha256':sha(exe[start-load+2048:end-load+2048])}for name,start,end in regions],'MIPS_executed':False,'candidate_opened':False,'source_written':False},indent=2)+'\n','utf8')
print(json.dumps({'contexts':len(contexts),'exe_sha256':sha(exe)}))
