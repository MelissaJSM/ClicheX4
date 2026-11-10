"""Isolated original-US MIPS RAM-loader/directory/object/decode/queue checks.

Only evidence is written. No process, EXE, ARC, disc, or save is modified.
"""
from pathlib import Path
import argparse,collections,hashlib,json,struct,sys
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from scripts.c01_audio_build import read_disc
from scripts.prepare_riko_ui import entry
from src.psx_player import bank_offsets,graphics_bank,decode_stream
from unicorn import Uc,UC_ARCH_MIPS,UC_MODE_MIPS32,UC_MODE_LITTLE_ENDIAN,UC_HOOK_CODE,UC_HOOK_MEM_WRITE
from unicorn import mips_const as m
D=Path(__file__).parent
BIN=ROOT/'out/ver_buki_riko/sprite_style_unification_20261107_v14/shibuki_riko.bin'
BIN_SHA='b1e00232f8a62bea766e7b40dded110b0c2e66a2fbd2795725347510a0af581d'
US=ROOT/'MegaMan X4.bin'
US_SHA='3ceab06ac99add4035f912188bcbf5b16c02056f46a33d38ff0c8dbce6cb613b'
GADDR=0x1789a0;CADDR=0x1b0000;OBJ=0x1418c8;QUEUE=0x1659d0;STOP=0x80008000
sha=lambda b:hashlib.sha256(b).hexdigest()
def digest(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def require(ok,why):
    if not ok:raise ValueError(why)
def word(u,a):return struct.unpack('<I',u.mem_read(a,4))[0]
def put(u,a,v):u.mem_write(a,struct.pack('<I',v))
def exe_at(exe,a,n):return exe[a-struct.unpack_from('<I',exe,24)[0]+2048:a-struct.unpack_from('<I',exe,24)[0]+2048+n]

# Unmodified initialization blocks, ending immediately after composition binding.
# Bank1/4 are physical aliases of the actual X effect owners2/5.
BLOCKS={2:(0x80093038,0x8009308c,10),3:(0x80093d9c,0x80093df0,11),
 5:(0x80095270,0x800952c8,13),6:(0x80095874,0x800958d4,14),
 7:(0x8009635c,0x800963b8,15),8:(0x80096ec8,0x80096f20,16),
 9:(0x800978fc,0x80097950,17)}

def main(args):
    args.candidate=args.candidate.resolve();args.out=args.out.resolve()
    require(args.out.resolve().is_relative_to(D.resolve()),'Evidence must remain under zero_audit')
    require(not args.out.exists(),'Fresh evidence folder required')
    require(digest(BIN)==BIN_SHA and digest(US)==US_SHA,'Disc input hash mismatch')
    now,_=read_disc(BIN,('SLUS_005.61','PL00_U.ARC'));orig,_=read_disc(US,('SLUS_005.61',))
    exe=now['SLUS_005.61'];original=orig['SLUS_005.61'];arc=args.candidate.read_bytes()
    require(sha(arc)==args.candidate_sha256,'Candidate hash mismatch')
    gfx,parts=entry(arc,2),entry(arc,3);oldg=entry(now['PL00_U.ARC'],2)
    gbases=bank_offsets(gfx,allow_aliases=True);cbases=bank_offsets(parts)
    require(len(gfx)==len(oldg)==186228 and len(gbases)==14,'Entry2 shape mismatch')
    require(gbases[1]==gbases[2] and gbases[4]==gbases[5],'Physical alias policy changed')
    require(GADDR+len(gfx)<CADDR and CADDR+len(parts)<0x1ff000,'Isolated resource memory overlap')
    tables=json.loads((ROOT/'work/sprite_consistency_20261105/coverage/ver_buki_riko/x_animations.json').read_text('utf8'))
    frame_steps={}
    for anim in tables['animations']:
        ptr=struct.unpack('<I',exe_at(exe,0x80119df0+4*anim['id'],4))[0]
        require(ptr==int(anim['address'],16),'Animation pointer evidence stale')
        for step in anim['steps']:
            require(exe_at(exe,int(step['address'],16),4).hex()==step['bytes'],'Animation step evidence stale')
            frame_steps.setdefault(step['frame'],(anim['id'],step['position']))
    capsule_types={}
    for typ in range(5):
        idx=exe_at(exe,0x8010d414+typ,1)[0]
        require(idx<4,'Capsule lookup range changed');capsule_types.setdefault(10+idx,typ)
    require(set(capsule_types)=={10,11,12,13},'Capsule lookup coverage incomplete')
    executed=set();rows=[];stats=collections.Counter()

    def create():
        u=Uc(UC_ARCH_MIPS,UC_MODE_MIPS32|UC_MODE_LITTLE_ENDIAN)
        u.mem_map(0,0x200000);u.mem_map(0x1f800000,0x1000)
        base,size=struct.unpack_from('<II',exe,24);u.mem_write(base&0x1fffffff,exe[2048:2048+size])
        u.mem_write(GADDR,gfx);u.mem_write(CADDR,parts)
        u.mem_write(OBJ,bytes(228));u.reg_write(m.UC_MIPS_REG_SP,0x801ff000)
        control={'stop':STOP}
        def trace(cpu,addr,size,data):
            if addr==control['stop']:cpu.emu_stop();return
            executed.add(addr)
        u.hook_add(UC_HOOK_CODE,trace)
        def run(start,end=STOP):
            control['stop']=end;u.reg_write(m.UC_MIPS_REG_RA,STOP)
            u.emu_start(start,0,count=1000000)
            require(u.reg_read(m.UC_MIPS_REG_PC)==end,f'Native path did not finish {start:08x}: {u.reg_read(m.UC_MIPS_REG_PC):08x}')
        # Real RAM-entry completion logic stores the pointer into the EXE table's
        # destination. Only loader input state is seeded, never bank pointers.
        for kind,address,data,scratch in ((2,GADDR,gfx,0x1f800014),(3,CADDR,parts,0x1f80001c)):
            put(u,0x137cd4,kind);put(u,0x137dc4,0x80000000+address);put(u,0x137dc8,len(data))
            run(0x80014040,0x80014094)
            require(word(u,scratch)==0x80000000+address,'Native RAM loader bound wrong entry')
            require(word(u,0x137dc4)==0x80000000+address+len(data),'Native RAM loader end wrong')
        return u,run

    def native_case(bankno,f,observe):
        n=f['index'];u,run=create();alias={1:2,4:5}.get(bankno,bankno)
        pointer_origin='native_effect_initializer_block';position=None
        u.reg_write(m.UC_MIPS_REG_S0,0x80000000+OBJ);u.reg_write(m.UC_MIPS_REG_A0,0x80000000+OBJ)
        if bankno==0:
            put(u,OBJ+0x30,0x80119df0)
            selected=frame_steps.get(n,frame_steps[0]);aid,pos=selected
            u.reg_write(m.UC_MIPS_REG_A1,aid);u.reg_write(m.UC_MIPS_REG_A2,pos)
            run(0x8003516c)
            require(word(u,OBJ+0x34)==struct.unpack('<I',exe_at(exe,0x80119df0+4*aid,4))[0]+4*pos,'Native animation cursor mismatch')
            if n in frame_steps:
                require(u.mem_read(OBJ+0x47,1)==bytes([n]),'Native frame selection mismatch')
                position={'animation':aid,'position':pos};pointer_origin='complete_native_player_frame_wrapper'
            else:pointer_origin='native_player_wrapper_then_frame_not_in_traced_table_fixture'
            pb=0
        elif alias in BLOCKS:
            start,end,pb=BLOCKS[alias]
            # Block7 calls the actual set_animation function; a0 is the object.
            run(start,end)
        else:
            typ=capsule_types[bankno];u.mem_write(OBJ+2,bytes([typ]))
            # Inputs at this block follow allocation slot0 (a2=0,t0=0,a1=24).
            u.reg_write(m.UC_MIPS_REG_A1,24);u.reg_write(m.UC_MIPS_REG_A2,0);u.reg_write(m.UC_MIPS_REG_T0,0)
            run(0x800c6f20,0x800c6f98);pb=bankno+8
            pointer_origin='native_capsule_type_lookup_and_initializer_block'
        expected_gp=0x80000000+GADDR+gbases[bankno];expected_cp=0x80000000+CADDR+cbases[pb]
        require(word(u,OBJ+0x38)==expected_gp,'Native graphics pointer mismatch')
        require(word(u,OBJ+0x3c)==expected_cp,'Native composition pointer mismatch')
        # Every directory/header reference is covered. Frames absent from the
        # selected real animation table use a frame-byte fixture after native
        # pointer initialization; this is not a gameplay reachability assertion.
        if bankno!=0 or n not in frame_steps:u.mem_write(OBJ+0x47,bytes([n]))
        u.mem_write(OBJ+0x48,bytes([255 if n!=255 else 254]))
        slot=3 if bankno==0 else 0;buf=0x16dea8 if slot==3 else 0x16eea8
        u.mem_write(OBJ+0x49,bytes([slot]));put(u,0x141f68,0x80000000+QUEUE);u.mem_write(QUEUE,bytes(108))
        raw=decode_stream(gfx,f['offset'],f['limit'],f['tile_count']*128).data
        capacity=4096 if bankno==0 else 6144
        require(len(raw)<=capacity,'Unexpected native decoded span')
        guard=bytes((i*73+11)&255 for i in range(capacity+128));u.mem_write(buf-64,guard)
        writes=[]
        if observe:
            def watch(cpu,access,address,size,value,data):writes.append((address&0x1fffffff,size))
            u.hook_add(UC_HOOK_MEM_WRITE,watch,begin=buf-64,end=buf+capacity+63)
        for reg,value in ((m.UC_MIPS_REG_A0,0x80000000+OBJ),(m.UC_MIPS_REG_A1,320),(m.UC_MIPS_REG_A2,0 if bankno==0 else 32)):
            u.reg_write(reg,value)
        run(0x80015ecc)
        after=bytes(u.mem_read(buf-64,len(guard)))
        require(after[64:64+len(raw)]==raw,'Native decoded raw mismatch')
        require(after[:64]==guard[:64] and after[64+len(raw):]==guard[64+len(raw):],'Native span guard changed')
        if observe:require(writes and min(x for x,z in writes)==buf and max(x+z for x,z in writes)==buf+len(raw),'Native write span mismatch')
        output=bytearray();rects=[]
        for i in range(9):
            x,y,w,h,ptr=struct.unpack('<hhhhI',u.mem_read(QUEUE+12*i,12))
            if not ptr:break
            at=ptr&0x1fffffff;size=w*h*2
            require(buf<=at<=buf+capacity and at+size<=buf+capacity,'GPU queue outside expected decoded span')
            output.extend(u.mem_read(at,size));rects.append({'x':x,'y':y,'width_words':w,'height':h,'bytes':size})
        require(bytes(output)==raw,'Native GPU queue bytes mismatch')
        require(word(u,0x141f68)==0x80000000+QUEUE+12*len(rects),'Native GPU queue cursor mismatch')
        return {'bank':bankno,'ref':n,'tiles':f['tile_count'],'decoded_sha256':sha(raw),'graphics_pointer':hex(expected_gp),'composition_pointer':hex(expected_cp),
          'directory_owner':alias,'pointer_origin':pointer_origin,'native_animation_selection':position,'queue':rects,'guard_exact':True,
          'effect_span_limit_is_fixture_not_game_allocation_proof':bankno!=0}

    for bankno in range(14):
        bank=graphics_bank(gfx,bankno,allow_bank_aliases=True)
        for f in bank['frames']:
            r=native_case(bankno,f,False);r2=native_case(bankno,f,True)
            require(r==r2,'Memory observer changed native result');rows.append(r)
            stats['references']+=1;stats['native_decode_calls']+=2;stats[r['pointer_origin']]+=1
        print(json.dumps({'bank':bankno,'references':len(bank['frames']),'complete':True}),flush=True)
    require(len(rows)==508,'PL00 full reference coverage changed')
    for pc in executed:
        require(exe_at(exe,pc,4)==exe_at(original,pc,4),'Executed instruction differs from original US')
    # Bind all actual instructions, not only the first bytes of a function.
    pcs=sorted(executed);digest_data=b''.join(struct.pack('<I',p)+exe_at(exe,p,4) for p in pcs)
    result={'passed':True,'scope':'로컬 원MIPS RAM-loader→directory→객체주소→decode→GPU 업로드 큐 검사. 게임 실기 아님.',
      'candidate_path':args.candidate.relative_to(ROOT).as_posix(),'candidate_sha256':sha(arc),'entry2_sha256':sha(gfx),'entry2_size':len(gfx),'bank_offsets':gbases,
      'source_bin':BIN.relative_to(ROOT).as_posix(),'source_bin_sha256':BIN_SHA,'exe_sha256':sha(exe),'original_us_bin_sha256':US_SHA,
      'stats':dict(stats),'executed_unique_instructions':len(pcs),'executed_address_and_bytes_sha256':sha(digest_data),'all_executed_instructions_original_US_exact':True,
      'loaders_native':True,'python_bank_pointer_injection':False,'code_patches_or_stubs':False,'memory_observer_results_identical':True,
      'references':rows,'initializer_blocks':{str(k):{'start':hex(s),'stop_before':hex(e),'parts_bank':p}for k,(s,e,p)in BLOCKS.items()},
      'capsule_type_lookup':capsule_types,'capsule_initializer_block':{'start':'0x800c6f20','stop_before':'0x800c6f98','allocator_result_fixture':{'a1':24,'a2':0,'t0':0}},
      'loader_block':{'start':'0x80014040','stop_before':'0x80014094','entries':[2,3]},
      'limits':['CD 읽기·전체 엔티티 spawn·물리·실제 GPU는 재현하지 않는다.',
       '효과 초기화는 원래 주소계산 기본블록의 시작 객체 상태를 주입한 뒤 실행하며 전체 생성함수 실행이라고 세지 않는다.',
       '모든 효과 및 추적한144표에 없는105/161/190 ref의 frame byte는 주소 초기화 후 독립시험 입력이다. 사용하지 않는그림 또는 실제게임순서라는 판정이 아니다.',
       '원래48타일 효과의 단일 디코드/전송 범위를 확인했으나 동시 객체 버퍼 할당·수명은 본 검사 밖이다.',
       'fresh-load 조건이다. 기존 세이브스테이트 객체의 오래된 cached pointer를 새 자원에 재사용하지 않는다.'],
      'game_process_opened':False,'resources_or_saves_written':False}
    args.out.mkdir(parents=True)
    (args.out/'executed_addresses.json').write_text(json.dumps([hex(p)for p in pcs],indent=2)+'\n','utf8')
    q=args.out/'report.json';q.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n','utf8')
    print(json.dumps({'passed':True,'report':str(q),'sha256':digest(q),'stats':dict(stats)}))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--candidate',type=Path,required=True);p.add_argument('--candidate-sha256',required=True);p.add_argument('--out',type=Path,required=True);main(p.parse_args())
