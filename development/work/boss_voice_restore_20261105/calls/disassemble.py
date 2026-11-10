from pathlib import Path
import sys,json,struct
from capstone import Cs,CS_ARCH_MIPS,CS_MODE_MIPS32,CS_MODE_LITTLE_ENDIAN
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE));from compare_calls import sections
md=Cs(CS_ARCH_MIPS,CS_MODE_MIPS32|CS_MODE_LITTLE_ENDIAN)
def main():
 es={r:(HERE/n).read_bytes() for r,n in [('us','SLUS_005.61'),('jp','SLPS_009.02')]}
 for r,e in es.items():
  lines=[]
  for s in sections(r):
   if s['kind']=='c' and (s['name'].startswith('mains/') or s['name'] in ('128C4','55C4','enemy_reaction','1E1BC','archive')):
    lines.append('\nSECTION '+s['name'])
    for i in md.disasm(e[s['offset']:s['end']],s['offset']+0x8000f800):lines.append(f'{i.address:08x} {i.bytes.hex()} {i.mnemonic} {i.op_str}')
  (HERE/(r+'_native.txt')).write_text('\n'.join(lines),encoding='utf8')
 summary=json.loads((HERE/'calls_initial.json').read_text())
 out=[]
 for s in summary:
  if int(s['name'].split('main_')[1][:2])<43:continue
  out.append('\n'+s['name'])
  for r in es:
   out.append(r.upper())
   for c in s[r+'_calls']:
    out.append(c['api'])
    off=c['offset']
    for i in md.disasm(es[r][off-28:off+8],off-28+0x8000f800):out.append(f'{i.address:08x} {i.mnemonic} {i.op_str}')
 (HERE/'boss_call_context.txt').write_text('\n'.join(out),encoding='utf8')
 print('disassembled')
if __name__=='__main__':main()
