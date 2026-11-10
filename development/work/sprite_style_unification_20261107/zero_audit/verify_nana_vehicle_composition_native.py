"""Read-only original-US loader and armor-composition directory lookup test."""
from pathlib import Path
import hashlib,json,struct,sys
ROOT=Path(__file__).resolve().parents[3];D=Path(__file__).parent;B=D.parent
sys.path.insert(0,str(ROOT))
from scripts.c01_audio_build import read_disc
from scripts.prepare_riko_ui import entry
from src.psx_player import bank_offsets,graphics_bank,decode_stream,composition_frame
from unicorn import Uc,UC_ARCH_MIPS,UC_MODE_MIPS32,UC_MODE_LITTLE_ENDIAN,UC_HOOK_CODE
from unicorn import mips_const as m

O=D/'nana_vehicle_composition_native01'
NEW=B/'root_nana_vehicle/packed_vehicle03/PL00_U.ARC'
OLD=B/'root_nana_return/packed_return03/PL00_U.ARC'
BIN=ROOT/'out/ver_rin_nana/sprite_style_unification_20261107_v34/rin_nana.bin'
US=ROOT/'MegaMan X4.bin'
sha=lambda b:hashlib.sha256(b).hexdigest()
def digest(p):
    with p.open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
def require(ok,why):
    if not ok:raise ValueError(why)
def word(u,a):return struct.unpack('<I',u.mem_read(a&0x1fffffff,4))[0]
def put(u,a,v):u.mem_write(a,struct.pack('<I',v))
def exebytes(exe,addr,n=4):
    start=addr-struct.unpack_from('<I',exe,24)[0]+2048;return exe[start:start+n]

require(digest(BIN)=='43b63a99328f4aa4e2aa004e8799834397efe91ff4510a36d4cd6b4dd48445d0','RN34 source mismatch')
require(digest(US)=='3ceab06ac99add4035f912188bcbf5b16c02056f46a33d38ff0c8dbce6cb613b','US source mismatch')
exe=read_disc(BIN,('SLUS_005.61',))[0]['SLUS_005.61']
us=read_disc(US,('SLUS_005.61',))[0]['SLUS_005.61']
new,old=NEW.read_bytes(),OLD.read_bytes()
require(sha(new)=='29f7b9a054ede30562bc4c3a88da96f70a909ad05262b3fd184c566e980454db','Candidate mismatch')
require(sha(old)=='6823c51d79f45beb3eeee8a9a2ec4a73aa1e067c5e1465d4325d6e4cf8c8ebf9','Parent mismatch')
GADDR=0x1789a0;CADDR=0x1b0000;OBJ=0x1418c8;STOP=0x80008000;QUEUE=0x1659d0;BUF=0x16dea8
executed=set();trace_rows=[];decode_rows=[]

def create(data):
    gfx,parts=entry(data,2),entry(data,3)
    require(GADDR+len(gfx)<CADDR and CADDR+len(parts)<0x1ff000,'Isolated allocation overlaps')
    u=Uc(UC_ARCH_MIPS,UC_MODE_MIPS32|UC_MODE_LITTLE_ENDIAN)
    u.mem_map(0,0x200000);u.mem_map(0x1f800000,0x1000)
    at,size=struct.unpack_from('<II',exe,24);u.mem_write(at&0x1fffffff,exe[2048:2048+size])
    u.mem_write(GADDR,gfx);u.mem_write(CADDR,parts);u.mem_write(OBJ,bytes(228))
    u.reg_write(m.UC_MIPS_REG_SP,0x801ff000);control={'stop':STOP}
    def code(cpu,addr,size,user):
        if addr==control['stop']:cpu.emu_stop();return
        executed.add(addr)
    u.hook_add(UC_HOOK_CODE,code)
    def run(start,end=STOP):
        control['stop']=end;u.reg_write(m.UC_MIPS_REG_RA,STOP);u.emu_start(start,0,count=1000000)
        require(u.reg_read(m.UC_MIPS_REG_PC)==end,f'Original path incomplete {start:08x}: {u.reg_read(m.UC_MIPS_REG_PC):08x}')
    # Seed RAM-entry load inputs. Native loader stores scratchpad pointers.
    for kind,ptr,resource,sp in ((2,GADDR,gfx,0x1f800014),(3,CADDR,parts,0x1f80001c)):
        put(u,0x137cd4,kind);put(u,0x137dc4,0x80000000+ptr);put(u,0x137dc8,len(resource))
        run(0x80014040,0x80014094)
        require(word(u,sp)==0x80000000+ptr,'Native loader scratch pointer mismatch')
    return u,run,gfx,parts

