"""원 US 부분아머 함수 전체에서 빈 헤드층 count0의 안전한 건너뛰기를 검사한다."""
from pathlib import Path
import hashlib,json,struct,sys
D=Path(__file__).resolve().parent;ROOT=D.parents[3]
sys.path.insert(0,str(ROOT))
from scripts.c01_audio_build import read_disc
from scripts.prepare_riko_ui import entry
from src.psx_player import bank_offsets,composition_frame
from unicorn import Uc,UC_ARCH_MIPS,UC_MODE_MIPS32,UC_MODE_LITTLE_ENDIAN,UC_HOOK_CODE
from unicorn import mips_const as m
from capstone import Cs,CS_ARCH_MIPS,CS_MODE_MIPS32,CS_MODE_LITTLE_ENDIAN

O=D/'native_empty01';NEW=D/'candidate01/PL00_U.ARC'
BIN=ROOT/'out/ver_rin_nana/sprite_style_unification_20261107_v39/rin_nana.bin'
US=ROOT/'MegaMan X4.bin'
EMPTY=(128,129,132,140,159);EXISTING=(109,112,113,114)
EXPECTED='96ac22f62d1f22d429211d6f2d44751cf2bcfc04b57cb855c776951e2f0cbf72'
PARENT='8951948879773266cae0bebd408b411f4806b5652257bba3c50df0212b3c6e10'
SOURCE='8eb84afaa7c201dfcaee8e5cbf4c2fef152d423b10b501e8238362f9b5cca5b2'
sha=lambda b:hashlib.sha256(b).hexdigest()
def digest(p):
 with p.open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def need(ok,msg):
 if not ok:raise ValueError(msg)
def put(u,a,v):u.mem_write(a&0x1fffffff,struct.pack('<I',v))
def word(u,a):return struct.unpack('<I',u.mem_read(a&0x1fffffff,4))[0]
def rel(p):return p.relative_to(ROOT).as_posix()
need(not O.exists(),'신규 소유폴더');need(digest(BIN)==SOURCE,'RN39 source');need(digest(US)=='3ceab06ac99add4035f912188bcbf5b16c02056f46a33d38ff0c8dbce6cb613b','원US')
src=read_disc(BIN,('PL00_U.ARC','SLUS_005.61'))[0];exe=src['SLUS_005.61'];parent=src['PL00_U.ARC'];original=read_disc(US,('SLUS_005.61',))[0]['SLUS_005.61'];new=NEW.read_bytes()
need(sha(parent)==PARENT and sha(new)==EXPECTED,'부모/후보 고정')
at,size=struct.unpack_from('<II',exe,24)
def codebytes(e,pc,n=4):return e[pc-at+2048:pc-at+2048+n]
need(codebytes(exe,0x8002588c,0x450)==codebytes(original,0x8002588c,0x450),'실제 부분아머 함수 원US exact')
GADDR=0x1789a0;CADDR=0x1b0000;OBJ=0x1418c8;STOP=0x80008000
PREV=0x170000;NEXT=PREV+40;DRAW=0x171000;ORDER=0x13bc40
executed=set();rows=[]
def run_case(data,n,facing,count_expected):
 u=Uc(UC_ARCH_MIPS,UC_MODE_MIPS32|UC_MODE_LITTLE_ENDIAN);u.mem_map(0,0x200000);u.mem_map(0x1f800000,0x1000)
 u.mem_write(at&0x1fffffff,exe[2048:2048+size]);g,c=entry(data,2),entry(data,3)
 need(GADDR+len(g)<CADDR and CADDR+len(c)<0x1ff000,'자원 fixture 비중첩')
 u.mem_write(GADDR,g);u.mem_write(CADDR,c);u.mem_write(OBJ,bytes(228));u.reg_write(m.UC_MIPS_REG_SP,0x801ff000)
 trace=[];control={'stop':STOP};lookup={}
 def code(cpu,addr,length,user):
  if addr==control['stop']:cpu.emu_stop();return
  executed.add(addr);trace.append(addr)
  if addr==0x80025974:
   sp=cpu.reg_read(m.UC_MIPS_REG_SP);lookup.update(count=word(cpu,sp+0x40),pointer=word(cpu,sp+0x18))
 u.hook_add(UC_HOOK_CODE,code)
 def run(start,end=STOP):
  control['stop']=end;u.reg_write(m.UC_MIPS_REG_RA,STOP);u.emu_start(start,0,count=1000000)
  need(u.reg_read(m.UC_MIPS_REG_PC)==end,'원함수 반환')
 # 원 RAM 로더가 실제 scratchpad의 자원 주소를 설정한다.
 for kind,ptr,resource,sp in ((2,GADDR,g,0x1f800014),(3,CADDR,c,0x1f80001c)):
  put(u,0x137cd4,kind);put(u,0x137dc4,0x80000000+ptr);put(u,0x137dc8,len(resource));run(0x80014040,0x80014094)
  need(word(u,sp)==0x80000000+ptr,'원로더 scratch 주소')
 # GPU packet allocator/ordering table은 독립 fixture이며 코드/함수 stub은 없다.
 guard=bytes((i*19+7)&255 for i in range(256));u.mem_write(PREV,guard);u.mem_write(DRAW,guard)
 put(u,0x1f800000,0);put(u,0x1f800100,0x80000000+NEXT);put(u,0x1f800104,0x80000000+DRAW);put(u,ORDER,0x80000000+PREV)
 u.mem_write(OBJ+0x47,bytes([n]));u.mem_write(OBJ+0x14,b'\xff');u.mem_write(OBJ+0x15,bytes([facing]))
 for reg,value in [(m.UC_MIPS_REG_A0,0x80000000+OBJ),(m.UC_MIPS_REG_A1,0),(m.UC_MIPS_REG_A2,0x7843)]:u.reg_write(reg,value)
 trace.clear();run(0x8002588c)
 base=bank_offsets(c)[5];header=struct.unpack_from('<I',c,base+n*4)[0]
 need(lookup['count']==count_expected==(header&65535),'네이티브 count0 조회')
 need(lookup['pointer']==0x80000000+CADDR+base+(header>>16)*4,'원 디렉터리 주소')
 need(0x80025984 in trace and 0x80025c30 in trace and 0x800259a0 not in trace,'원 count0 분기, 파트 루프 미진입')
 need(word(u,0x1f800100)==0x80000000+NEXT and word(u,0x1f800104)==0x80000000+DRAW,'빈층 GPU 할당 증가 없음')
 need(word(u,ORDER)==0x80000000+PREV,'ordering tail 보존')
 need(bytes(u.mem_read(PREV+4,252))==guard[4:] and bytes(u.mem_read(DRAW,256))==guard,'새 primitive 영역 미작성')
 # 원 epilogue는 기존 마지막 packet의 link를 현재 drawmode 위치로 연결한다.
 expected_link=(struct.unpack_from('<I',guard)[0]&0xff000000)|(DRAW&0xffffff)
 need(word(u,PREV)==expected_link,'원 epilogue의 link 갱신')
 need(u.reg_read(m.UC_MIPS_REG_SP)==0x801ff000,'stack 복구')
 return {'ref':n,'facing':facing,'native_count':lookup['count'],'record_pointer':hex(lookup['pointer']),'returned':True,'part_loop_entered':False,'new_GPU_packets':0,'allocator_pointers_unchanged':True,'ordering_tail_unchanged':True,'prior_packet_link':hex(word(u,PREV)),'packet_state_sha256':sha(bytes(u.mem_read(PREV,256))+bytes(u.mem_read(DRAW,256))),'trace':trace}

