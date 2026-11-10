"""등장 원표와 실제 beam_in 종료를 격리 MIPS 실행하고 양팔레트 연결판을 만든다."""
from pathlib import Path
import sys,json,hashlib,struct
import numpy as np
from PIL import Image,ImageDraw
from unicorn import Uc,UC_ARCH_MIPS,UC_MODE_MIPS32,UC_MODE_LITTLE_ENDIAN,UC_HOOK_CODE,mips_const as m
D=Path(__file__).parent;ROOT=D.parents[2];sys.path.insert(0,str(ROOT))
from scripts.c01_audio_build import read_disc
from scripts.overhaul_sprites_audit import render,rgba
from scripts.prepare_riko_ui import entry
R=D/'rin_extension';P=R/'prepared_arrival01';O=R/'arrival294_review_v2';O.mkdir(exist_ok=True);read=lambda p:json.loads(p.read_text('utf8'));sha=lambda b:hashlib.sha256(b).hexdigest();rel=lambda p:p.relative_to(ROOT).as_posix()
plan=read(R/'rin294_components.json');exe=read_disc(ROOT/plan['source_bin'],('SLUS_005.61',))[0]['SLUS_005.61'];load,size=struct.unpack_from('<II',exe,0x18);table=read(ROOT/'work/sprite_consistency_20261105/coverage/ver_rin_nana/zero_animations.json');anim=table['animations'][2];assert anim['id']==2 and anim['graphics_bank']==0;steps=anim['steps'];at=lambda addr,n:exe[addr-load+0x800:addr-load+0x800+n]
assert struct.unpack('<I',at(int(table['table_address'],16)+8,4))[0]==int(anim['address'],16)
for s in steps:assert at(int(s['address'],16),4)==bytes.fromhex(s['bytes'])
u=Uc(UC_ARCH_MIPS,UC_MODE_MIPS32|UC_MODE_LITTLE_ENDIAN);u.mem_map(0,0x200000);u.mem_map(0x1f800000,4096);u.mem_write(load&0x1fffffff,exe[2048:2048+size]);u.reg_write(m.UC_MIPS_REG_SP,0x801ff000);obj=0x1418c8;END=0x80001000;u.mem_write(obj+2,b'\x01');u.mem_write(obj+6,b'\x01');u.mem_write(obj+0x34,struct.pack('<I',int(anim['address'],16)));u.mem_write(obj+0x44,bytes.fromhex(steps[0]['bytes']));entered=False;trace=[]
def observe(mu,pc,size,_):
 global entered
 if pc==0x800343A4 and not entered:entered=True;mu.emu_stop()
 elif pc==END:mu.emu_stop()
u.hook_add(UC_HOOK_CODE,observe)
for tick in range(200):
 cursor=struct.unpack('<I',u.mem_read(obj+0x34,4))[0];state=bytes(u.mem_read(obj+0x44,4));pos=(cursor-int(anim['address'],16))//4;assert 0<=pos<len(steps);s=steps[pos];assert state[1:]==bytes.fromhex(s['bytes'])[1:]
 trace.append({'tick':tick,'position':pos,'frame':state[3],'remaining_duration':state[0],'relative_step':state[2]})
 u.reg_write(m.UC_MIPS_REG_A0,obj|0x80000000);u.reg_write(m.UC_MIPS_REG_RA,END);u.emu_start(0x80031410,0,count=10000)
 if entered:break
