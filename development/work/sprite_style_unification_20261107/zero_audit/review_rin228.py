"""뇌신격 원 EXE119/120 선택과95/96 원 시간표의 접점을 읽기 검토한다."""
from pathlib import Path
import sys,json,struct,hashlib
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[3];sys.path[:0]=[str(ROOT),str(ROOT/'work/tools/korean_env/Lib/site-packages')]
from unicorn import Uc,UC_ARCH_MIPS,UC_MODE_MIPS32,UC_MODE_LITTLE_ENDIAN,UC_HOOK_CODE
from unicorn import mips_const as m
from scripts.c01_audio_build import read_disc
from scripts.overhaul_sprites_audit import render,rgba
from scripts.prepare_riko_ui import entry
from scripts.export_x_consistency import page
D=Path(__file__).parent/'rin_extension';P=D/'prepared_bank1_special01';O=D/'bank1_special228_review';O.mkdir(exist_ok=True)
sha=lambda b:hashlib.sha256(b).hexdigest();plan=json.loads((D/'rin228_components.json').read_text('utf8'));src=ROOT/plan['source_bin'];assert sha(src.read_bytes())==plan['source_sha256']
exe=read_disc(src,('SLUS_005.61',))[0]['SLUS_005.61'];base,size=struct.unpack_from('<II',exe,0x18)
old=(D/'prepared_dash_saber01/PL01_U.ARC').read_bytes();new=(P/'PL01_U.ARC').read_bytes();assert sha(new)=='989b68597fa276164a16902806136f897c16ef3c1c81950b3b16fa039bede7a0'
def code(a,z):return exe[a-base+2048:z-base+2048]
manifest=json.loads((ROOT/'work/sprite_consistency_20261105/playback/manifest.json').read_text('utf8'));anims={q['id']:q for q in manifest['characters']['rin']['forms']['normal']['animations']}
for aid in (95,96,119,120):
 a=anims[aid];assert code(0x8011aff0+aid*4,0x8011aff4+aid*4)==bytes.fromhex(a['pointer_bytes'])
 for s in a['steps']:assert code(int(s['address'],16),int(s['address'],16)+4)==bytes.fromhex(s['bytes'])
assert code(0x80108b54,0x80108b56)==bytes([119,5])
def cpu():
 u=Uc(UC_ARCH_MIPS,UC_MODE_MIPS32|UC_MODE_LITTLE_ENDIAN);u.mem_map(0,0x200000);u.mem_map(0x1f800000,4096);u.mem_write(base&0x1fffffff,exe[2048:2048+size]);u.reg_write(m.UC_MIPS_REG_SP,0x801ff000);return u
initializers=[]
for combo in(0,1):
 u=cpu();u.mem_write(0xb000,bytes([1,0x20,combo]));u.reg_write(m.UC_MIPS_REG_A0,0x8000b000);u.reg_write(m.UC_MIPS_REG_A1,0x8000a000)
 def init_stop(mu,pc,sz,_):
  if pc==0x80015d60:mu.emu_stop()
 u.hook_add(UC_HOOK_CODE,init_stop);u.emu_start(0x80097fc4,0,count=1000)
 assert u.reg_read(m.UC_MIPS_REG_PC)==0x80015d60 and u.reg_read(m.UC_MIPS_REG_A1)==119+combo and u.reg_read(m.UC_MIPS_REG_S2)==5
 initializers.append({'weapon_id':32,'variant':combo,'actual_animation':119+combo,'actual_palette_row':5,'native_code_sha256':sha(code(0x80097fc4,0x800980e4))})