# Use the actual animation table and player wrapper to initialize base pointers.
tables=json.loads((ROOT/'work/sprite_consistency_20261105/coverage/ver_rin_nana/x_animations.json').read_text('utf8'))
frame_steps={}
for anim in tables['animations']:
    ptr=struct.unpack('<I',exebytes(exe,0x80119df0+4*anim['id']))[0]
    require(ptr==int(anim['address'],16),'Animation pointer changed')
    for step in anim['steps']:
        require(exebytes(exe,int(step['address'],16)).hex()==step['bytes'],'Animation step changed')
        frame_steps.setdefault(step['frame'],(anim['id'],step['position']))

for tag,data in [('parent',old),('candidate',new)]:
    for n in range(162,175):
        u,run,g,c=create(data);aid,pos=frame_steps[n]
        put(u,OBJ+0x30,0x80119df0)
        u.reg_write(m.UC_MIPS_REG_A0,0x80000000+OBJ);u.reg_write(m.UC_MIPS_REG_A1,aid);u.reg_write(m.UC_MIPS_REG_A2,pos)
        run(0x8003516c)
        require(u.mem_read(OBJ+0x47,1)==bytes([n]),'Original wrapper frame mismatch')
        require(word(u,OBJ+0x38)==0x80000000+GADDR+bank_offsets(g,allow_aliases=True)[0],'Base gfx pointer mismatch')
        require(word(u,OBJ+0x3c)==0x80000000+CADDR+bank_offsets(c)[0],'Base composition pointer mismatch')
        u.mem_write(OBJ+0x48,bytes([255]));u.mem_write(OBJ+0x49,bytes([3]));put(u,0x141f68,0x80000000+QUEUE);u.mem_write(QUEUE,bytes(108))
        guard=bytes((i*73+11)&255 for i in range(4224));u.mem_write(BUF-64,guard)
        for reg,val in [(m.UC_MIPS_REG_A0,0x80000000+OBJ),(m.UC_MIPS_REG_A1,320),(m.UC_MIPS_REG_A2,0)]:u.reg_write(reg,val)
        run(0x80015ecc)
        f=graphics_bank(g,0,allow_bank_aliases=True)['frames'][n];raw=decode_stream(g,f['offset'],f['limit'],f['tile_count']*128).data
        result=bytes(u.mem_read(BUF-64,len(guard)))
        require(result[64:64+len(raw)]==raw and result[:64]==guard[:64]and result[64+len(raw):]==guard[64+len(raw):],'Decode/guard mismatch')
        output=bytearray();rects=[]
        for i in range(9):
            x,y,w,h,p=struct.unpack('<hhhhI',u.mem_read(QUEUE+12*i,12))
            if not p:break
            at=p&0x1fffffff;count=w*h*2
            require(BUF<=at and at+count<=BUF+4096,'Upload queue escaped buffer')
            output.extend(u.mem_read(at,count));rects.append([x,y,w,h])
        require(bytes(output)==raw,'Upload bytes differ')
        decode_rows.append({'source':tag,'ref':n,'animation':aid,'position':pos,'gfx_pointer':hex(word(u,OBJ+0x38)),'base_composition_pointer':hex(word(u,OBJ+0x3c)),'raw_sha256':sha(raw),'queue':rects,'guard_exact':True})
    # Every native armor header/record sequence, including non-target and reserved
    # composition entries. Only frame and layer selector are fixture inputs.
    for pb in (5,6,7,8):
        count=composition_frame(c,pb,0)['bank_frame_count']
        for n in range(count):
            u,run,g,c=create(data)
            u.mem_write(OBJ+0x47,bytes([n]));u.mem_write(OBJ+0x14,b'\xff')
            u.reg_write(m.UC_MIPS_REG_A0,0x80000000+OBJ);u.reg_write(m.UC_MIPS_REG_A1,pb-5);u.reg_write(m.UC_MIPS_REG_A2,0x7843)
            run(0x8002588c,0x80025974)
            sp=u.reg_read(m.UC_MIPS_REG_SP);record_count=word(u,sp+0x40);record_ptr=word(u,sp+0x18)
            base=bank_offsets(c)[pb];header=struct.unpack_from('<I',c,base+n*4)[0];expected=base+(header>>16)*4
            require(record_count==(header&65535)and record_ptr==0x80000000+CADDR+expected,'Native layer directory lookup mismatch')
            records=bytes(u.mem_read(record_ptr&0x1fffffff,record_count*4));require(records==c[expected:expected+record_count*4],'Native selected record bytes mismatch')
            trace_rows.append({'source':tag,'bank':pb,'ref':n,'bank_offset':base,'record_offset':expected,'count':record_count,'records_sha256':sha(records)})
    print(json.dumps({'source':tag,'native_lookup_count':sum(r['source']==tag for r in trace_rows),'native_decode_count':sum(r['source']==tag for r in decode_rows)}),flush=True)
