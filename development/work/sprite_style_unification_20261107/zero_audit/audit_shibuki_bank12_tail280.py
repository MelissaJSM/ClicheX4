"""현재 부모의 캡슐12 종료 읽기와 조건부280B 주소계획. ARC 생성 없음."""
from pathlib import Path
import hashlib,json,struct,sys,collections
ROOT=Path(__file__).resolve().parents[3];D=Path(__file__).parent;B=D.parent;H=B/'shibuki_audit'
sys.path[:0]=[str(ROOT),str(D)]
from scripts.c01_audio_build import read_disc
from scripts.prepare_riko_ui import entry
from src.psx_player import bank_offsets,graphics_bank,decode_stream,composition_frame
from unicorn import Uc,UC_ARCH_MIPS,UC_MODE_MIPS32,UC_MODE_LITTLE_ENDIAN,UC_HOOK_CODE,UC_HOOK_MEM_READ
from unicorn import mips_const as m
from verify_pl00_directory_native import put,word,exe_at
sha=lambda b:hashlib.sha256(b).hexdigest();rel=lambda p:p.relative_to(ROOT).as_posix()
O=D/'shibuki_bank12_tail280_audit01';O.mkdir(exist_ok=True)
tracked={}
def load(p):
 b=p.read_bytes();tracked[rel(p)]=sha(b);return b
ap=H/'prepared_hurt_base01/PL00_U.ARC';arc=load(ap)
assert sha(arc)=='87e7d1db40c2380815ca2986bc27382db73f718d9c338d2eaad776372a2e257b'
proposal=json.loads(load(H/'standing_special_capacity_readonly.json'))
gfx,c=entry(arc,2),entry(arc,3);bs=bank_offsets(gfx,allow_aliases=True);cs=bank_offsets(c)
assert len(gfx)==186228 and len(bs)==14 and bs[1]==bs[2]and bs[4]==bs[5]
rows=[];allrefs=[]
for k in range(14):
 bank=graphics_bank(gfx,k,allow_bank_aliases=True);ends=[]
 for f in bank['frames']:
  dec=decode_stream(gfx,f['offset'],f['limit'],f['tile_count']*128);ends.append(dec.end)
  allrefs.append({'bank':k,'ref':f['index'],'offset':f['offset'],'end':dec.end,'tile_count':f['tile_count'],'raw_sha256':sha(dec.data)})
 last=max(ends);rows.append({'bank':k,'base':bank['base'],'end':bank['end'],'frame_count':len(bank['frames']),'unique_streams':len({f['offset']for f in bank['frames']}),'consumed_end':last,'aligned_consumed_end':(last+3)&~3,'tail':bank['end']-((last+3)&~3),'bank_sha256':sha(gfx[bank['base']:bank['end']])})
b12=rows[12];assert b12['base']==183172 and b12['end']==184744 and b12['consumed_end']==184462 and b12['tail']==280
bank=graphics_bank(gfx,12,allow_bank_aliases=True);assert len(bank['frames'])==11 and len({f['offset']for f in bank['frames']})==1
assert all(f['tile_count']==48 and f['offset']==183216 for f in bank['frames'])
newbases=[p+(280 if 1<=k<=12 else 0)for k,p in enumerate(bs)]
assert newbases[1]==newbases[2]and newbases[4]==newbases[5]and newbases[13]==bs[13]
plans=[]
for k,r in enumerate(rows):
 end=next((n for n in newbases[k+1:]if n>newbases[k]),len(gfx));span=end-newbases[k]
 if k==0:assert span==r['end']-r['base']+280
 elif k==12:assert span==1292 and r['aligned_consumed_end']-r['base']==span
 else:assert span==r['end']-r['base']
 plans.append({'bank':k,'old_start':r['base'],'planned_start':newbases[k],'planned_end':end,'planned_span':span,'header_words_change_required':False})
binp=ROOT/'out/ver_buki_riko/sprite_style_unification_20261107_v20/shibuki_riko.bin'
assets,_=read_disc(binp,('SLUS_005.61',));us,_=read_disc(ROOT/'MegaMan X4.bin',('SLUS_005.61',))
exe=assets['SLUS_005.61'];orig=us['SLUS_005.61']
oldreport=json.loads(load(D/'pl00_bank_relocation_audit01/report.json'));inv=json.loads(load(D/'pl00_bank_relocation_audit01/native_inventory.json'))
direct=json.loads(load(D/'pl00_bank_relocation_audit01/direct_gfx_pointer_reads.json'))
for q in inv['code'].values():
 a,z=int(q['start'],16),int(q['end'],16);data=exe_at(exe,a,z-a);assert sha(data)==q['sha256'] and data==exe_at(orig,a,z-a)
for q in direct:
 a=int(q['load_address'],16);assert exe_at(exe,a-8,108)==exe_at(orig,a-8,108)
