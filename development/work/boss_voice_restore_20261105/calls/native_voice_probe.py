"""Execute JP/US boss-intro functions in isolated MIPS RAM, never an emulator process."""
from pathlib import Path
import sys, json, struct, hashlib
from unicorn import Uc,UC_ARCH_MIPS,UC_MODE_MIPS32,UC_MODE_LITTLE_ENDIAN,UC_HOOK_CODE,UC_HOOK_MEM_WRITE
from unicorn import mips_const as m
H=Path(__file__).resolve().parent;R=H.parents[2]
sys.path.insert(0,str(R/'work/ultimate_costume_swap_20261105/audit'))
from native_contracts import cpu,RETURN
CFG={
 'us':dict(exe='SLUS_005.61',enter=0x800921e8,rng=0x8002b73c,xa=0x8001663c,timer=0x1721f6,wait=0x8009227c,busy=0x173c84,music=0x8001653c),
 'jp':dict(exe='SLPS_009.02',enter=0x80092244,rng=0x8002b790,xa=0x80016670,timer=0x1722ae,wait=0x800922c8,busy=0x173d3c,music=0x80016570)}
ADDRESS=0x800921f8;BEFORE=bytes.fromhex('18004014');AFTER=bytes(4)
def patch_voice_call(exe):
 off=ADDRESS-0x8000f800
 if exe[off:off+4]!=BEFORE:raise ValueError('boss intro branch differs: fail closed')
 out=bytearray(exe);out[off:off+4]=AFTER
 return bytes(out)
def setup(region,patched=False):
 c=CFG[region];exe=(H/c['exe']).read_bytes()
 if patched:exe=patch_voice_call(exe)
 u=Uc(UC_ARCH_MIPS,UC_MODE_MIPS32|UC_MODE_LITTLE_ENDIAN);u.ctl_set_cpu_model(m.UC_CPU_MIPS32_4KC)
 u.mem_map(0,0x200000);u.mem_map(0x1f800000,4096)
 base,size=struct.unpack_from('<II',exe,0x18);u.mem_write(base&0x1fffffff,exe[2048:2048+size])
 state={'rng':0,'calls':[],'writes':[]}
 def code(mu,pc,size,_):
  if pc==RETURN:mu.emu_stop()
  elif pc==c['rng']:
   mu.reg_write(m.UC_MIPS_REG_V0,state['rng']);mu.reg_write(m.UC_MIPS_REG_PC,mu.reg_read(m.UC_MIPS_REG_RA))
  elif pc in (c['xa'],c['music']):
   state['calls'].append({'api':'xa' if pc==c['xa'] else 'music','a0':mu.reg_read(m.UC_MIPS_REG_A0),'a1':mu.reg_read(m.UC_MIPS_REG_A1)})
   mu.reg_write(m.UC_MIPS_REG_PC,mu.reg_read(m.UC_MIPS_REG_RA))
 def write(mu,access,at,size,value,_):
  p=at&0x1fffffff
  if p<0x1fef00:state['writes'].append((p,size,value))
 for at in (RETURN,c['rng'],c['xa'],c['music']):u.hook_add(UC_HOOK_CODE,code,begin=at,end=at)
 # Inspect RAM deltas after the call; a write callback in a branch delay slot
 # causes a known instrumentation exception in this Unicorn build.
 return u,state,c