timelines={};calls=0
for bodyid,effectid in((95,119),(96,120)):
 u=cpu();objects=(0xa000,0xb000);steps=(next(s for s in anims[bodyid]['steps']if s['event']&128),anims[effectid]['steps'][0])
 for o,s in zip(objects,steps):u.mem_write(o+0x34,struct.pack('<I',int(s['address'],16)));u.mem_write(o+0x44,bytes.fromhex(s['bytes']))
 def stop(mu,pc,sz,_):
  if pc==0x80008000:mu.emu_stop()
 u.hook_add(UC_HOOK_CODE,stop);rows=[]
 for tick in range(96):
  body,fx=[bytes(u.mem_read(o+0x44,4))for o in objects];rows.append({'tick':tick,'body':body[3],'effect':fx[3],'body_event':body[1],'effect_event':fx[1]})
  for o in objects:u.reg_write(m.UC_MIPS_REG_A0,o|0x80000000);u.reg_write(m.UC_MIPS_REG_RA,0x80008000);u.emu_start(0x80015dc8,0,count=1000);assert u.reg_read(m.UC_MIPS_REG_PC)==0x80008000;calls+=1
 timelines[str(bodyid)]=rows
selected={91,93,101,103,105,107};pairs=list(dict.fromkeys((r['body'],r['effect'])for rows in timelines.values()for r in rows if r['body']in selected));assert {x[0]for x in pairs}==selected
fxpal=struct.unpack_from('<16H',entry(new,9),5*32);sheets=[]
for name,row in [('normal',0),('black',13)]:
 pal=struct.unpack_from('<16H',entry(new,9),row*32)
 for start in range(0,len(pairs),4):
  items=[]
  for n,e in pairs[start:start+4]:
   fx=render(new,1,5,e)[0];assert np.array_equal(fx,render(old,1,5,e)[0])
   for label,arc in [('old',old),('new',new)]:
    im=rgba(render(arc,1,5,n)[0],pal);im.alpha_composite(rgba(fx,fxpal));items.append((f'b1 {n}+{e} {label}',im))
  p=O/f'effects_{name}_{start//4:02}.png';page(items,rgba(render(new,0,0,147)[0],pal),p,cols=2,scale=5);sheets.append(p.name)
 # Full source body order, with all unchanged neighbouring poses for context.
 for aid in(95,96):
  refs=list(dict.fromkeys(int(s['frame_id'].rsplit('_',1)[1])for s in anims[aid]['steps']if s['frame_id']))
  for start in range(0,len(refs),5):
   subset=refs[start:start+5];im=Image.new('RGB',(320*len(subset),680),'#64717b');dr=ImageDraw.Draw(im)
   for col,n in enumerate(subset):
    for iy,(label,arc)in enumerate([('old',old),('new',new)]):
     p=rgba(render(arc,1,5,n)[0],pal).crop((120,112,200,192)).resize((320,320),Image.Resampling.NEAREST);im.paste(p,(col*320,iy*340+20),p);dr.text((col*320+4,iy*340+3),f'{aid}:{n} {label}',fill='white')
   p=O/f'sequence{aid}_{name}_{start//5:02}.png';im.save(p);sheets.append(p.name)
result={'passed':True,'candidate_sha256':sha(new),'source_arc_sha256':sha(old),'source_bin_sha256':plan['source_sha256'],'native_initializers':initializers,'native_animation_calls':calls,'timelines':timelines,'selected_body_effect_pairs':pairs,'effect_palette_row':5,'sheets':sheets,'actually_viewed_pending':True,'runtime_verified':False,'limitations':['실제 초기화 코드에서 무기0x20의 variant0/1→119/120 및 팔레트5 선택을 확인했다. 실제 원MIPS animate_object 호출의 순서/유지시간만 격리 재현했다.','같은 원점 합성으로 몸체·검기 접점을 비교한다. 물리·배경·외부 중단·이펙트 삭제/루프 종료는 재현하지 않으며 실제 화면 캡처가 아니다.','후반107은 효과의 종료가 외부 상태에 의존하므로 잔존127의 격리 합성이 실제 게임 잔존 효과라고 주장하지 않는다.']}
(O/'report.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps({'passed':True,'calls':calls,'pairs':pairs,'sheets':len(sheets)}))