for tag,data,ns in [('parent_existing_empty',parent,EXISTING),('candidate_existing_empty',new,EXISTING),('candidate_removed_transparent',new,EMPTY)]:
 for n in ns:
  for facing in (0,64):
   r=run_case(data,n,facing,0);r['source']=tag;rows.append(r)
need(len({r['packet_state_sha256']for r in rows})==1,'기존 count0와 동일 GPU allocator/packet 상태')
for pc in executed:need(codebytes(exe,pc)==codebytes(original,pc),'실행명령 원US exact')
O.mkdir();cs=Cs(CS_ARCH_MIPS,CS_MODE_MIPS32|CS_MODE_LITTLE_ENDIAN)
(O/'original_renderer_mips.txt').write_text('\n'.join(f'{i.address:08x} {i.mnemonic} {i.op_str}'for i in cs.disasm(codebytes(exe,0x8002588c,0x450),0x8002588c))+'\n','utf8')
pcs=sorted(executed);(O/'executed_addresses.json').write_text(json.dumps([hex(p)for p in pcs],indent=2)+'\n','utf8')
for r in rows:r['trace_sha256']=sha(b''.join(struct.pack('<I',p)for p in r.pop('trace')))
report={'passed':True,'scope':'원 RAM 로더와 원 US 부분아머 렌더러 전체 반환. 신규 빈층5와 기존 count0 네층을 양방향 비교. GPU packet 생성 루프를 건너뛰고 기존 count0와 동일 allocator/packet 상태.','candidate':rel(NEW),'candidate_sha256':sha(new),'parent_sha256':sha(parent),'source_bin':rel(BIN),'source_bin_sha256':SOURCE,'exe_sha256':sha(exe),'original_US_bin_sha256':digest(US),'original_function_range':['0x8002588c','0x80025cdc'],'zero_branch':'0x80025984 beqz v0,0x80025c30','empty_head_refs':list(EMPTY),'existing_empty_controls':list(EXISTING),'native_calls':len(rows),'native_loader_entries':[2,3],'executed_unique_instructions':len(pcs),'all_executed_original_US_exact':True,'executed_bytes_sha256':sha(b''.join(struct.pack('<I',p)+codebytes(exe,p)for p in pcs)),'cases':rows,'code_stubs_or_patches':False,'game_process_opened':False,'source_BIN_EXE_resources_changed':False,'runtime_verified':False,'limits':['실제 GPU 래스터화/실기/게임 도달성 검사가 아니다.','GPU allocator·ordering table·객체 상태는 독립 fixture이다. 원코드가 자원주소와 헤드 디렉터리를 조회했다.','빈층 epilogue는 이전 packet link를 갱신하지만 신규 primitive와 drawmode packet을 만들지 않으며, 기존 count0 네 참조와 최종 packet 상태가 같다.','Root 최종229 하체 변경 가능성 때문에 현재후보는 패킹 해결 증거이며 최종동결이 아니다.']}
(O/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf8')
plan={'project':'ver_rin_nana','source_bin':rel(BIN),'source_sha256':SOURCE,'resources':{'PL00_U.ARC':{'path':rel(NEW),'before':PARENT,'after':EXPECTED}},'checkpoint_only':True}
(D/'component_plan.json').write_text(json.dumps(plan,ensure_ascii=False,indent=2)+'\n','utf8')
print(json.dumps({'passed':True,'native_calls':len(rows),'report_sha256':digest(O/'report.json')}))
