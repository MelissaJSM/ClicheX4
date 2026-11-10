"""고정 선택 atlas의 원 RAM loader→directory→14종 선택 객체 초기화 실행."""
from pathlib import Path
import sys,json,struct,hashlib
ROOT=Path(__file__).resolve().parents[3];D=Path(__file__).parent;W=D.parent;O=D/'nana_selection8_capacity01'
sys.path.insert(0,str(ROOT))
from scripts.c01_audio_build import read_disc
from scripts.prepare_riko_ui import entry
from unicorn import Uc,UC_ARCH_MIPS,UC_MODE_MIPS32,UC_MODE_LITTLE_ENDIAN,UC_HOOK_CODE
from unicorn import mips_const as m
sha=lambda b:hashlib.sha256(b).hexdigest();rel=lambda p:p.relative_to(ROOT).as_posix()
r=json.loads((O/'report.json').read_text('utf8'));ui=(ROOT/r['input']['path']).read_bytes();assert sha(ui)==r['input']['sha256']
now=read_disc(ROOT/r['source_BIN'],['SLUS_005.61'])[0]['SLUS_005.61'];orig=read_disc(ROOT/'MegaMan X4.bin',['SLUS_005.61'])[0]['SLUS_005.61']
assert sha(now)==r['current_EXE_sha256']and sha(orig)==r['original_EXE_sha256']
ex=lambda e,a,n=4:e[a-0x80010000+2048:a-0x80010000+2048+n]
parts=entry(ui,10);directory=entry(ui,12);bases=struct.unpack_from('<3I',parts)
CADDR=0x180000;TADDR=0x190000;OBJ=0x1a0000;STOP=0x80008000;executed=set();cases=[]
for typ in range(14):
 u=Uc(UC_ARCH_MIPS,UC_MODE_MIPS32|UC_MODE_LITTLE_ENDIAN);u.mem_map(0,0x200000);u.mem_map(0x1f800000,0x1000)
 base,size=struct.unpack_from('<II',now,24);u.mem_write(base&0x1fffffff,now[2048:2048+size]);u.mem_write(CADDR,parts);u.mem_write(TADDR,directory);u.reg_write(m.UC_MIPS_REG_SP,0x801ff000)
 ctrl={'stop':STOP}
 def hook(cpu,addr,size,data):
  if addr==ctrl['stop']:cpu.emu_stop();return
  executed.add(addr)
 u.hook_add(UC_HOOK_CODE,hook)
 def put(addr,v):u.mem_write(addr,struct.pack('<I',v))
 def word(addr):return struct.unpack('<I',u.mem_read(addr&0x1fffffff,4))[0]
 def run(start,end=STOP):
  ctrl['stop']=end;u.reg_write(m.UC_MIPS_REG_RA,STOP);u.emu_start(start,0,count=100000)
  assert u.reg_read(m.UC_MIPS_REG_PC)==end,hex(u.reg_read(m.UC_MIPS_REG_PC))
 # These are RAM-loader inputs, not injected scratchpad or object bank pointers.
 for kind,addr,data,dest in[(10,CADDR,parts,0x1f800020),(12,TADDR,directory,0x801406a8)]:
  put(0x137cd4,kind);put(0x137dc4,0x80000000+addr);put(0x137dc8,len(data));run(0x80014040,0x80014094)
  assert word(dest)==0x80000000+addr
 u.mem_write(OBJ,bytes(256));u.mem_write(OBJ+2,bytes([typ]));u.reg_write(m.UC_MIPS_REG_A0,0x80000000+OBJ);run(0x800cca34)
 bank=2 if typ in(7,9,10)else 0 if typ in(8,11)else 1
 ptr=word(OBJ+0x3c);tex=struct.unpack('<H',u.mem_read(OBJ+0x40,2))[0]
 assert ptr==0x80000000+CADDR+bases[bank]
 assert tex==r['texture_directory'][bank]//128
 frame=u.mem_read(OBJ+0x47,1)[0];assert frame<r['banks'][bank]['frames']
 cases.append({'subtype':typ,'bank':bank,'texture_units_128bytes':tex,'composition_pointer':hex(ptr),'animation_table':hex(word(OBJ+0x30)),'initial_frame':frame,'CLUT':hex(struct.unpack('<H',u.mem_read(OBJ+0x42,2))[0]),'direction':u.mem_read(OBJ+0x15,1)[0]})
for a in executed:assert ex(now,a)==ex(orig,a)
report={'passed':True,'scope':'원 US RAM 완료 loader와 전체 선택 객체 initializer 14종의 실제 MIPS 실행. CD I/O·GPU·실기는 별도.','parent_report_sha256':sha((O/'report.json').read_bytes()),'candidate_written':False,'new_MIPS_executed':True,'native_loader_entries':[10,12],'native_loader_range':['0x80014040','0x80014094'],'initializer':'0x800cca34','all14_subtypes':cases,'executed_unique_opcodes':len(executed),'executed_original_US_exact':True,'executed_signature_sha256':sha(b''.join(struct.pack('<I',a)+ex(now,a)for a in sorted(executed))),'python_injected_object_or_scratchpad_pointers':False,'code_stubs_or_patches':False,'limits':['RAM에 실자원과 완료-loader 입력을 제공하고 원코드가 scratchpad/global directory 및 객체 포인터를 계산했다. CD-ROM 전송은 실행하지 않았다.','원래 선택 객체의 인물·탄환·텍스트·초상화 14종 전체가 세 조립은행 및 해당 texture offset을 사용한다. 임의로 잘못 생성한 다른 게임 객체의 모든 접근까지 증명한 것은 아니다.','GPU 렌더러 전체 또는 화면 전환 실기 검사는 이번 실행 범위가 아니다. 새 복사본은 별도 비대상 전체 비교와 UV 경계 검사가 필요하다.'],'runtime_verified':False,'resources_or_save_data_modified':False}
p=O/'native_initializers.json';assert not p.exists();p.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf8')
print(json.dumps({'passed':True,'sha256':sha(p.read_bytes()),'cases':cases,'unique_opcodes':len(executed)}))
