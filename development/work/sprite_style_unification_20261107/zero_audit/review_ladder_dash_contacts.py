"""원 시간표의 몸체/검기 짝과 고정원점 접점. 실제 플레이 재현은 아니다."""
from pathlib import Path
import sys,json,struct,hashlib
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'work/tools/korean_env/Lib/site-packages'))
from unicorn import Uc,UC_ARCH_MIPS,UC_MODE_MIPS32,UC_MODE_LITTLE_ENDIAN,UC_HOOK_CODE
from unicorn import mips_const as m
from scripts.c01_audio_build import read_disc
from scripts.overhaul_sprites_audit import render,rgba
from scripts.prepare_riko_ui import entry
D=Path(__file__).parent/'rin_extension';A=D/'ladder_dash01';O=A/'contact_probe';O.mkdir(exist_ok=True)
info=json.loads((A/'inputs.json').read_text('utf8'));arc=(ROOT/info['actual_input_arc']).read_bytes();sha=lambda b:hashlib.sha256(b).hexdigest();assert sha(arc)==info['archive_sha256']
src=ROOT/info['source_bin'];assert sha(src.read_bytes())==info['source_sha256'];exe=read_disc(src,('SLUS_005.61',))[0]['SLUS_005.61'];base,size=struct.unpack_from('<II',exe,0x18)
def code(a,z):return exe[a-base+2048:z-base+2048]
manifest=json.loads((ROOT/'work/sprite_consistency_20261105/playback/manifest.json').read_text('utf8'));anims={a['id']:a for a in manifest['characters']['rin']['forms']['normal']['animations']}
for i in(93,104,117,125):
 a=anims[i];assert code(0x8011aff0+i*4,0x8011aff4+i*4)==bytes.fromhex(a['pointer_bytes'])
 for s in a['steps']:assert code(int(s['address'],16),int(s['address'],16)+4)==bytes.fromhex(s['bytes'])
def cpu():
 u=Uc(UC_ARCH_MIPS,UC_MODE_MIPS32|UC_MODE_LITTLE_ENDIAN);u.mem_map(0,0x200000);u.mem_map(0x1f800000,4096);u.mem_write(base&0x1fffffff,exe[2048:2048+size]);u.reg_write(m.UC_MIPS_REG_SP,0x801ff000);return u
def pairs(bodyid,effectid):
 u=cpu();obj=[0xa000,0xb000];steps=[next(s for s in anims[bodyid]['steps']if s['event']&128),anims[effectid]['steps'][0]]
 for o,s in zip(obj,steps):u.mem_write(o+0x34,struct.pack('<I',int(s['address'],16)));u.mem_write(o+0x44,bytes.fromhex(s['bytes']))
 def stop(mu,pc,size,_):
  if pc==0x80008000:mu.emu_stop()
 u.hook_add(UC_HOOK_CODE,stop);rows=[]
 for tick in range(20):
  bb,ee=[bytes(u.mem_read(o+0x44,4))for o in obj];rows.append({'tick':tick,'body':bb[3],'effect':ee[3]})
  for o in obj:u.reg_write(m.UC_MIPS_REG_A0,o|0x80000000);u.reg_write(m.UC_MIPS_REG_RA,0x80008000);u.emu_start(0x80015dc8,0,count=1000);assert u.reg_read(m.UC_MIPS_REG_PC)==0x80008000
 return rows
timelines={'ladder':pairs(93,117),'dash':pairs(104,125)};mapping={199:199,201:199,**{n:202 for n in(202,204,206,208,210)},155:155,156:156};contacts=[];paths=[]
for name,aid,eid,row,addr in(('ladder',93,117,3,0x80108b50),('dash',104,125,9,0x80108b4e)):
 assert code(addr,addr+2)==bytes([eid,row]);unique=list(dict.fromkeys((q['body'],q['effect'])for q in timelines[name]if q['body']in mapping));palette=struct.unpack_from('<16H',entry(arc,9),row*32)
 arrays=[render(arc,0,0,k)[0]for pair in unique for k in pair]+[np.array(Image.open(A/'body_probe'/f'b0_{mapping[n]:03}_indices.png'))for n,e in unique];boxes=[Image.fromarray(np.uint8(z>0)*255).getbbox()for z in arrays];box=(min(z[0]for z in boxes)-2,min(z[1]for z in boxes)-2,max(z[2]for z in boxes)+2,max(z[3]for z in boxes)+2);w,h=(box[2]-box[0])*3,(box[3]-box[1])*3
 for form,pr in(('normal',0),('black',13)):
  words=struct.unpack_from('<16H',entry(arc,9),pr*32);canvas=Image.new('RGB',(len(unique)*w,2*(h+20)),(23,30,40));draw=ImageDraw.Draw(canvas)
  for col,(n,e)in enumerate(unique):
   old=render(arc,0,0,n)[0];new=np.array(Image.open(A/'body_probe'/f'b0_{mapping[n]:03}_indices.png'));effect=render(arc,0,0,e)[0];roi=np.zeros_like(new,bool);roi[150:162,135:156]=True if name=='ladder'else False
   if name=='dash':roi[166:173,127:144]=True
   record={'body':n,'effect':e,'color_form':form}
   for line,(label,body)in enumerate((('old',old),('new',new))):
    im=rgba(body,words);im.alpha_composite(rgba(effect,palette));pic=im.crop(box).resize((w,h),Image.Resampling.NEAREST);canvas.paste(pic,(col*w,line*(h+20)+16),pic);draw.text((col*w+2,line*(h+20)),f'{n}+{e} {label}',fill='white')
    by,bx=np.where((body>0)&roi);ey,ex=np.where(effect>0);dist=np.maximum(abs(by[:,None]-ey),abs(bx[:,None]-ex));record[label+'_hand_to_effect_chebyshev']=int(dist.min());record[label+'_roi_overlap']=int(np.count_nonzero((body>0)&(effect>0)&roi))
   contacts.append(record)
  path=O/f'{name}_{form}.png';canvas.save(path);paths.append(path.name)
report={'passed':True,'candidate_only':True,'native_animation_calls':160,'native_tables_and_weapon_palette_checked':True,'source_bin_sha256':info['source_sha256'],'source_arc_sha256':sha(arc),'timelines':timelines,'contacts':contacts,'sheets':paths,'actual_gameplay':False,'limitations':['원래 animate_object와 실제 표93/117 및104/125의 시작 이후20호출씩을 격리 실행했다. 외부 중단/물리/발생 객체 위치를 재현하지 않는다.','합성은 같은 원점/실제 무기 팔레트의 정적 접점 참고이며 실제 화면 캡처가 아니다.','접점 최소거리는 불투명 손영역과 효과의 거리이며 접촉하는 원검기 전체 의미를 자동 미술판정하지 않는다.']}
(O/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps({'contacts':contacts,'sheets':paths}))
