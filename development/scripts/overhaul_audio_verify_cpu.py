"""실제 US 사운드 명령 디스패처 실행. SPU 하드웨어/청취 검증은 별도다."""
import hashlib,json,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from unicorn import Uc,UC_ARCH_MIPS,UC_MODE_MIPS32,UC_MODE_LITTLE_ENDIAN,UC_HOOK_CODE
from unicorn import mips_const as m
from scripts.discover_inputs import DiscReader,psx_arc
from scripts.inventory_riko_voice import parse_bank
from src.psx_spu_audio import decode_spu

D=ROOT/'work/overhaul_20261105/audio';P=D/'prepared'
def sha(b):return hashlib.sha256(b).hexdigest()
def banks(a):
    result={};es=psx_arc(a)
    for e in es:
        h=a[e['offset']:e['offset']+e['size']]
        if len(h)<8:continue
        packed,length=struct.unpack_from('<II',h);vo=packed&0xffffff;slot=packed>>24
        if h[vo:vo+4]!=b'pBAV':continue
        # Stage base archives may put unrelated entries between VH and VB.
        candidates=[v for v in es if int(v['type'],16)>>16==2
                    and (int(v['type'],16)>>8)&255==slot and v['size']==length]
        if len(candidates)!=1:raise ValueError('Missing or ambiguous sound body')
        v=candidates[0];b=a[v['offset']:v['offset']+v['size']]
        q=parse_bank(h,b,False)
        if slot in result:raise ValueError('Duplicate sound bank slot')
        result[slot]=(h,b,q)
    return result

def run(exe,loaded,slot,command):
    u=Uc(UC_ARCH_MIPS,UC_MODE_MIPS32|UC_MODE_LITTLE_ENDIAN);u.mem_map(0,0x200000)
    load=struct.unpack_from('<I',exe,0x18)[0]&0x1fffffff;u.mem_write(load,exe[2048:])
    for s,(h,b,q) in loaded.items():
        at=0x180000+s*0x2000;u.mem_write(at,h)
        u.mem_write(0x141ee8+s*4,struct.pack('<I',0x80000000|at+q['vab_offset']))
        u.mem_write(0x141f50+s*4,struct.pack('<I',0x80000000|at+8))
        u.mem_write(0x13e198+s,bytes([s]))
    u.mem_write(0x139234,bytes([255])*24)
    for at in (0xdfac0,0xdfcfc,0xdbf34):u.mem_write(at,struct.pack('<III',0x24020000,0x03e00008,0))
    stop=0x80008000;calls=[]
    preserved={m.UC_MIPS_REG_SP:0x801ff000,m.UC_MIPS_REG_RA:stop}
    for n,reg in enumerate((m.UC_MIPS_REG_S0,m.UC_MIPS_REG_S1,m.UC_MIPS_REG_S2,m.UC_MIPS_REG_S3,m.UC_MIPS_REG_S4,m.UC_MIPS_REG_S5,m.UC_MIPS_REG_S6,m.UC_MIPS_REG_S7,m.UC_MIPS_REG_FP)):preserved[reg]=0x123400+n
    for reg,val in preserved.items():u.reg_write(reg,val)
    for reg,val in ((m.UC_MIPS_REG_A0,slot),(m.UC_MIPS_REG_A1,command),(m.UC_MIPS_REG_A2,0)):u.reg_write(reg,val)
    def hook(cpu,address,size,data):
        if address==stop:cpu.emu_stop();return
        if address&0x1fffffff==0xdfac0:
            bank,program,tone=[cpu.reg_read(r) for r in (m.UC_MIPS_REG_A0,m.UC_MIPS_REG_A1,m.UC_MIPS_REG_A2)]
            h,_,q=loaded[bank];assert program<q['program_count'] and tone<16
            off=q['vab_offset']+32+128*16+(program*16+tone)*32
            cpu.mem_write(cpu.reg_read(m.UC_MIPS_REG_A3)&0x1fffffff,h[off:off+32])
        elif address&0x1fffffff==0xdfcfc:
            channel,bank,program,tn=[cpu.reg_read(r) for r in (m.UC_MIPS_REG_A0,m.UC_MIPS_REG_A1,m.UC_MIPS_REG_A2,m.UC_MIPS_REG_A3)]
            h,b,q=loaded[bank];off=q['vab_offset']+32+128*16+(program*16+tn)*32;t=h[off:off+32]
            wave_id=struct.unpack_from('<H',t,22)[0];assert 1<=wave_id<=q['wave_count']
            w=q['waves'][wave_id-1];raw=b[w['body_offset']:w['body_offset']+w['bytes']]
            pcm=decode_spu(raw).pcm;sp=cpu.reg_read(m.UC_MIPS_REG_SP)&0x1fffffff
            note,fine,left,right=struct.unpack('<IIII',cpu.mem_read(sp+16,16))
            calls.append(dict(channel=channel,bank=bank,program=program,tone=tn,wave=wave_id,note=note,fine=fine,left=left,right=right,pcm_nonzero=any(pcm),tone_volume=t[2],center=t[4],wave_sha256=sha(raw)))
    u.hook_add(UC_HOOK_CODE,hook);u.emu_start(0x8001540c,0,count=30000)
    assert u.reg_read(m.UC_MIPS_REG_PC)==stop and all(u.reg_read(r)==v for r,v in preserved.items())
    return calls

