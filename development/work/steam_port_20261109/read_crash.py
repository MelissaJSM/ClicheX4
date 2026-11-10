import json
from pathlib import Path
import struct
from capstone import Cs,CS_ARCH_X86,CS_MODE_32

WORK=Path(__file__).resolve().parent
path=Path.home()/'AppData/Local/CrashDumps/RXC1.exe.51352.dmp'
raw=path.read_bytes()
if raw[:4]!=b'MDMP':raise ValueError('Expected minidump')
n,directory=struct.unpack_from('<II',raw,8)
streams={}
for i in range(n):
    kind,size,rva=struct.unpack_from('<III',raw,directory+i*12)
    streams[kind]=(rva,size)
regions=[]
if 5 in streams:
    rva,size=streams[5];count=struct.unpack_from('<I',raw,rva)[0]
    for i in range(count):
        start,length,data_rva=struct.unpack_from('<QII',raw,rva+4+i*16)
        regions.append((start,start+length,data_rva))
if 9 in streams:
    rva,size=streams[9];count,loc=struct.unpack_from('<QQ',raw,rva)
    for i in range(count):
        start,length=struct.unpack_from('<QQ',raw,rva+16+i*16)
        regions.append((start,start+length,loc));loc+=length
def memory(address,length):
    for start,end,rva in regions:
        if start<=address and address+length<=end:return raw[rva+address-start:rva+address-start+length]
    raise ValueError(f'No dump region: {address:08x}/{length}')
rva,size=streams[6]
thread=struct.unpack_from('<I',raw,rva)[0]
code=struct.unpack_from('<I',raw,rva+8)[0]
address=struct.unpack_from('<Q',raw,rva+24)[0]
parameters=struct.unpack_from('<15Q',raw,rva+40)
context_size,context_rva=struct.unpack_from('<II',raw,rva+160)
registers={name:struct.unpack_from('<I',raw,context_rva+off)[0] for name,off in
           [('edi',156),('esi',160),('ebx',164),('edx',168),('ecx',172),('eax',176),('ebp',180),('eip',184),('esp',196)]}
report={'path':str(path),'stream_types':list(streams),'thread':thread,'exception_code':hex(code),
        'address':hex(address),'parameters':[hex(v) for v in parameters[:2]],
        'registers':{k:hex(v) for k,v in registers.items()},'memory_regions':len(regions)}
md=Cs(CS_ARCH_X86,CS_MODE_32)
try:
    machine=memory(address-48,160)
    report['disassembly']='\n'.join(f'{i.address:08x}: {i.mnemonic} {i.op_str}' for i in md.disasm(machine,address-48))
except ValueError as e:report['code_error']=str(e)
try:report['stack']=[hex(v) for v in struct.unpack('<64I',memory(registers['esp'],256))]
except ValueError as e:report['stack_error']=str(e)
(WORK/'runtime/crash_v1_parsed.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
