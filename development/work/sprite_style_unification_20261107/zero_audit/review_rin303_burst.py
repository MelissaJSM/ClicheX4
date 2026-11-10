"""낙봉파 실제 원함수/원표 순서와 새9·기존4 몸체의 연결을 비교한다."""
from pathlib import Path
import sys,json,hashlib,struct
import numpy as np
from PIL import Image,ImageDraw
from unicorn import Uc,UC_ARCH_MIPS,UC_MODE_MIPS32,UC_MODE_LITTLE_ENDIAN,UC_HOOK_CODE,mips_const as m
D=Path(__file__).parent;ROOT=D.parents[2];sys.path.insert(0,str(ROOT))
from scripts.c01_audio_build import read_disc
from scripts.overhaul_sprites_audit import render,rgba
from scripts.prepare_riko_ui import entry
R=D/'rin_extension';P=R/'prepared_burst_remaining02';O=R/'burst303_review_v2';O.mkdir(exist_ok=True);read=lambda p:json.loads(p.read_text('utf8'));sha=lambda b:hashlib.sha256(b).hexdigest();rel=lambda p:p.relative_to(ROOT).as_posix()
plan=read(R/'rin303_v2_components.json');exe=read_disc(ROOT/plan['source_bin'],('SLUS_005.61',))[0]['SLUS_005.61'];load,size=struct.unpack_from('<II',exe,0x18);table=read(ROOT/'work/sprite_consistency_20261105/coverage/ver_rin_nana/zero_animations.json');anim=table['animations'][103];assert anim['id']==103 and anim['graphics_bank']==1;steps=anim['steps'];at=lambda addr,n:exe[addr-load+0x800:addr-load+0x800+n]
assert struct.unpack('<I',at(int(table['table_address'],16)+103*4,4))[0]==int(anim['address'],16)
for s in steps:assert at(int(s['address'],16),4)==bytes.fromhex(s['bytes'])
cases=[]
for facing in(0,1):
 u=Uc(UC_ARCH_MIPS,UC_MODE_MIPS32|UC_MODE_LITTLE_ENDIAN);u.mem_map(0,0x200000);u.mem_map(0x1f800000,4096);u.mem_write(load&0x1fffffff,exe[2048:2048+size]);u.reg_write(m.UC_MIPS_REG_SP,0x801ff000);obj=0x1418c8;END=0x80001000;u.mem_write(obj+2,b'\x01');u.mem_write(obj+0x15,bytes([facing]));u.mem_write(obj+0x34,struct.pack('<I',int(anim['address'],16)));u.mem_write(obj+0x44,bytes.fromhex(steps[0]['bytes']));stop={'land':False};trace=[];calls={'visual_allocator':0,'weapon_allocator':0}
 def observe(mu,pc,size,_):
  if pc==0x8003470C:stop['land']=True;mu.emu_stop()
  elif pc==0x8002AD3C:calls['visual_allocator']+=1
  elif pc==0x8002AC0C:calls['weapon_allocator']+=1
  elif pc==END:mu.emu_stop()
 u.hook_add(UC_HOOK_CODE,observe)
 for tick in range(200):
  cursor=struct.unpack('<I',u.mem_read(obj+0x34,4))[0];state=bytes(u.mem_read(obj+0x44,4));pos=(cursor-int(anim['address'],16))//4;assert 0<=pos<len(steps);s=steps[pos];assert state[2:]==bytes.fromhex(s['bytes'])[2:];trace.append({'tick':tick,'position':pos,'frame':state[3],'duration_left':state[0],'event_before_update':state[1]})
  u.reg_write(m.UC_MIPS_REG_A0,obj|0x80000000);u.reg_write(m.UC_MIPS_REG_RA,END);u.emu_start(0x8003B044,0,count=30000)
  if stop['land']:break
 assert stop['land'] and len(trace)==sum(s['duration_calls_uninterrupted']for s in steps[:-1])
 assert calls=={'visual_allocator':1,'weapon_allocator':9}
 for s in steps[:-1]:assert sum(x['position']==s['position']for x in trace)==s['duration_calls_uninterrupted']
 cases.append({'facing':facing,'calls_until_land_or_fall':len(trace),'original_allocator_calls':calls,'trace':trace,'terminal96_not_displayed':True})