def main():
    p=ROOT/'MegaMan X4.bin'
    with p.open('rb') as f:
        d=DiscReader(f,p.stat().st_size);r=next(r for r in d.inspect()['files'] if r['path']=='/SLUS_005.61;1');exe=d.read(r['lba'],r['size'])
    rows=[]
    for project in ('ver_buki_riko','ver_rin_nana'):
        proposal=json.loads((P/project/'proposal.json').read_text(encoding='utf8'))
        for rec in proposal['files'].values():assert sha((ROOT/rec['path']).read_bytes())==rec['after']
        for player in ('PL00_U.ARC','PL01_U.ARC','PL02_U.ARC'):
            loaded=banks((P/project/player).read_bytes())
            for command in range(13):
                calls=run(exe,loaded,3,command);assert calls
                if command in (0,1,12):assert all(c['bank']==0 and c['pcm_nonzero'] for c in calls)
                elif command==10 and player=='PL01_U.ARC':assert all(c['bank']==1 and c['pcm_nonzero'] for c in calls)
                else:assert all(c['bank']==3 and not c['pcm_nonzero'] for c in calls)
                rows.append(dict(project=project,player=player,source_slot=3,command=command,calls=calls))
            for stage,commands in ((5,(178,)),(6,(196,199)),(7,(190,))):
                for name in (f'ST{stage}_1_1.ARC',f'ONPARE{stage}.ARC'):
                    case={**loaded,**banks((P/project/name).read_bytes())}
                    for command in commands:
                        calls=run(exe,case,2,command);assert calls and all(c['pcm_nonzero'] and c['tone_volume']>0 and c['left']>0 and c['right']>0 for c in calls)
                        if stage==6:assert len(calls)==1 and calls[0]['bank']==3 and calls[0]['tone']==(14 if command==196 else 15)
                        else:assert all(c['bank']==2 for c in calls)
                        rows.append(dict(project=project,player=player,boss=name,source_slot=2,command=command,calls=calls))
    proof=dict(native_function='0x8001540C',command_decoder='0x800154E8',native_code_sha256=sha(exe[0x1540c-0x10000+2048:0x157ac-0x10000+2048]),tests=len(rows),all_cases_passed=True,caller_registers_preserved=True,hardware_spu_sdk_calls_mocked=True,game_runtime_verified=False,human_listening_verified=False,cases=rows)
    (D/'cpu_verification.json').write_text(json.dumps(proof,indent=2),encoding='utf8');print(json.dumps({k:v for k,v in proof.items() if k!='cases'}))
if __name__=='__main__':main()
