"""Read original/current EXE code; no resource transformation or game mutation."""
from pathlib import Path
import hashlib,json,struct,sys
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT))
from scripts.c01_audio_build import read_disc
from scripts.prepare_riko_ui import entry
from src.psx_player import bank_offsets,graphics_bank,decode_stream
from capstone import Cs,CS_ARCH_MIPS,CS_MODE_MIPS32,CS_MODE_LITTLE_ENDIAN
OUT=Path(__file__).parent/'pl00_bank_relocation_audit01'
OUT.mkdir(exist_ok=True)
sha=lambda b:hashlib.sha256(b).hexdigest()
def file_sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(8388608),b''):h.update(b)
    return h.hexdigest()
current=ROOT/'out/ver_buki_riko/sprite_style_unification_20261107_v14/shibuki_riko.bin'
original=ROOT/'MegaMan X4.bin'
expected={current:'b1e00232f8a62bea766e7b40dded110b0c2e66a2fbd2795725347510a0af581d',original:'3ceab06ac99add4035f912188bcbf5b16c02056f46a33d38ff0c8dbce6cb613b'}
for p,h in expected.items():assert file_sha(p)==h,('input hash mismatch',p)
cur,recs=read_disc(current,('SLUS_005.61','PL00_U.ARC'))
old,_=read_disc(original,('SLUS_005.61','PL00_U.ARC'))
exe=cur['SLUS_005.61'];orig=old['SLUS_005.61']
base=struct.unpack_from('<I',exe,0x18)[0]
def at(data,start,end):return data[start-base+2048:end-base+2048]
md=Cs(CS_ARCH_MIPS,CS_MODE_MIPS32|CS_MODE_LITTLE_ENDIAN)
def lines(data,start,end):return [f'{x.address:08X} {bytes(x.bytes).hex()} {x.mnemonic:8} {x.op_str}' for x in md.disasm(at(data,start,end),start)]
ranges={'loader':(0x80013e68,0x80014140),'decompress_player':(0x80015ecc,0x80016004),'decompress_stream':(0x80016ff4,0x800170b0),'player_animation':(0x800350a4,0x80035240),'player_spawn':(0x80035240,0x80035694),'capsule':(0x800c6edc,0x800c7168),'static_vram_loader':(0x800142bc,0x80014514)}
rows={}
for name,(start,end) in ranges.items():
    b=at(exe,start,end)
    rows[name]={'start':hex(start),'end':hex(end),'sha256':sha(b),'original_us_identical':b==at(orig,start,end)}
    (OUT/f'{name}.asm.txt').write_text('\n'.join(lines(exe,start,end))+'\n',encoding='utf8')
# Enumerate every direct scratchpad base construction in the loadable EXE.
scratch=[]
size=struct.unpack_from('<I',exe,0x1c)[0]
for i in range(2048,min(len(exe),2048+size),4):
    word=struct.unpack_from('<I',exe,i)[0]
    if word>>26==15 and word&0xffff==0x1f80:
        addr=base+i-2048
        scratch.append({'address':hex(addr),'context':lines(exe,max(base,addr-8),min(base+size,addr+64))})