assert entered and len(trace)==sum(s['duration_calls_uninterrupted']for s in steps[:-1]);assert trace[-1]['frame']==253;assert not any(x['position']==13 for x in trace)
for s in steps[:-1]:assert sum(x['position']==s['position']for x in trace)==s['duration_calls_uninterrupted']
idle=table['animations'][5];assert idle['id']==5 and idle['steps'][0]['frame']==0
assert struct.unpack('<I',at(int(table['table_address'],16)+20,4))[0]==int(idle['address'],16)
for s in idle['steps']:assert at(int(s['address'],16),4)==bytes.fromhex(s['bytes'])
u.mem_write(obj+0x30,struct.pack('<I',int(table['table_address'],16)))
u.mem_write(obj+0x5c,b'\x18');u.reg_write(m.UC_MIPS_REG_SP,0x801ff000)
u.reg_write(m.UC_MIPS_REG_A0,obj|0x80000000);u.reg_write(m.UC_MIPS_REG_RA,END)
u.emu_start(0x800343A4,0,count=10000)
idle_cursor=struct.unpack('<I',u.mem_read(obj+0x34,4))[0]
idle_state=bytes(u.mem_read(obj+0x44,4))
assert idle_cursor==int(idle['address'],16),(hex(idle_cursor),idle_state.hex())
assert idle_state==bytes.fromhex(idle['steps'][0]['bytes'])
old=(R/'prepared_chaser01/PL01_U.ARC').read_bytes();new=(P/'PL01_U.ARC').read_bytes();assert sha(new)=='adf3b9475dd95cad5ff53ba627e4461dc9cb7ec18d202482b59744b0587c0322';idle0same=bool(np.array_equal(render(new,0,0,0)[0],render(new,0,0,147)[0]));sheets=[]
frames=[s['frame']for s in steps[:-1]]+[s['frame']for s in idle['steps']];durations=[s['duration_calls_uninterrupted']for s in steps[:-1]]+[s['duration_calls_uninterrupted']for s in idle['steps']]
for form,row in [('normal',0),('black',13)]:
 pal=struct.unpack_from('<16H',entry(new,9),row*32)
 for page,ids in enumerate(([247,248,249,250],[251,252,253,147],[253,0,146,147])):
  sh=Image.new('RGB',(1536,768),'#64717b');dr=ImageDraw.Draw(sh)
  for col,n in enumerate(ids):
   for iy,(tag,arc)in enumerate([('old',old),('new',new)]):
    z=render(arc,0,0,n)[0];outside=z.copy();outside[112:192,112:208]=0;assert not outside.any();pic=rgba(z,pal).crop((112,112,208,192)).resize((384,320),Image.Resampling.NEAREST);sh.paste(pic,(col*384,iy*384+40),pic);dr.text((col*384+4,iy*384+5),f'{tag} {n}'+(' idle reference'if n==147 else ''),fill='white')
  p=O/f'original_order_{form}_{page:02}.png';sh.save(p);sheets.append({'path':rel(p),'sha256':sha(p.read_bytes()),'refs':ids,'actually_viewed':False})
 pics=[];times=[]
 for n,d in zip(frames,durations):
  pic=Image.new('RGB',(768,376),'#64717b');dr=ImageDraw.Draw(pic)
  for col,(label,arc)in enumerate([('old',old),('new',new)]):
   sprite=rgba(render(arc,0,0,n)[0],pal).crop((112,96,208,192)).resize((384,384),Image.Resampling.NEAREST);pic.paste(sprite,(col*384,-8),sprite);dr.text((col*384+4,3),f'{label} {n} / {d} calls',fill='white')
  pics.append(pic);times.append(round(d*1000/60))
 pics[0].save(O/f'arrival_{form}.webp',save_all=True,append_images=pics[1:],duration=times,loop=0,lossless=True)
report={'passed':True,'candidate_sha256':sha(new),'source_exe_sha256':sha(exe),'native_entry':'0x80031410','native_animation_function':'0x80015DC8','native_stop_observed':'0x800343A4 player_enter_idle','native_calls_until_idle':len(trace),'trace':trace,'source_table':anim,'original_terminal96_not_shown_by_caller':True,'source_table_pointer_bytes_exact':True,'idle0_equals147':idle0same,'native_enter_idle':{'executed_original_function':True,'animation':5,'first_ref':0,'cursor':hex(idle_cursor),'step_bytes':idle_state.hex(),'initialization':{'hp':24,'animation_table':table['table_address'],'script_state':0,'max_hp':0},'source_table':idle},'sheets':sheets,'runtime_verified':False,'user_accepted':False,'limitations':['실제 beam_in 함수의 접지후 경로만 격리 실행. 실제 위에서 낙하하는 이동/맵충돌/차량/에뮬레이터 실기는 미검증.','원표 마지막253 duration96 자기참조는 호출자가 대기함수로 진입하며 표시되지 않는다.39호출 종료와 이어진 원대기함수의 animation5/ref0 선택을 실제 MIPS로 확인했다.','두번째 판의147은 기준 그림이며 실제 직후는0이다. 세번째 판253→0→146→147 및 WEBP는 실제 대기표 순서를 사용한다. 전체파일 반복은 미술 검토용이며 재등장이 실제 자동반복된다는 뜻은 아니다.','대기 표 이후 외부입력/피격/주변물리 개입은 미재현.60calls/sec는 재생가정.']}
(O/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps({'passed':True,'calls':len(trace),'idle0_equals147':idle0same,'sheets':len(sheets)}))