previous_native=json.loads(load(D/'shibuki_run32_directory_native01/report.json'))
runarc=load(H/'prepared_base_run01/PL00_U.ARC');rungfx=entry(runarc,2)
assert gfx[bs[1]:]==rungfx[bs[1]:], 'All relocated effect/capsule banks must retain previous proven bytes'
capsule_types=list(exe_at(exe,0x8010d414,5));typ=next(i for i,q in enumerate(capsule_types)if q==2)
G=0x1789a0;C=0x1b0000;OBJ=0x1418c8;Q=0x1659d0;BUF=0x16eea8;STOP=0x80008000
executed=set()
def case(n,watch):
 u=Uc(UC_ARCH_MIPS,UC_MODE_MIPS32|UC_MODE_LITTLE_ENDIAN);u.mem_map(0,0x200000);u.mem_map(0x1f800000,0x1000)
 base,size=struct.unpack_from('<II',exe,24);u.mem_write(base&0x1fffffff,exe[2048:2048+size]);u.mem_write(G,gfx);u.mem_write(C,c)
 u.mem_write(OBJ,bytes(228));u.reg_write(m.UC_MIPS_REG_SP,0x801ff000)
 ctl={'stop':STOP};reads=[]
 def trace(cpu,addr,size,data):
  if addr==ctl['stop']:cpu.emu_stop();return
  executed.add(addr)
 u.hook_add(UC_HOOK_CODE,trace)
 if watch:
  def read(cpu,access,addr,size,value,data):
   p=addr&0x1fffffff
   if G<=p<G+len(gfx):reads.append((p-G,size,cpu.reg_read(m.UC_MIPS_REG_PC)))
  u.hook_add(UC_HOOK_MEM_READ,read)
 def run(start,end=STOP):
  ctl['stop']=end;u.reg_write(m.UC_MIPS_REG_RA,STOP);u.emu_start(start,0,count=1000000);assert u.reg_read(m.UC_MIPS_REG_PC)==end
 for kind,address,data,scratch in ((2,G,gfx,0x1f800014),(3,C,c,0x1f80001c)):
  put(u,0x137cd4,kind);put(u,0x137dc4,0x80000000+address);put(u,0x137dc8,len(data));run(0x80014040,0x80014094)
  assert word(u,scratch)==0x80000000+address and word(u,0x137dc4)==0x80000000+address+len(data)
 u.mem_write(OBJ+2,bytes([typ]));u.reg_write(m.UC_MIPS_REG_S0,0x80000000+OBJ)
 u.reg_write(m.UC_MIPS_REG_A1,24);u.reg_write(m.UC_MIPS_REG_A2,0);u.reg_write(m.UC_MIPS_REG_T0,0)
 run(0x800c6f20,0x800c6f98)
 gp=word(u,OBJ+0x38);cp=word(u,OBJ+0x3c)
 assert gp==0x80000000+G+bs[12]and cp==0x80000000+C+cs[20]
 u.mem_write(OBJ+0x47,bytes([n]));u.mem_write(OBJ+0x48,b'\xff');u.mem_write(OBJ+0x49,b'\0');put(u,0x141f68,0x80000000+Q);u.mem_write(Q,bytes(108))
 guard=bytes((i*53+17)&255 for i in range(6272));u.mem_write(BUF-64,guard)
 u.reg_write(m.UC_MIPS_REG_A0,0x80000000+OBJ);u.reg_write(m.UC_MIPS_REG_A1,320);u.reg_write(m.UC_MIPS_REG_A2,32)
 run(0x80015ecc)
 f=bank['frames'][n];expected=decode_stream(gfx,f['offset'],f['limit'],f['tile_count']*128).data;actual=bytes(u.mem_read(BUF,6144));assert actual==expected
 assert bytes(u.mem_read(BUF-64,64))==guard[:64]and bytes(u.mem_read(BUF+6144,64))==guard[-64:]
 queue=[];output=bytearray()
 for i in range(9):
  x,y,w,h,p=struct.unpack('<hhhhI',u.mem_read(Q+i*12,12))
  if not p:break
  sz=w*h*2;assert BUF<=(p&0x1fffffff)and(p&0x1fffffff)+sz<=BUF+6144
  output.extend(u.mem_read(p&0x1fffffff,sz));queue.append([x,y,w,h])
 assert bytes(output)==expected
 if watch:
  assert (48,4,0x800c6f44)in reads
  compressed=[(a,s,pc)for a,s,pc in reads if a>=f['offset']]
  assert min(a for a,s,pc in compressed)==183216 and max(a+s for a,s,pc in compressed)==184462
  assert not any(a+s>184462 for a,s,pc in compressed)
  assert set((a,s)for a,s,pc in reads if a<f['offset'])=={(48,4),(bs[12]+n*4,4)}
 return {'ref':n,'graphics_pointer':hex(gp),'composition_pointer':hex(cp),'raw_sha256':sha(actual),'queue':queue,'compressed_read_min':183216 if watch else None,'compressed_read_end':184462 if watch else None,'entry2_read_operations':len(reads),'read_sites':sorted({hex(pc)for a,s,pc in reads})}