(OUT/'scratchpad_contexts.json').write_text(json.dumps(scratch,indent=2),encoding='utf8')
# Local constant propagation only; do not claim whole-program completeness.
direct={}
for row in scratch:
    start=int(row['address'],16);known={0:0};deadline=None
    for addr in range(start,min(start+96,base+size),4):
        w=struct.unpack('<I',at(exe,addr,addr+4))[0]
        op=w>>26;rs=(w>>21)&31;rt=(w>>16)&31;rd=(w>>11)&31;imm=w&65535
        simm=imm if imm<32768 else imm-65536
        if op==35:
            effective=(known[rs]+simm)&0xffffffff if rs in known else None
            if effective==0x1f800014:
                direct[addr]={'load_address':hex(addr),'context':lines(exe,addr-8,addr+100),'original_us_identical':at(exe,addr-8,addr+100)==at(orig,addr-8,addr+100)}
            known.pop(rt,None)
        elif op==15:known[rt]=imm<<16
        elif op in (9,13):
            value=((known[rs]+simm)&0xffffffff if op==9 else known[rs]|imm) if rs in known else None
            if value is None:known.pop(rt,None)
            else:known[rt]=value
        elif op==0:
            fn=w&63
            if fn in (33,37) and rs in known and rt in known:
                known[rd]=((known[rs]+known[rt])&0xffffffff) if fn==33 else known[rs]|known[rt]
            elif fn not in (8,9,12,13):known.pop(rd,None)
        elif op in (32,33,34,36,37,38,8,10,11,12,14):known.pop(rt,None)
        known[0]=0
        if deadline==addr:break
        if op in (1,2,3,4,5,6,7) or op==0 and (w&63) in (8,9):deadline=addr+4
for addr,row in direct.items():
    row['graphics_bank_ids']=([10,11,12,13] if addr==0x800c6f38 else [0] if addr==0x800355e8 else [])
    w=struct.unpack('<I',at(exe,addr,addr+4))[0];gp=(w>>16)&31
    if not row['graphics_bank_ids']:
        for a in range(addr+4,addr+56,4):
            q=struct.unpack('<I',at(exe,a,a+4))[0]
            if q>>26==35 and (q>>21)&31==gp:
                offset=q&65535
                if offset<56 and offset%4==0:row['graphics_bank_ids']=[offset//4]
                break
(OUT/'direct_gfx_pointer_reads.json').write_text(json.dumps(list(direct.values()),indent=2),encoding='utf8')
gfx=entry(cur['PL00_U.ARC'],2);bs=bank_offsets(gfx,allow_aliases=True)
banks=[]
for n in range(len(bs)):
    try:
        b=graphics_bank(gfx,n,allow_bank_aliases=True)
        fs=[]
        for f in b['frames']:
            d=decode_stream(gfx,f['offset'],f['limit'],f['tile_count']*128)
            fs.append({'ref':f['index'],'tiles':f['tile_count'],'stream_relative_offset':f['offset']-b['base'],'decoded_sha256':sha(d.data)})
        banks.append({'bank':n,'base':b['base'],'end':b['end'],'frames':fs})
    except Exception as e:banks.append({'bank':n,'error':str(e)})
result={'scope':'실제 원US/현재BR14 EXE 및 PL00 주소 읽기. 재배치 후보 생성·적용·실기 실행 없음.','sources':{current.relative_to(ROOT).as_posix():{'exe_sha256':sha(exe),'arc_sha256':sha(cur['PL00_U.ARC'])},original.relative_to(ROOT).as_posix():{'exe_sha256':sha(orig),'arc_sha256':sha(old['PL00_U.ARC'])}},'load_base':hex(base),'load_size':size,'code':rows,'scratchpad_base_constructions':len(scratch),'entry2_length':len(gfx),'entry2_sha256':sha(gfx),'bank_offsets':bs,'banks':banks}
(OUT/'native_inventory.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8')
result['disc_hashes']={p.relative_to(ROOT).as_posix():h for p,h in expected.items()}
result['loader_destination_table']=[hex(x) for x in struct.unpack('<22I',at(exe,0x800f15bc,0x800f1614))]
assert result['loader_destination_table'][2]=='0x1f800014'
result['loader_handler_table']=[hex(x) for x in struct.unpack('<4I',at(exe,0x80010014,0x80010024))]
result['direct_gfx_pointer_reads']=len(direct)
assert all(r['original_us_identical'] for r in direct.values())
assert all('error' not in b for b in banks)
(OUT/'native_inventory.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps({'ranges':rows,'scratchpad_contexts':len(scratch),'bank_count':len(bs),'entry2_length':len(gfx)},ensure_ascii=False))