old=(R/'prepared_arrival01/PL01_U.ARC').read_bytes();new=(P/'PL01_U.ARC').read_bytes();assert sha(new)=='1dde3e8793628d5f38b4318543e8d9f3a22b37ad350622a96f4f4f63e92610b9';sheets=[]
for form,row in(('normal',0),('black',13)):
 pal=struct.unpack_from('<16H',entry(new,9),row*32)
 for page,ids in enumerate(([177,178,179,180],[180,181,182,183],[182,183,184,185],[185,186,187,188],[186,187,188,189])):
  sh=Image.new('RGB',(1536,768),'#526274');dr=ImageDraw.Draw(sh)
  for col,n in enumerate(ids):
   duration=[s['duration_calls_uninterrupted']for s in steps[:-1]if s['frame']==n]
   for iy,(tag,arc)in enumerate([('old',old),('new',new)]):
    z=render(arc,1,5,n)[0];outside=z.copy();outside[112:192,112:208]=0;assert not outside.any();pic=rgba(z,pal).crop((112,112,208,192)).resize((384,320),Image.Resampling.NEAREST);sh.paste(pic,(col*384,iy*384+40),pic);dr.text((col*384+4,iy*384+5),f'{tag} {n} / {duration} calls',fill='white')
  path=O/f'original_order_{form}_{page:02}.png';sh.save(path);sheets.append({'path':rel(path),'sha256':sha(path.read_bytes()),'refs':ids,'actually_viewed':False})
 pics=[];times=[]
 for s in steps[:-1]:
  n=s['frame'];d=s['duration_calls_uninterrupted'];pic=Image.new('RGB',(768,384),'#526274');dr=ImageDraw.Draw(pic)
  for col,(tag,arc)in enumerate([('old',old),('new',new)]):
   z=rgba(render(arc,1,5,n)[0],pal).crop((112,112,208,192)).resize((384,320),Image.Resampling.NEAREST);pic.paste(z,(col*384,40),z);dr.text((col*384+4,5),f'{tag} ref{n}, {d} calls, pos{s["position"]}',fill='white')
  pics.append(pic);times.append(round(d*1000/60))
 pics[0].save(O/f'original_table_{form}.webp',save_all=True,append_images=pics[1:],duration=times,loop=0,lossless=True)
report={'passed':True,'candidate_sha256':sha(new),'source_exe_sha256':sha(exe),'original_animation_table':anim,'original_native_function':'0x8003B044 player_zero_rakuhouha','native_return_at':'0x8003470C player_enter_land_or_fall','cases':cases,'sheets':sheets,'runtime_verified':False,'user_accepted':False,'limitations':['실제 원MIPS 함수와 원 allocator를 격리 실행했으며 호출/몸체순서만 확인했다. 생성된 무기·시각 객체의 후속 업데이트와 맵충돌/피격/게임플레이는 미재현.','182..185는 원표상1/2/3/4호출씩4회 진행하고186..189로 회복한다. 원표 끝189 duration96은 호출자가 land_or_fall로 전환하여 표시하지 않는다.','구체는 몸체에 이미 포함된 원 world texel을 보존한다. 별도 정적23/24/효과후속은 바이트/정적검증 근거이며 이 몸체판에는 따로 합성하지 않았다.','WEBP 전체 반복은 미술검토용이며 실제 자동 재공격을 의미하지 않는다. 60calls/sec는 재생가정이다.']}
(O/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps({'passed':True,'calls':[r['calls_until_land_or_fall']for r in cases],'sheets':len(sheets)}))