def run(u,s,c,entry,a0=0):
 s['calls']=[];s['writes']=[]
 u.reg_write(m.UC_MIPS_REG_A0,a0);u.reg_write(m.UC_MIPS_REG_SP,0x801ff000);u.reg_write(m.UC_MIPS_REG_RA,RETURN)
 u.reg_write(m.UC_MIPS_REG_S0,0x12345678)
 before=bytes(u.mem_read(0,0x200000))
 try:u.emu_start(entry,RETURN)
 except Exception as ex:raise RuntimeError((c['exe'],hex(entry),hex(u.reg_read(m.UC_MIPS_REG_PC)),s)) from ex
 assert u.reg_read(m.UC_MIPS_REG_PC)==RETURN
 assert u.reg_read(m.UC_MIPS_REG_S0)==0x12345678
 after=bytes(u.mem_read(0,0x200000))
 # Fast equal slices prove all non-stack/non-timer bytes unchanged.
 assert before[:c['timer']]==after[:c['timer']]
 assert before[c['timer']+1:0x1fef00]==after[c['timer']+1:0x1fef00]
 assert before[0x1ff000:]==after[0x1ff000:]
 return {'calls':s['calls'][:],'timer':u.mem_read(c['timer'],1)[0]}
def main():
 mapping=json.loads((H/'xa_mapping.json').read_text())
 results={};wait=[]
 for name in ('us','jp','patched'):
  u,s,c=setup('jp' if name=='jp' else 'us',name=='patched')
  results[name]={}
  for boss in range(13):
   for rand in range(256):
    s['rng']=rand;u.mem_write(c['timer'],b'\x77')
    results[name][boss,rand]=run(u,s,c,c['enter'],boss)
  u.mem_write(c['timer'],b'\1')
  for busy in [1,1,1,0]:
   u.mem_write(c['busy'],bytes([busy]));res=run(u,s,c,c['wait']);wait.append({'region':name,'busy':busy,**res})
   assert res['timer']==(1 if busy else 0)
   assert len(res['calls'])==(0 if busy else 1)
  del u
 count=0
 for boss in range(13):
  for rand in range(256):
   expected=mapping['jp']['bosses'][boss]['track_ids'][rand%3]
   assert results['patched'][boss,rand]==results['jp'][boss,rand]=={'calls':[{'api':'xa','a0':expected,'a1':127}],'timer':1}
   assert results['us'][boss,rand]==(results['patched'][boss,rand] if boss>=8 else {'calls':[],'timer':60})
   count+=1
 original=(H/'SLUS_005.61').read_bytes();fixed=patch_voice_call(original)
 changed=[i for i,(a,b) in enumerate(zip(original,fixed)) if a!=b]
 assert all(ADDRESS-0x8000f800<=i<ADDRESS-0x8000f800+4 for i in changed)
 try:patch_voice_call(fixed)
 except ValueError: reject=True
 else:reject=False
 assert reject
 result={'passed':True,'cases_boss_by_rng':count,'native_function_executions':count*3,'rng_contract':'return all 256 low-byte possibilities; native modulo/table/pick/dispatch executed','xa_stub_contract':'record command/volume only; no CD emulation in this test','write_contract':'only timer byte and stack; saved s0 preserved','wait_results':wait,'source_sha256':hashlib.sha256(original).hexdigest(),'patched_reference_exe_sha256':hashlib.sha256(fixed).hexdigest(),'patch':{'address':hex(ADDRESS),'file_offset':ADDRESS-0x8000f800,'before':BEFORE.hex(),'after':AFTER.hex(),'changed_bytes':len(changed)},'bad_source_rejected':reject,'limitations':['실제 XA 스트리밍/CD 완료 콜백은 별도 검증 대상','개전 60호출 무음대기 대신 음성 끝날 때까지 대기; 전투 AI와 공격 프레임은 변경하지 않음']}
 (H/'native_voice_probe.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8')
 (H/'branch_proposal.json').write_text(json.dumps({'purpose':'8보스 개전음성 호출 복구','patches':[result['patch']],'current_exe_sha256':'1789ef719487b3e49571ccc2f419d6eb36c16f03709a16cb74f856d433f699ab','guard':'원주소4바이트 일치, 실제 전체입력 SHA는 통합자가 추가 검사','no_disc_written':True,'test':'native_voice_probe.json'},ensure_ascii=False,indent=2),encoding='utf8')
 print(json.dumps({'passed':True,'cases':count,'patch':result['patch']},indent=2))
if __name__=='__main__':main()
