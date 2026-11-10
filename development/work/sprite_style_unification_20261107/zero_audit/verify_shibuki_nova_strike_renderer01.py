"""원 RAM 로더/애니 초기화/해독 뒤 실제 본체·아머 렌더러의31+7파트 검사."""
from pathlib import Path
import collections,hashlib,json,struct,sys
ROOT=Path(__file__).resolve().parents[3];D=Path(__file__).parent;W=D.parent;H=W/'shibuki_audit';sys.path.insert(0,str(ROOT))
from scripts.c01_audio_build import read_disc
from scripts.prepare_riko_ui import entry
from src.psx_player import bank_offsets,graphics_bank,decode_stream,composition_frame
from scripts.export_x_consistency import animation_map
from unicorn import Uc,UC_ARCH_MIPS,UC_MODE_MIPS32,UC_MODE_LITTLE_ENDIAN,UC_HOOK_CODE,UC_HOOK_MEM_WRITE
from unicorn import mips_const as m
OBSERVER=sys.argv[1]if len(sys.argv)>1 else'none'
need_mode=OBSERVER in('none','single');assert need_mode
O=D/('shibuki_nova_strike2_renderer_native02'if OBSERVER=='none'else'shibuki_nova_strike2_renderer_single_observer01');assert not O.exists()
C=H/'prepared_nova_strike_base01/PL00_U.ARC';EXPECTED='36d4d0293abc77052c476e0495f4f4542ca75471c7a149f200e4bdb8f4e1bd4e'
BIN=ROOT/'out/ver_buki_riko/sprite_style_unification_20261107_v27/shibuki_riko.bin'
sha=lambda b:hashlib.sha256(b).hexdigest();rel=lambda p:p.relative_to(ROOT).as_posix()
def digest(p):
 with p.open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def need(x,s):
 if not x:raise AssertionError(s)
orig=read_disc(ROOT/'MegaMan X4.bin',('SLUS_005.61',))[0]['SLUS_005.61'];exe=read_disc(BIN,('SLUS_005.61',))[0]['SLUS_005.61'];data=C.read_bytes();need(sha(data)==EXPECTED,'candidate hash')
g,c=entry(data,2),entry(data,3);gb,cb=bank_offsets(g,allow_aliases=True),bank_offsets(c);bank=graphics_bank(g,0,allow_bank_aliases=True)
at,sz=struct.unpack_from('<II',exe,24)
def code(e,pc,n=4):return e[pc-at+2048:pc-at+2048+n]
wrapper=(0x800257bc,0x8002588c)
need(sha(code(exe,*[wrapper[0],wrapper[1]-wrapper[0]]))=='46c1fe4c8c01be08e49c733c24e99fe7e4e2416b93a2dc50585a3503854038c5','accepted wrapper')
for lo,hi in((0x80024334,0x80024920),(0x8002588c,0x80025cdc)):need(code(exe,lo,hi-lo)==code(orig,lo,hi-lo),'original renderer bytes')
an,refs=animation_map(exe);positions={n:next((q['id'],s['position'])for q in an for s in q['steps']if s['frame']==n)for n in(217,220)}
GADDR=0x1789a0;CADDR=0x1b0000;OBJ=0x1418c8;QUEUE=0x1659d0;STOP=0x80008000;PREV=0x170000;ORDER=0x13bc40
def put(u,a,v):u.mem_write(a&0x1fffffff,struct.pack('<I',v))
def word(u,a):return struct.unpack('<I',u.mem_read(a&0x1fffffff,4))[0]
def regs(u,**kw):
 for key,val in kw.items():u.reg_write(getattr(m,'UC_MIPS_REG_'+key.upper()),val)