native=[]
for n in range(11):
 a=case(n,False);b=case(n,True)
 assert all(a[k]==b[k]for k in ('ref','graphics_pointer','composition_pointer','raw_sha256','queue'));native.append(b)
for pc in executed:assert exe_at(exe,pc,4)==exe_at(orig,pc,4)
comp=[{'ref':n,'parts':composition_frame(c,20,n)['parts']}for n in range(11)]
# This is a supplemental literal search, not a whole-program pointer proof.
literals=[]
for value in (bs[12],G+bs[12],0x80000000+G+bs[12],183216,G+183216,0x80000000+G+183216,184464,184744):
 pat=struct.pack('<I',value);hits=[i for i in range(2048,len(exe)-3,4)if exe[i:i+4]==pat]
 literals.append({'value':hex(value),'aligned_exe_occurrences':[hex(struct.unpack_from('<I',exe,24)[0]+i-2048)for i in hits]})
tail=gfx[184464:184744]
result={'passed':True,'scope':'부모87e7 bank12 실제원MIPS 소비와 280B 내부배치 계산의 읽기 조사. 신규ARC/재배치 실행 아님.',
 'parent_sha256':sha(arc),'entry2_size':len(gfx),'entry2_sha256':sha(gfx),'bank_rows':rows,'all_508_references':allrefs,
 'bank12':{'header':gfx[183172:183216].hex(),'stream_start':183216,'decoder_end_exclusive':184462,'alignment_end_exclusive':184464,'tail_end_exclusive':184744,'tail_size':280,'tail_sha256':sha(tail),'tail_nonzero_bytes':sum(x!=0 for x in tail),'all_11_share_one_48tile_stream':True,'parts_bank20':comp},
 'planned_directory':newbases,'planned_banks':plans,'capsule_type_lookup':capsule_types,'bank12_type':typ,
 'native_parent_only':{'loader_original':True,'directory_offset':48,'capsule_initializer_original':True,'python_bank_pointer_injected':False,'cases':native,'observer_and_no_observer_results_exact':True,'code_patches':False,'all_executed_original_US_exact':True,'executed_addresses':[hex(p)for p in sorted(executed)]},
 'latest_checked_EXE':{'bin':rel(binp),'sha256':sha(exe),'all_previous_read_contexts_original_US_exact':True,'direct_contexts':len(direct),'bounded_scan_limit':'기존30개 직접scratch+14독자 문맥과로더/캡슐/디코더바이트 재대조. 모든가능한간접포인터의부재를증명하는whole-program분석이아님.'},
 'all_effect_banks1_through13_equal_previous_native381d':True,'previous_508ref_native_report_sha256':tracked[rel(D/'shibuki_run32_directory_native01/report.json')],
 'literal_scan':literals,'read_only_conclusion':'현재부모의bank12 280B는실제캡슐11헤더와원MIPS디코더/전송경로에서읽지않는후미다. 제안은기존검토한entry2내부directory재배치형태와동일하며조건부시험후보로진행할기술근거가있다. 새후보의508ref주소/원화/비대상/MIPS검증은별도로필요하다.',
 'constraints':['entry2총186228B·bank13주소184744·외부LBA/ARC크기·EXE와기타entry를보존한다.','은행1/2·4/5동일주소alias를그대로+280이동하고bank12의원1292B앞부분/정렬2B를보존한다.','bank12각48tile6144B·11프레임header·bank20조립/캡슐타입표와타이밍을보존한다. 타일이나hidden texel 삭제가아니다.','새ARC정상load후객체초기화를전제로한다. 기존세이브상주객체의캐시+38포인터를새배치에재사용하지않는다.','새은행0의95/96/97변경은별도원화검사. 이번독립검사는new joint.raw 타깃15층/압축부족280B를재패킹검증하지않았다.'],
 'limitations':['부모의bank12만새로MIPS실행했고후보는생성하지않았다. 이전508native를새후보통과로재사용하지않는다.','캡슐블록시작의allocator결과fixture및ref바이트를사용했다. 전체캡슐생성/게임실기/동시객체할당검사가아니다.','임의간접고정포인터는정적독자조사범위를넘어부재증명을하지못한다. 확인된native경로에고정bank12주소참조는없다.'],
 'source_files':tracked,'resource_or_game_modified':False,'relocated_candidate_created':False,'approval_claim':False}
(O/'report.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n','utf8')
print(json.dumps({'passed':True,'sha256':sha((O/'report.json').read_bytes()),'bank12':{k:result['bank12'][k]for k in('stream_start','decoder_end_exclusive','alignment_end_exclusive','tail_size','tail_nonzero_bytes')},'bank12_type':typ,'literal_scan':literals,'native_cases':len(native)}))
