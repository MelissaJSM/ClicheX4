"""귀환156..160에서 포스 획득 플래그가 실제로 없어지는지 최신 MIPS로 검사한다."""
from pathlib import Path
import importlib.util,json,struct,sys,hashlib
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from unicorn import UC_HOOK_CODE,mips_const as m
from scripts.c01_audio_build import read_disc
from scripts.export_x_consistency import Archive,page
from src.psx_disc import file_hash
from scripts.export_sprite_playback import at
SOURCE=ROOT/'out/ver_buki_riko/sprite_reaudit_20261106_v1/shibuki_riko.bin'
SOURCE_SHA='21bee159a1267d56561d4fa15c99ec652780af782fe08a433859c9eb7676099a'
def sha(b):return hashlib.sha256(b).hexdigest()
def need(v,s):
 if not v:raise ValueError(s)
def write(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n','utf8')

def main():
 need(file_hash(SOURCE)==SOURCE_SHA,'Source BIN changed')
 data=read_disc(SOURCE,('SLUS_005.61','PL00_U.ARC'))[0];exe=data['SLUS_005.61'];arc=Archive(data['PL00_U.ARC'])
 original=read_disc(ROOT/'MegaMan X4.bin',('SLUS_005.61',))[0]['SLUS_005.61']
 regions=[(0x80031540,0xA0),(0x80035048,0x5C)]
 for addr,size in regions:need(at(exe,addr,size)==at(original,addr,size),'Return function differs from original')
 spec=importlib.util.spec_from_file_location('native_contracts',ROOT/'work/ultimate_costume_swap_20261105/audit/native_contracts.py');nc=importlib.util.module_from_spec(spec);spec.loader.exec_module(nc)
 PLAYER=nc.PLAYER;ENGINE=nc.ENGINE;RETURN=nc.RETURN
 animptr=struct.unpack('<I',at(exe,0x80119DF0+3*4,4))[0]
 rows=[]
 for armor in range(16):
  for arm in(1,2):
   u=nc.cpu(exe);u.mem_write(PLAYER,bytes(0xE4));u.mem_write(ENGINE,bytes(0x800))
   u.mem_write(PLAYER+0xA7,bytes([armor]));u.mem_write(PLAYER+0xB8,bytes([arm]));u.mem_write(ENGINE+0x47,bytes([armor,arm]));u.mem_write(ENGINE+0x37,b'\0')
   u.mem_write(PLAYER+0x34,struct.pack('<I',animptr));u.mem_write(PLAYER+0x44,at(exe,animptr,4))
   terminal=[];draw=[];seen=set();trace=[]
   def observe(mu,pc,size,_):
    if pc==RETURN:mu.emu_stop()
    elif pc==0x800350A4:
     terminal.append(mu.reg_read(m.UC_MIPS_REG_A1));mu.emu_stop()
    elif pc==0x8002588C:draw.append(mu.reg_read(m.UC_MIPS_REG_A1))
   # Only the final GPU rasterizer is replaced; native animation and selector run.
   u.mem_write(0x2588C,bytes.fromhex('0800e00300000000'));u.hook_add(UC_HOOK_CODE,observe)
   def run(pc):
    u.reg_write(m.UC_MIPS_REG_A0,PLAYER|0x80000000);u.reg_write(m.UC_MIPS_REG_RA,RETURN);u.emu_start(pc,0,count=10000)
   ticks=0
   while not terminal:
    frame=u.mem_read(PLAYER+0x47,1)[0];cursor=struct.unpack('<I',u.mem_read(PLAYER+0x34,4))[0]
    draw.clear();run(0x800257BC)
    want=[v for bit,v in((8,3),(1,0),(4,2),(2,1))if armor&bit]
    need(draw==want,'Native armor selection changed')
    if cursor not in seen:
     seen.add(cursor);trace.append({'ref':frame,'tick':ticks,'player_armor':u.mem_read(PLAYER+0xA7,1)[0],'arm_type':u.mem_read(PLAYER+0xB8,1)[0],'native_draw_parts':list(draw)})
    run(0x80031540);ticks+=1;need(ticks<130,'Unexpected long sequence')
    need(u.mem_read(PLAYER+0xA7,1)[0]==armor and u.mem_read(PLAYER+0xB8,1)[0]==arm,'Armor lost during return')
   need(terminal==[4],'Unexpected exit animation');rows.append({'armor':armor,'arm_type':arm,'ticks_until_animation4':ticks,'trace':trace})
 out=H/'fourth_return158';out.mkdir(exist_ok=True)
 target=next(r for r in rows if r['armor']==15 and r['arm_type']==2)
 layers={str(n):{str(b):int((arc.layer(n,b)[0]>0).sum())for b in(0,5,6,7,8)}for n in(156,157,158,159,160)}
 write(out/'native.json',{'passed':True,'source_bin_sha256':SOURCE_SHA,'executable_sha256':sha(exe),'original_return_code_exact':True,'original_code_regions':[{'address':hex(a),'bytes':s,'sha256':sha(at(exe,a,s))}for a,s in regions],'cases':rows,'observed_layer_opaque_counts':layers,'conclusion':'귀환156..160은 모든16mask에서 획득 파츠를 유지한다.158 기본붉은의상은 등장133..139의 일시적armor0와 다른 경우이다.현재158포스overlay가 비어 있으면 자원 보완 대상.','runtime_emulator_test':False,'gpu_rasterizer_executed':False,'game_changed':False})
 page([(f'{n} base',arc.composite(n,0)[0])for n in(156,157,158,159,160)]+[(f'{n} fourth',arc.composite(n,15)[0])for n in(156,157,158,159,160)],arc.composite(0,15)[0],out/'frames.png',cols=5,scale=3)
 print(json.dumps({'passed':True,'case_count':len(rows),'full_trace':target,'layers':layers}))
if __name__=='__main__':main()