executed=set();rows=[]
def run_case(n,facing,mask,arm,boundary=False):
 u=Uc(UC_ARCH_MIPS,UC_MODE_MIPS32|UC_MODE_LITTLE_ENDIAN);u.mem_map(0,0x200000);u.mem_map(0x1f800000,0x1000);u.mem_write(at&0x1fffffff,exe[2048:2048+sz]);u.mem_write(GADDR,g);u.mem_write(CADDR,c);u.mem_write(OBJ,bytes(228));regs(u,sp=0x801ff000)
 control={'stop':STOP,'phase':'loader','layer':0};lookups=[];consumed=[];packet_writes=[];debug_s0=[]
 def trace(cpu,pc,length,user):
  if pc==control['stop']:cpu.emu_stop();return
  executed.add(pc);control['pc']=pc
  if pc==0x8002588c:control['layer']=5+cpu.reg_read(m.UC_MIPS_REG_A1)
  if control['phase']!='renderer':return
  sp=cpu.reg_read(m.UC_MIPS_REG_SP)
  if pc in(0x8002446c,0x80024844,0x800ea0f4):debug_s0.append([hex(pc),hex(cpu.reg_read(m.UC_MIPS_REG_S0)),hex(cpu.reg_read(m.UC_MIPS_REG_S4))])
  if pc in(0x80024414,0x80025974):
   pb=0 if pc==0x80024414 else control['layer'];p=word(cpu,sp+(0x10 if pb==0 else 0x18));count=word(cpu,sp+0x40);lookups.append({'bank':pb,'pointer':p,'count':count})
  if pc in(0x8002446c,0x800259a0):
   pb=0 if pc==0x8002446c else control['layer'];p=word(cpu,sp+(0x10 if pb==0 else 0x18));consumed.append({'bank':pb,'record_pointer':p,'bytes':bytes(cpu.mem_read(p&0x1fffffff,4)).hex(),'primitive_pointer':cpu.reg_read(m.UC_MIPS_REG_S4),'drawmode_pointer':cpu.reg_read(m.UC_MIPS_REG_S6 if pb==0 else m.UC_MIPS_REG_S5)})
 u.hook_add(UC_HOOK_CODE,trace)
 def run(start,end=STOP):
  control['stop']=end;regs(u,ra=STOP);u.emu_start(start,0,count=1000000);need(u.reg_read(m.UC_MIPS_REG_PC)==end,f'return {start:x}')
 for kind,ptr,blob,sp in((2,GADDR,g,0x1f800014),(3,CADDR,c,0x1f80001c)):
  put(u,0x137cd4,kind);put(u,0x137dc4,0x80000000+ptr);put(u,0x137dc8,len(blob));run(0x80014040,0x80014094);need(word(u,sp)==0x80000000+ptr,'native RAM loader scratch')
 aid,pos=positions[n];put(u,OBJ+0x30,0x80119df0);regs(u,a0=0x80000000+OBJ,a1=aid,a2=pos);run(0x8003516c)
 need(u.mem_read(OBJ+0x47,1)==bytes([n]),'real animation selection');need(word(u,OBJ+0x38)==0x80000000+GADDR+gb[0]and word(u,OBJ+0x3c)==0x80000000+CADDR+cb[0],'native object pointers')
 f=bank['frames'][n];raw=decode_stream(g,f['offset'],f['limit'],f['tile_count']*128).data;buf=0x16dea8;guard=bytes((i*73+11)&255 for i in range(4224));u.mem_write(buf-64,guard);u.mem_write(OBJ+0x48,b'\xff');u.mem_write(OBJ+0x49,b'\x03');put(u,0x141f68,0x80000000+QUEUE);u.mem_write(QUEUE,bytes(108));regs(u,a0=0x80000000+OBJ,a1=320,a2=0);run(0x80015ecc)
 after=bytes(u.mem_read(buf-64,len(guard)));need(after[64:64+len(raw)]==raw and after[:64]==guard[:64]and after[64+len(raw):]==guard[64+len(raw):],'decoder and guard')
 output=bytearray();rects=[]
 for i in range(9):
  x,y,w,h,p=struct.unpack('<hhhhI',u.mem_read(QUEUE+i*12,12))
  if not p:break
  need(buf<=p&0x1fffffff and (p&0x1fffffff)+w*h*2<=buf+4096,'upload span');output.extend(u.mem_read(p&0x1fffffff,w*h*2));rects.append([x,y,w,h])
 need(bytes(output)==raw,'upload source bytes')
 layers=[0]+[pb for bit,pb in((8,8),(1,5),(4,7),(2,6))if mask&bit];parts={pb:composition_frame(c,pb,n)['parts']for pb in layers};total=sum(map(len,parts.values()));bodycount=len(parts[0]);display=int(boundary);startslot=1024-total if boundary else 0;startcounter=1000-bodycount if boundary else 0
 pbase=0x1499c8+display*0xa000;dbase=0x169d98+display*0x2000;pp=pbase+startslot*40;dp=dbase+startslot*8
 pguard=bytes((i*31+7)&255 for i in range(0xa000+128));dguard=bytes((i*19+13)&255 for i in range(0x2000+128));u.mem_write(pbase-64,pguard);u.mem_write(dbase-64,dguard);u.mem_write(PREV,bytes([0x77])*40)
 put(u,0x1f800000,display);put(u,0x1f800100,0x80000000+pp);put(u,0x1f800104,0x80000000+dp);put(u,0x1f800124,startcounter);put(u,ORDER+display*128,0x80000000+PREV)
 u.mem_write(OBJ+0x14,b'\xff');u.mem_write(OBJ+0x15,bytes([facing]));u.mem_write(OBJ+0x16,b'\0');u.mem_write(OBJ+0xa7,bytes([mask]));u.mem_write(OBJ+0xb8,bytes([arm]));u.mem_write(0x1721c0+0x37,b'\0');u.mem_write(OBJ+0xa,struct.pack('<H',160));u.mem_write(OBJ+0xe,struct.pack('<H',120))
 def watch(cpu,access,address,size,value,user):
  if control['phase']=='renderer':packet_writes.append((address&0x1fffffff,size,control['pc']))
 if OBSERVER=='single':u.hook_add(UC_HOOK_MEM_WRITE,watch,begin=pbase-64,end=dbase+0x2000+63)
 control['phase']='renderer';regs(u,a0=0x80000000+OBJ);run(0x80024334);regs(u,a0=0x80000000+OBJ);run(0x800257bc)
 need(len(consumed)==total and [l['bank']for l in lookups]==layers,'all expected layers/parts executed')
 expected=[]
 for pb in layers:
  ps=parts[pb];lookup=next(l for l in lookups if l['bank']==pb);start=0x80000000+CADDR+ps[0]['record_offset']if ps else None
  need(lookup['count']==len(ps)and(not ps or lookup['pointer']==start),'native layer count/directory lookup')
  for p in ps:expected.append((pb,0x80000000+CADDR+p['record_offset'],c[p['record_offset']:p['record_offset']+4].hex()))
 need([(a['bank'],a['record_pointer'],a['bytes'])for a in consumed]==expected,'native records read in order')
 for i,a in enumerate(consumed):need(a['primitive_pointer']==0x80000000+pp+40*i and a['drawmode_pointer']==0x80000000+dp+8*i,'each emitted packet address')
 need(word(u,0x1f800100)==0x80000000+pp+40*total and word(u,0x1f800104)==0x80000000+dp+8*total,'final packet cursors');need(word(u,0x1f800124)==startcounter+bodycount,'body global count only')
 pafter=bytes(u.mem_read(pbase-64,len(pguard)));dafter=bytes(u.mem_read(dbase-64,len(dguard)));po=64+40*startslot;do=64+8*startslot
 badp=[i for i,(a,b)in enumerate(zip(pafter,pguard))if a!=b and not po<=i<po+total*40]
 badd=[i for i,(a,b)in enumerate(zip(dafter,dguard))if a!=b and not do<=i<do+total*8]
 need(not badp,f'primitive guards n{n} mask{mask} facing{facing} arm{arm} boundary{boundary} total{total} positions{[hex(pbase-64+i)for i in badp[:20]]} debug{debug_s0}');need(not badd,f'drawmode guards {badd[:20]}')
 pool_writes=[q for q in packet_writes if pbase-64<=q[0]<pbase+0xa000+64 or dbase-64<=q[0]<dbase+0x2000+64]
 if OBSERVER=='single':need(pool_writes and all(pp<=a and a+s<=pp+total*40 or dp<=a and a+s<=dp+total*8 for a,s,pc in pool_writes),'all observed packet writes bounded')
 need(word(u,ORDER+display*128)==0x80000000+pp+(total-1)*40,'normal OT tail commit');need(u.reg_read(m.UC_MIPS_REG_SP)==0x801ff000,'stack restored')
 packets=[]
 for i in range(total):
  b=bytes(u.mem_read(pp+i*40,40));d=bytes(u.mem_read(dp+i*8,8));need(b[7]in(0x7d,0x2d),'actual GPU primitive command');need(d[3]==1 and struct.unpack('<I',d[4:])[0]&0xff000000==0xe1000000,'drawmode packet');packets.append({'record_bank':consumed[i]['bank'],'primitive_words':list(struct.unpack('<10I',b)),'drawmode_words':list(struct.unpack('<2I',d))})
 return {'ref':n,'facing':facing,'mask':mask,'arm_type':arm,'boundary_fixture':boundary,'animation':{'id':aid,'position':pos},'decoded_sha256':sha(raw),'upload_rects':rects,'native_layer_counts':{str(pb):len(parts[pb])for pb in layers},'total_packets':total,'primitive_bytes':40*total,'drawmode_bytes':8*total,'start_slot':startslot,'end_slot':startslot+total,'start_counter':startcounter,'end_counter':word(u,0x1f800124),'all_expected_records_consumed_in_order':True,'native_directory_lookup':True,'guards_exact':True,'normal_OT_commit':True,'packet_sha256':sha(bytes(u.mem_read(pp,total*40))+bytes(u.mem_read(dp,total*8))),'packets':packets}
