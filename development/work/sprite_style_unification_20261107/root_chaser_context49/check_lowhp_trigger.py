"""저체력 자세 진입 조건을 변경 없는 미국판 MIPS 코드로 격리 실행한다."""
from pathlib import Path
import hashlib,json,struct,sys
from unicorn import Uc,UC_ARCH_MIPS,UC_MODE_MIPS32,UC_MODE_LITTLE_ENDIAN,UC_HOOK_CODE
from unicorn import mips_const as m
O=Path(__file__).resolve().parent;ROOT=O.parents[2];sys.path.insert(0,str(ROOT))
from scripts.discover_inputs import DiscReader
def read_exe(path):
    with path.open('rb')as f:
        d=DiscReader(f,path.stat().st_size);q=next(q for q in d.inspect()['files'] if q['path']=='/SLUS_005.61;1');return d.read(q['lba'],q['size'])
sha=lambda b:hashlib.sha256(b).hexdigest()
exe=read_exe(ROOT/'out/ver_rin_nana/sprite_style_unification_20261107_v43/rin_nana.bin')
assert sha(exe)=='93a8f0cab28034bd7d5b93fe4362c7c56c8c2bfba5ccb764e7bf547a02ae1616'
orig=read_exe(ROOT/'MegaMan X4.bin');off=lambda a:a-0x80010000+0x800
blocks=[]
for lo,hi in ((0x80036534,0x800365a4),(0x80038678,0x80038748)):
    code=exe[off(lo):off(hi)];assert code==orig[off(lo):off(hi)];blocks.append({'start':hex(lo),'end':hex(hi),'sha256':sha(code),'original_equal':True})
PLAYER=0x1418c8;calls=[]
def run(addr,hp,maxhp,animation=5,attack_ended=0,shot_fired=0):
    u=Uc(UC_ARCH_MIPS,UC_MODE_MIPS32|UC_MODE_LITTLE_ENDIAN);u.mem_map(0,0x200000);u.mem_write(0x10000,exe[0x800:])
    p=bytearray(228);p[0]=1;p[2]=0;p[0x17]=animation;p[0x5c]=hp;p[0x8f]=shot_fired;p[0x90]=attack_ended
    u.mem_write(PLAYER,bytes(p));u.mem_write(0x172206,bytes([maxhp]));u.reg_write(m.UC_MIPS_REG_SP,0x801ff000);u.reg_write(m.UC_MIPS_REG_RA,0x80008000);u.reg_write(m.UC_MIPS_REG_A0,0x801418c8)
    trace=[];result=[]
    def hook(cpu,at,size,user):
        trace.append(at)
        if at in (0x800350a4,0x80015dc8,0x80038748):
            result.append({'callee':hex(at),'animation':cpu.reg_read(m.UC_MIPS_REG_A1)if at==0x800350a4 else None});cpu.emu_stop()
        elif at==0x80008000:cpu.emu_stop()
    u.hook_add(UC_HOOK_CODE,hook);u.emu_start(addr,0,count=2000);assert len(result)==1,(addr,result,hex(u.reg_read(m.UC_MIPS_REG_PC)))
    q={'function':hex(addr),'hp':hp,'max_hp':maxhp,'input_animation':animation,'attack_ended':attack_ended,'shot_fired':shot_fired,**result[0],'instructions':len(trace)};calls.append(q);return q
for maximum in (24,32,40,48):
    for hp in range(1,maximum+1):
        q=run(0x80036534,hp,maximum);assert q['animation']==(6 if hp<maximum//3 else 5)
for hp,anim,ended,expected in ((15,5,0,None),(15,5,1,6),(16,6,0,5),(15,6,0,None),(48,5,1,5)):
    q=run(0x80038678,hp,48,animation=anim,attack_ended=ended);assert q['animation']==expected
    if expected is None:assert q['callee']=='0x80015dc8'
q=run(0x80038678,15,48,attack_ended=1,shot_fired=1);assert q['callee']=='0x80038748'
cfg=json.loads((ROOT/'config/shibuki_x_us.json').read_text('utf8'));a=struct.unpack_from('<I',exe,off(cfg['animation_table_address'])+6*4)[0];i=0;seen=set();seq=[]
while i not in seen:
    seen.add(i);t,e,rel,ref=struct.unpack_from('<bbbB',exe,off(a)+i*4);seq.append({'index':i,'ticks':t,'relative':rel,'ref':ref});i+=rel
assert {q['ref']for q in seq}==set(range(120,126))
report={'passed':True,'current_EXE_sha256':sha(exe),'original_code_blocks':blocks,'cases':calls,'case_count':len(calls),'lowhp_animation':6,'animation_sequence':seq,'game_process_started':False,'process_memory_written':False,'original_or_user_files_modified':False,'real_MIPS_condition_executed':True,'live_gameplay_verified':False,'renderer_called':False,'findings':['최대 체력48에서는15 이하에서 저체력 애니메이션6을 선택하고,16 이상은 일반 대기5를 선택한다.','일반 대기5에서 체력 값만 낮아지면 player_idle_animate는6으로 전환하지 않는다. 대기 재진입 또는 공격 종료 경로에서 player_set_idle_animation 호출이 필요하다.','사격 발동은 공격 종료/저체력 대기 선택보다 우선한다.'],'limitations':['분리된 CPU의 입력 상태를 구성하고, 그리기/애니메이션 호출 경계에서 멈춘 검사다. 실제 플레이에서의 발동이나 화면 표시 증거가 아니다.']}
# Korean project notes are maintained separately; identifiers and machine evidence stay stable.
(O/'lowhp_trigger_native.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf8')
print(json.dumps({'passed':True,'cases':len(calls),'lowhp_refs':[q['ref']for q in seq]}))
