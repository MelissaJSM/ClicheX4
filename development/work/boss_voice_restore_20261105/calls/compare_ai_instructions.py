from pathlib import Path
import sys,struct,json,collections
H=Path(__file__).resolve().parent
sys.path.insert(0,str(H));from compare_calls import sections
from compare_boss_ai import M
def signed(x):return x-65536 if x&32768 else x
def main():
 e={r:(H/n).read_bytes() for r,n in [('us','SLUS_005.61'),('jp','SLPS_009.02')]};sec={r:sections(r) for r in e};out=[]
 for a in sec['us']:
  if a['kind']!='c' or not a['name'].startswith('mains/'):continue
  b=next(s for s in sec['jp'] if s['name']==a['name'] and s['kind']=='c')
  au=e['us'][a['offset']:a['end']];bj=e['jp'][b['offset']:b['end']]
  if len(au)!=len(bj):out.append({'section':a['name'],'same_size':False,'us_bytes':len(au),'jp_bytes':len(bj)});continue
  reg_u={};reg_j={};diff=[];relocations=[]
  for i in range(0,len(au),4):
   u,j=struct.unpack_from('<I',au,i)[0],struct.unpack_from('<I',bj,i)[0]
   op=u>>26;rs=(u>>21)&31;rt=(u>>16)&31
   if u!=j:
    reason=None
    if u>>26==j>>26 and op in (2,3):reason='jump_address'
    elif (u&0xffff0000)==(j&0xffff0000) and rs in reg_u and rs in reg_j and op in (9,13,32,33,35,36,37,40,41,43):
     ua=(reg_u[rs]+(u&65535 if op==13 else signed(u&65535)))&0xffffffff
     ja=(reg_j[rs]+(j&65535 if op==13 else signed(j&65535)))&0xffffffff
     if 0x80010000<=ua<0x80200000 and 0x80010000<=ja<0x80200000:reason='absolute_address_operand'
    elif op==15 and j>>26==15 and u>>16==j>>16 and 0x8000<=u&65535<=0x8020 and 0x8000<=j&65535<=0x8020:reason='absolute_address_high'
    record={'us':hex(a['offset']+i+0x8000f800),'jp':hex(b['offset']+i+0x8000f800),'us_word':hex(u),'jp_word':hex(j)}
    if reason:relocations.append(dict(reason=reason,**record))
    else:
     record['us_asm']=[x.mnemonic+' '+x.op_str for x in M.disasm(au[i:i+4],a['offset']+i+0x8000f800)][0]
     record['jp_asm']=[x.mnemonic+' '+x.op_str for x in M.disasm(bj[i:i+4],b['offset']+i+0x8000f800)][0]
     diff.append(record)
   for w,regs in ((u,reg_u),(j,reg_j)):
    o=w>>26;r=(w>>21)&31;t=(w>>16)&31
    if o==15:regs[t]=(w&65535)<<16
    elif o in (9,13):
     if r in regs:regs[t]=(regs[r]+(w&65535 if o==13 else signed(w&65535)))&0xffffffff
     else:regs.pop(t,None)
    elif o in (32,33,35,36,37):regs.pop(t,None)
    elif o==0:
     rd=(w>>11)&31;fn=w&63
     if fn==0x21 and (r in regs or t in regs):regs[rd]=regs[r] if r in regs else regs[t]
     else:regs.pop(rd,None)
   # Cross-block static address propagation is only a conservative relocation classification.
  out.append({'section':a['name'],'same_size':True,'instruction_count':len(au)//4,'unexplained_differences':diff,'address_relocations':relocations})
 (H/'ai_instruction_diff.json').write_text(json.dumps(out,indent=2),encoding='utf8')
 for s in out:
  if not s['same_size'] or s.get('unexplained_differences'):print(s['section'],s.get('us_bytes'),s.get('jp_bytes'),len(s.get('unexplained_differences',[])),s.get('unexplained_differences',[])[:5])
if __name__=='__main__':main()