try:
 for n in(217,220):
  for mask in range(16):
   for facing in(0,64):
    for arm in(0,2):rows.append(run_case(n,facing,mask,arm))
  for facing in(0,64):
   for arm in(0,2):rows.append(run_case(n,facing,15,arm,True))
  print(json.dumps({'ref':n,'cases':sum(r['ref']==n for r in rows),'complete':True}),flush=True)
except AssertionError as error:
 if OBSERVER=='single':
  O.mkdir(exist_ok=False)
  failure={'passed':False,'scope':'메모리쓰기observer가원renderer결과를바꾸는격리fixture 진단. 후보결함판정으로사용하지않음.','candidate_sha256':EXPECTED,'exe_sha256':sha(exe),'memory_observer':OBSERVER,'PC_RA_stores_or_code_patches':False,'error':str(error),'unobserved_control':'shibuki_nova_strike2_renderer_native01/report.json','unobserved_control_sha256':digest(D/'shibuki_nova_strike2_renderer_native01/report.json'),'provisional_cause':'쓰기hook부착과결과변화의상관만확인. Unicorn내부원인은분석하지않았으며PC읽기가원인이라는초기가설도미확정.'}
  (O/'diagnostic.json').write_text(json.dumps(failure,ensure_ascii=False,indent=2)+'\n','utf8')
 raise