oldrows={(r['bank'],r['ref']):r for r in trace_rows if r['source']=='parent'}
for r in trace_rows:
    if r['source']!='candidate':continue
    q=oldrows[r['bank'],r['ref']]
    if r['ref'] not in range(162,175):require(r['records_sha256']==q['records_sha256']and r['count']==q['count'],'Non-target native records differ')
    require(r['bank_offset']==q['bank_offset']+(40 if r['bank']==6 else 0),'Unexpected native bank movement')
for pc in executed:require(exebytes(exe,pc)==exebytes(us,pc),'Executed opcode differs from original US')
pcs=sorted(executed);signature=b''.join(struct.pack('<I',pc)+exebytes(exe,pc)for pc in pcs)
report={'passed':True,'scope':'원MIPS RAM완료로더→scratchpad→원player wrapper/decode/upload와 원부분아머 renderer의 directory/header/record 조회 구간','candidate':str(NEW.relative_to(ROOT)),'candidate_sha256':sha(new),'parent_sha256':sha(old),'source_bin':str(BIN.relative_to(ROOT)),'source_bin_sha256':digest(BIN),'exe_sha256':sha(exe),'original_us_bin_sha256':digest(US),'decode_calls':len(decode_rows),'composition_lookup_calls':len(trace_rows),'executed_unique_instructions':len(pcs),'executed_bytes_sha256':sha(signature),'all_executed_original_US_exact':True,'python_bank_pointer_injection':False,'code_patches_or_stubs':False,'native_loader_entries':[2,3],'native_lookup_start':'0x8002588c','stop_before':'0x80025974','native_lookup_reads':'scratchpad1f80001c + directory[5+selector] + frame header offset/count','decode_cases':decode_rows,'composition_cases':trace_rows,'resource_hashes_unchanged':sha(NEW.read_bytes())==sha(new)and sha(OLD.read_bytes())==sha(old),'game_process_opened':False,'resources_or_saves_written':False,'runtime_verified':False,'limits':['CD I/O·전체spawn·실제GPU·물리접점 실기가 아니다.','부분아머는실제renderer의원주소조회구간까지실행하며GPU프리미티브 전체작성함수는 실행하지 않았다.','프레임과부분selector는독립fixture.표시마스크전환/동시버퍼수명/게임도달성을증명하지않는다.','loader 입력자원RAM주소만설정했고scratchpad·directory bank pointer·객체38/3c는원코드가계산했다.','fresh-load조건이며오래된세이브상태cached포인터재사용검사는아니다.']}
O.mkdir(exist_ok=False)
(O/'executed_addresses.json').write_text(json.dumps([hex(p)for p in pcs],indent=2)+'\n','utf8')
(O/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf8')
print(json.dumps({'passed':True,'report_sha256':digest(O/'report.json'),'decode_calls':len(decode_rows),'composition_lookup_calls':len(trace_rows),'unique_instructions':len(pcs)}))
