"""JP/US static call-site comparison, with concrete IDs and bounded context."""
from pathlib import Path
import sys,json,struct,re,difflib,collections
from capstone import Cs,CS_ARCH_MIPS,CS_MODE_MIPS32,CS_MODE_LITTLE_ENDIAN
H=Path(__file__).resolve().parent
sys.path.insert(0,str(H));from compare_calls import sections
M=Cs(CS_ARCH_MIPS,CS_MODE_MIPS32|CS_MODE_LITTLE_ENDIAN)
TARGETS={'us':{0x8001540c:'play_sound',0x800154e8:'sound_dispatch',0x800157ac:'sound_variant',0x80015930:'stop_sound',0x80015a10:'is_sound_finished',0x8001663c:'play_xa',0x8002217c:'dialogue',0x800921e8:'boss_intro',0x8009227c:'boss_wait'},'jp':{0x80015440:'play_sound',0x8001551c:'sound_dispatch',0x800157e0:'sound_variant',0x80015964:'stop_sound',0x80015a44:'is_sound_finished',0x80016670:'play_xa',0x800221c8:'dialogue',0x80092244:'boss_intro',0x800922c8:'boss_wait'}}
TARGETS['us'].update({0x80013ad8:'load_archive',0x80013890:'load_archive_sync',0x80015a50:'load_sound_bank'})
TARGETS['jp'].update({0x80013b0c:'load_archive',0x800138c4:'load_archive_sync',0x80015a84:'load_sound_bank'})
def norm(i,base):
 # Compare control/command skeleton while flagging literal addresses as relocation.
 s=i.op_str
 if i.mnemonic in ('j','jal'):
  addr=int(s,16);return i.mnemonic+' '+('api:'+TARGETS[base].get(addr,'external'))
 if i.mnemonic.startswith('b') and ',' in s:s=s.rsplit(',',1)[0]+', relative'
 if i.mnemonic=='lui' and re.search(r'0x80[01][0-9a-f]',s):s=s.split(',')[0]+', address_hi'
 return i.mnemonic+' '+s
def args(ins,k):
 out={};orig={}
 for reg in ('$a0','$a1','$a2'):
  found=[]
  for p in list(range(max(0,k-16),k))+[k+1]:
   if p>=len(ins):continue
   i=ins[p];s=i.op_str
   if not s.startswith(reg+','):continue
   if i.mnemonic in ('sw','sh','sb') or i.mnemonic.startswith('b') or i.mnemonic in ('j','jr','jal','jalr'):continue
   found.append((p,i))
  if found:
   p,i=found[-1];orig[reg]=f'{i.address:08x} {i.mnemonic} {i.op_str}'
   v=i.op_str.split(', ')[1:]
   if i.mnemonic=='move' and v==['$zero']:out[reg]=0
   elif i.mnemonic in ('addiu','ori') and v[0]=='$zero':out[reg]=int(v[1],0)&0xffffffff
   else:out[reg]={'dynamic':i.mnemonic+' '+i.op_str}
  else:out[reg]=None
 return out,orig
def main():
 es={r:(H/n).read_bytes() for r,n in [('us','SLUS_005.61'),('jp','SLPS_009.02')]}
 ss={r:sections(r) for r in es};result=[]
 for us in ss['us']:
  if us['kind']!='c':continue
  jp=next(x for x in ss['jp'] if x['name']==us['name'] and x['kind']=='c')
  rows={};instructions={}
  for r,s in [('us',us),('jp',jp)]:
   ins=list(M.disasm(es[r][s['offset']:s['end']],s['offset']+0x8000f800));instructions[r]=ins
   out=[]
   for k,i in enumerate(ins):
    if i.mnemonic!='jal':continue
    target=int(i.op_str,16)
    if target not in TARGETS[r]:continue
    a,orig=args(ins,k)
    out.append({'address':hex(i.address),'api':TARGETS[r][target],'arguments':a,'argument_assignment_evidence':orig,'context':[f'{x.address:08x} {x.mnemonic} {x.op_str}' for x in ins[max(0,k-10):k+2]],'context_scope':'10 preceding instructions plus delay slot; branch conditions retained, no inferred gameplay label'})
   rows[r]=out
  if not rows['us'] and not rows['jp']:continue
  sig=lambda a:[(c['api'],c['arguments']) for c in a]
  same=sig(rows['us'])==sig(rows['jp'])
  # Address-based dynamic values may differ. The common sound IDs are compared independently.
  play=lambda a:[(c['arguments']['$a0'],c['arguments']['$a1'],c['arguments']['$a2']) for c in a if c['api']=='play_sound']
  playsame=play(rows['us'])==play(rows['jp'])
  result.append({'section':us['name'],'us_range':[hex(us['offset']+0x8000f800),hex(us['end']+0x8000f800)],'jp_range':[hex(jp['offset']+0x8000f800),hex(jp['end']+0x8000f800)],'sound_call_ids_and_owner_match':playsame,'all_selected_api_signatures_match':same,'calls':rows,'sound_id_inventory':{r:sorted(set((c['arguments']['$a0'],c['arguments']['$a1']) for c in rows[r] if c['api']=='play_sound' and isinstance(c['arguments']['$a0'],int) and isinstance(c['arguments']['$a1'],int))) for r in rows}})
 (H/'boss_ai_calls.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8')
 print('Sections with sound/load/dialogue calls:',len(result))
 for x in result:
  if x['section'].startswith('shots/') and not x['sound_call_ids_and_owner_match']:print(x['section'],'DIFF')
if __name__=='__main__':main()