pcs=sorted(executed);patched=[]
for pc in pcs:
 if code(exe,pc)!=code(orig,pc):need(wrapper[0]<=pc<wrapper[1],'unexpected non-original instruction');patched.append(pc)
need(sha(C.read_bytes())==EXPECTED,'candidate remained fixed');O.mkdir(exist_ok=False)
report={'passed':True,'scope':'원RAM완료loader→scratchpad→원애니wrapper/obj+38/+3c→원decode/upload→실제본체/아머renderer. 격리fixture이며게임실기/GPU래스터화아님.','candidate':rel(C),'candidate_sha256':EXPECTED,'source_bin':rel(BIN),'source_bin_sha256':digest(BIN),'exe_sha256':sha(exe),'original_US_exe_sha256':sha(orig),'actual_calls':len(rows),'all_16_masks_both_directions_and_two_arm_types':True,'near_capacity_fixtures':sum(r['boundary_fixture']for r in rows),'python_graphics_or_composition_pointer_injection':False,'base_and_partial_renderers_original_US_exact':True,'only_non_original_executed_range':{'start':hex(wrapper[0]),'end':hex(wrapper[1]),'known_accepted_PL00_mask_wrapper_sha256':sha(code(exe,wrapper[0],wrapper[1]-wrapper[0])),'executed_non_original_PCs':[hex(p)for p in patched]},'code_patches_or_stubs_used':False,'executed_instruction_count':len(pcs),'executed_address_bytes_sha256':sha(b''.join(struct.pack('<I',p)+code(exe,p)for p in pcs)),'cases':rows,'limitations':['원RAMloader의입력주소/객체좌표/아머/프레임테이블/packetallocator·OT는격리시험fixture이다. CD로더/전체frame dispatcher/다른동시객체를실행하지않음.','실제게임GPU픽셀/60Hz/혼잡장면및글로벌counter고갈이후정상성을검증하지않음.','각파트수/recordpointer/순서/실제packet기록·끝주소/guard는확인했지만packet래스터화로이미지를비교하지않음.','near-capacity는필요조건등호1000/1024에서정상종료를확인하는독립fixture이며게임이이상태에도달한다는주장이아님.'],'game_process_opened':False,'resource_or_saves_modified':False}
report['renderer_memory_observer']=OBSERVER
report['guard_method']='실행전후 두 전체pool의할당구간밖/전후64B exact; 실제cursor·기록순서·OT commit검사'
(O/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf8');(O/'executed_addresses.json').write_text(json.dumps([hex(p)for p in pcs],indent=2)+'\n','utf8');print(json.dumps({'passed':True,'cases':len(rows),'report_sha256':digest(O/'report.json')}))
