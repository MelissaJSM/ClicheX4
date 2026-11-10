"""현재 실행 파일의 캡슐 지급/몸체 표시를 격리 MIPS에서 추적한다."""
from pathlib import Path
import hashlib, importlib.util, json, struct, sys
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from unicorn import UC_HOOK_CODE, mips_const as m
from capstone import Cs, CS_ARCH_MIPS, CS_MODE_MIPS32, CS_MODE_LITTLE_ENDIAN
spec=importlib.util.spec_from_file_location('nc',ROOT/'work/ultimate_costume_swap_20261105/audit/native_contracts.py')
nc=importlib.util.module_from_spec(spec);spec.loader.exec_module(nc)
EXE=(H/'before/SLUS_005.61').read_bytes()
P=0x1418c8;E=0x1721c0;O=0xa000;END=nc.RETURN
RET=bytes.fromhex('0800e00300000000')

def run_case(part,direction,order,ultimate=1,initial=0):
 u=nc.cpu(EXE)
 # Only resource lookup, GPU upload/visibility and final part rasterization are
 # isolated boundaries. Actual state, animation stepping and armor routing run.
 for at in (0x2938c,0x15ecc,0x2b318,0x2588c):u.mem_write(at,RET)
 u.mem_write(0x2938c,bytes.fromhex('0800e00321100000')) # return resource index0
 u.mem_write(0x1f800014,struct.pack('<I',0x80010000))
 u.mem_write(0x1f80001c,struct.pack('<I',0x80010200))
 u.mem_write(0x10000,b''.join(struct.pack('<I',0x1000+i*0x100) for i in range(24)))
 u.mem_write(0x10200,b''.join(struct.pack('<I',0x3000+i*0x100) for i in range(24)))
 u.mem_write(P+8,struct.pack('<II',0x09128000,0x03214000))
 u.mem_write(P+0x15,bytes([direction]));u.mem_write(P+0x30,struct.pack('<I',0x80119df0))
 u.mem_write(O+2,bytes([part]));u.mem_write(E+0x37,bytes([ultimate]))
 for at in [P+0xa7,E+0x47]:u.mem_write(at,bytes([initial]))
 for at in [P+0xb8,E+0x48]:u.mem_write(at,bytes([2 if initial&4 else 0]))
 draw=[]
 def observe(mu,pc,size,unused):
  if pc==END:mu.emu_stop()
  if pc==0x8002588c:draw.append(mu.reg_read(m.UC_MIPS_REG_A1))
 u.hook_add(UC_HOOK_CODE,observe)
 def call(at,obj=P,a1=0):
  u.reg_write(m.UC_MIPS_REG_SP,0x801ff000);u.reg_write(m.UC_MIPS_REG_RA,END)
  u.reg_write(m.UC_MIPS_REG_A0,obj|0x80000000);u.reg_write(m.UC_MIPS_REG_A1,a1)
  u.emu_start(at,0,count=20000)
  assert u.reg_read(m.UC_MIPS_REG_PC)==END,hex(u.reg_read(m.UC_MIPS_REG_PC))
 call(0x80015d60,P,107)
 call(0x800c6edc,O)
 assert u.mem_read(P+8,8)==u.mem_read(O+8,8)
 rows=[]
 for tick in range(300):
  pbytes=bytes(u.mem_read(P+0x44,4));obytes=bytes(u.mem_read(O+0x44,4))
  draw.clear();call(0x800257bc)
  owned=u.mem_read(E+0x47,1)[0]
  row={'tick':tick,'effect_ref':obytes[3],'effect_duration':obytes[0],
       'effect_cursor':hex(struct.unpack('<I',u.mem_read(O+0x34,4))[0]),
       'body_ref':pbytes[3],'body_duration':pbytes[0],'armor':owned,
       'body_mask':sum(1<<v for v in draw),'body_xy':list(struct.unpack('<II',u.mem_read(P+8,8))),
       'effect_xy':list(struct.unpack('<II',u.mem_read(O+8,8))),
       'body_facing':u.mem_read(P+0x15,1)[0],'effect_facing':u.mem_read(O+0x15,1)[0]}
  rows.append(row)
  assert row['body_ref']==0 and row['body_xy']==row['effect_xy']
  assert row['body_facing']==row['effect_facing']==direction
  assert row['body_mask']==((0 if owned else 15)if ultimate else owned)
  if not obytes[2]:
   call(0x800c6edc,O)
   assert u.mem_read(P+0xe2,1)==b'\x04'
   break
  for target in order:
   call(0x800332c0 if target=='body' else 0x800c6edc,P if target=='body' else O)
 else:raise AssertionError('capsule did not terminate')
 grant=next(r['tick'] for r in rows if r['armor']!=initial)
 assert rows[-1]['armor']==(15 if ultimate else initial|[1,2,4,4,8][part])
 collapsed=[]
 for r in rows:
  key=(r['effect_ref'],r['body_mask'])
  if not collapsed or (collapsed[-1]['effect_ref'],collapsed[-1]['body_mask'])!=key:
   collapsed.append({**r,'calls':1})
  else:collapsed[-1]['calls']+=1
 return {'ultimate':ultimate,'initial_armor':initial,'part':part,'facing':direction,'update_order':order,'calls':len(rows),
         'grant_tick':grant,'all_body_ref0':True,'all_xy_facing_exact':True,'sequence':collapsed}

def main():
 cases=[run_case(p,d,o) for p in range(5) for d in (0,64) for o in (['body','effect'],['effect','body'])]
 cases += [run_case(p,d,['body','effect'],0,mask)for p in range(5) for mask in range(16) if not mask&[1,2,4,4,8][p] for d in (0,64)]
 md=Cs(CS_ARCH_MIPS,CS_MODE_MIPS32|CS_MODE_LITTLE_ENDIAN)
 sections={'capsule_part_update':(0x800c6edc,0x800c7164),'player_script_victory':(0x800332c0,0x80033394),
           'player_start_script':(0x80034e2c,0x80034fe0),'costume_renderer':(0x800257bc,0x8002588c)}
 lines=[]
 for name,(lo,hi) in sections.items():
  lines.append(name);lines += [f'{i.address:08x}: {i.mnemonic} {i.op_str}' for i in md.disasm(nc.code(EXE,lo,hi),lo)]
 (H/'native_disassembly.txt').write_text('\n'.join(lines)+'\n','utf8')
 out={'passed':True,'exe_sha256':hashlib.sha256(EXE).hexdigest(),'cases':cases,
      'scope':'실제 MIPS의 연속 애니메이션·지급 이벤트·몸체 표시 분기. 자원 조회/GPU 업로드/화면 판정/래스터 함수만 격리 stub. 실제 게임이나 외부 충돌/카메라 실행은 아님.',
      'historical_ultimate_conclusion':'지급 뒤 잔상이 끝날 때까지 본체 ref0 고정, 세계 좌표와 방향 동일. 지급 이벤트에서 재킷 mask15→수영복 mask0 전환. 호흡/승리 자세가 잔상과 겹치는 원인은 이 경로에서 없음.',
      'runtime_emulator_verified':False,'game_or_save_modified':False}
 (H/'native_timeline.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n','utf8')
 print(json.dumps({'passed':True,'cases':len(cases),'calls':cases[0]['calls'],'grant_tick':cases[0]['grant_tick'],'sequence':[(r['effect_ref'],r['body_mask'],r['calls']) for r in cases[0]['sequence']]}))
if __name__=='__main__':main()
