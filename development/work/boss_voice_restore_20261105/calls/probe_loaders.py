from pathlib import Path
import sys,json,struct
from unicorn import UC_HOOK_CODE
from unicorn import mips_const as m
H=Path(__file__).resolve().parent;R=H.parents[2]
sys.path.insert(0,str(R/'work/ultimate_costume_swap_20261105/audit'))
from native_contracts import cpu,RETURN
def main():
 e=(H/'SLUS_005.61').read_bytes();mp=json.loads((H/'loader_mapping.json').read_text())['us'];paths=mp['path_id_map']
 out=[]
 for stage in range(13):
  for area in ([0] if stage in (9,10) else [0,1]):
   u=cpu(e);obj=0x180000;calls=[]
   u.mem_write(0x1721cc,bytes([stage,area]));u.mem_write(0x171ea8,b'\0');u.mem_write(0x173c84,b'\0');u.mem_write(0x1406ac,b'\2');u.mem_write(0x13bd40,b'\0');u.mem_write(0x141f38,struct.pack('<I',0x34560))
   def load(mu,pc,size,_):
    calls.append({'archive_id':mu.reg_read(m.UC_MIPS_REG_A0),'allocation_mode':mu.reg_read(m.UC_MIPS_REG_A1),'spu_address':mu.reg_read(m.UC_MIPS_REG_A2)})
    mu.reg_write(m.UC_MIPS_REG_PC,mu.reg_read(m.UC_MIPS_REG_RA))
   u.hook_add(UC_HOOK_CODE,load,begin=0x80013ad8,end=0x80013ad8)
   states=[]
   for _ in range(4):
    u.reg_write(m.UC_MIPS_REG_A0,obj|0x80000000);u.reg_write(m.UC_MIPS_REG_SP,0x801ff000);u.reg_write(m.UC_MIPS_REG_RA,RETURN)
    u.emu_start(0x800b5eec,RETURN)
    states.append(list(u.mem_read(obj+4,2)))
   for c in calls:c['archive']=paths[str(c['archive_id'])]
   expected=((area==1 and stage!=12) or stage==10)
   assert len(calls)==int(expected),(stage,area,calls)
   if expected:assert calls[0]['archive']==mp['stage_common'][stage]['boss_bank_archive'] and calls[0]['allocation_mode']==4 and calls[0]['spu_address']==0x34560
   out.append({'stage':stage,'area':area,'native_states':states,'calls':calls})
 rem=[]
 for checkpoint in range(2,10):
  u=cpu(e);u.mem_write(0x1721dd,bytes([checkpoint]));u.mem_write(0x141f38,struct.pack('<I',0x34560))
  # Actual engine checkpoint offset is verified from the native function below.
  u.emu_start(0x80012f44,0x80013ad8)
  fileid=u.reg_read(m.UC_MIPS_REG_A0)
  rem.append({'checkpoint':checkpoint,'file_id':fileid,'archive':paths[str(fileid)]})
  assert fileid==mp['rematch_checkpoint_2_to_9'][checkpoint-2]['id']
 report={'passed':True,'stage_load_cases':len(out),'stage_calls':out,'rematch_calls':rem,'scope':'실제 US MIPS 로더·stage switch·표조회, CD 로드함수는 격리환경에서 기록만 함','notes':['stage12 area1은 일반 effect loader에서 생략하고 FinalSigma 본체 0x8008D51C에서 STC_1_1을 따로 읽음','stage9 Colonel1은 ST09_00에 이미 들어있는 bank2를 사용']}
 (H/'loader_native_probe.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8');print('passed',len(out),len(rem))
if __name__=='__main__':main()
