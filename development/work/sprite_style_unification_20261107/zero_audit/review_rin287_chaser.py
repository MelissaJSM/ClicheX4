"""현재 EXE의 체이서12표를 원MIPS로 확인하고 원순서 비교를 만든다."""
from pathlib import Path
import sys,json,hashlib,struct,importlib.util
import numpy as np
from PIL import Image,ImageDraw
from unicorn import mips_const as m,UC_HOOK_CODE,Uc,UC_ARCH_MIPS,UC_MODE_MIPS32,UC_MODE_LITTLE_ENDIAN
D=Path(__file__).parent;ROOT=D.parents[2];sys.path.insert(0,str(ROOT))
from scripts.c01_audio_build import read_disc
from scripts.overhaul_sprites_audit import render,rgba
from scripts.prepare_riko_ui import entry
R=D/'rin_extension';P=R/'prepared_chaser01';O=R/'chaser287_review';O.mkdir(exist_ok=True);read=lambda p:json.loads(p.read_text('utf8'));sha=lambda b:hashlib.sha256(b).hexdigest()
plan=read(R/'rin287_components.json');exe=read_disc(ROOT/plan['source_bin'],('SLUS_005.61',))[0]['SLUS_005.61'];load=struct.unpack_from('<I',exe,0x18)[0]
table=read(ROOT/'work/sprite_consistency_20261105/coverage/ver_rin_nana/zero_animations.json');selected=[a for a in table['animations']if 65<=a['id']<=76]
RETURN=0x80001000
def cpu():
 u=Uc(UC_ARCH_MIPS,UC_MODE_MIPS32|UC_MODE_LITTLE_ENDIAN);u.mem_map(0,0x200000);u.mem_map(0x1f800000,4096);size=struct.unpack_from('<I',exe,0x1c)[0];u.mem_write(load&0x1fffffff,exe[2048:2048+size]);u.reg_write(m.UC_MIPS_REG_SP,0x801ff000);return u
native=[];total=0
for a in selected:
 assert a['graphics_bank']==1 and a['composition_bank']==5;off=int(table['table_address'],16)-load+0x800+a['id']*4;assert struct.unpack_from('<I',exe,off)[0]==int(a['address'],16)
 steps=a['steps'];loop=a['loop_to_position'];assert loop is not None
 for s in steps:off=int(s['address'],16)-load+0x800;assert exe[off:off+4]==bytes.fromhex(s['bytes'])
 u=cpu();obj=0xA000;u.mem_write(obj+0x34,struct.pack('<I',int(a['address'],16)));u.mem_write(obj+0x44,bytes.fromhex(steps[0]['bytes']))
 def stop(mu,pc,size,_):
  if pc==RETURN:mu.emu_stop()
 hook=u.hook_add(UC_HOOK_CODE,stop);calls=0
 for s in steps[:loop]+steps[loop:]+steps[loop:]:
  duration=s['duration_calls_uninterrupted']
  for tick in range(duration):
   assert struct.unpack('<I',u.mem_read(obj+0x34,4))[0]==int(s['address'],16);actual=bytes(u.mem_read(obj+0x44,4));assert actual[1:]==bytes.fromhex(s['bytes'])[1:]and actual[0]==(duration-tick)&255
   u.reg_write(m.UC_MIPS_REG_A0,0x80000000+obj);u.reg_write(m.UC_MIPS_REG_RA,RETURN);u.emu_start(0x80015DC8,0,count=1000);assert u.reg_read(m.UC_MIPS_REG_PC)==RETURN;calls+=1
 u.hook_del(hook);assert struct.unpack('<I',u.mem_read(obj+0x34,4))[0]==int(steps[loop]['address'],16);native.append({'animation':a['id'],'actual_calls':calls,'loop_to_position':loop,'frames':[s['frame']for s in steps],'duration_calls':[s['duration_calls_uninterrupted']for s in steps],'passed':True});total+=calls
old=(R/'prepared_ride_heads02/PL01_U.ARC').read_bytes();new=(P/'PL01_U.ARC').read_bytes();assert sha(new)=='99603ab0c003149a4fa415b3dcea78a0967a3be615d226471888bb3ece092a11';sheets=[]
for form,row in [('normal',0),('black',13)]:
 pal=struct.unpack_from('<16H',entry(new,9),row*32)
 for at in range(0,12,2):
  subset=selected[at:at+2];w=max(len(a['steps'])for a in subset)*288;sheet=Image.new('RGB',(w,2*448),'#64717b');dr=ImageDraw.Draw(sheet)
  for rowi,a in enumerate(subset):
   for col,s in enumerate(a['steps']):
    n=s['frame']
    for iy,(tag,arc)in enumerate([('old',old),('new',new)]):
     z=render(arc,1,5,n)[0];outside=z.copy();outside[120:184,112:208]=0;assert not outside.any();pic=rgba(z,pal).crop((112,120,208,184)).resize((288,192),Image.Resampling.NEAREST);x=col*288;y=rowi*448+iy*224;sheet.paste(pic,(x,y+27),pic);dr.text((x+4,y+5),f'{a["id"]}:{s["position"]} {tag} {n} / {s["duration_calls_uninterrupted"]} calls',fill='white')
  p=O/f'original_order_{form}_{at//2:02}.png';sheet.save(p);sheets.append({'path':str(p.relative_to(ROOT)),'sha256':sha(p.read_bytes()),'animations':[a['id']for a in subset],'actually_viewed':False})
 # Exact table-driven prefix and two loops, presented at assumed60calls/sec.
 for a in selected:
  loop=a['loop_to_position'];steps=a['steps'][:loop]+a['steps'][loop:]+a['steps'][loop:];pics=[];dur=[]
  for s in steps:
   frame=Image.new('RGB',(768,280),'#64717b');dr=ImageDraw.Draw(frame)
   for col,(label,arc)in enumerate([('old',old),('new',new)]):
    pic=rgba(render(arc,1,5,s['frame'])[0],pal).crop((112,120,208,184)).resize((384,256),Image.Resampling.NEAREST);frame.paste(pic,(col*384,24),pic);dr.text((col*384+4,4),f'{label} {a["id"]}:{s["position"]} frame{s["frame"]}',fill='white')
   pics.append(frame);dur.append(round(s['duration_calls_uninterrupted']*1000/60))
  pics[0].save(O/f'animation_{a["id"]}_{form}.webp',save_all=True,append_images=pics[1:],duration=dur,loop=0,lossless=True)
report={'passed':True,'candidate_sha256':sha(new),'source_exe_sha256':sha(exe),'native_function':'0x80015DC8','native_actual_calls':total,'native_cases':native,'source_table_bytes_rechecked_in_current_exe':True,'sheets':sheets,'runtime_verified':False,'user_accepted':False,'limitations':['원MIPS animate_object의 순서·유지시간만 격리 실행했다. 실제 차량 물리/핸들/좌석 및 외부 상태 전환은 재현하지 않았다.','WEBP는60calls/sec 가정으로 prefix+두주기를 재생한다. 영상 끝에서 처음으로 돌아가는 것은 검토 반복이며 외부입력으로 바뀌는 실제 플레이를 주장하지 않는다.','96유지시간 relative_step0은 원표의 자기참조다. 프레임 유지와 실제 탑승 종료를 구분한다.']}
(O/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps({'passed':True,'native_calls':total,'sheets':len(sheets)}))
