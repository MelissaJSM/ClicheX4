"""Restore native body/flame pair order and inspect authored hand contacts."""
from pathlib import Path
import sys,json,hashlib,struct
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'work/tools/korean_env/Lib/site-packages'))
from unicorn import Uc,UC_ARCH_MIPS,UC_MODE_MIPS32,UC_MODE_LITTLE_ENDIAN,UC_HOOK_CODE
from unicorn import mips_const as m
from scripts.c01_audio_build import read_disc
from scripts.prepare_riko_ui import entry
from scripts.overhaul_sprites_audit import render,rgba
D=Path(__file__).parent/'rin_extension';P=D/'prepared_rising_rear_v1';O=D/'rising_flame_review_v1';O.mkdir(exist_ok=True)
sha=lambda b:hashlib.sha256(b).hexdigest()
old=(D/'prepared_rear_continuation2_v1/PL01_U.ARC').read_bytes();new=(P/'PL01_U.ARC').read_bytes()
assert sha(old)=='a565e55fb422764432b03fe60d53430fcd5ede2aa95829a655a9c22bcc902c4d';assert sha(new)=='223e553f97ecc85d52b085f3e0e6cd46ecc914063f1adcef43fd1d34c25d298e'
source=ROOT/'out/ver_rin_nana/sprite_reaudit_20261106_v1/rin_nana.bin';assert sha(source.read_bytes())=='f9762868ea6a5c3e9ce65708a07bfbff3762cd98c6a057f78b584525fb48c720'
exe=read_disc(source,('SLUS_005.61',))[0]['SLUS_005.61'];base,size=struct.unpack_from('<II',exe,0x18)
def code(a,z):return exe[a-base+2048:z-base+2048]
manifest_path=ROOT/'work/sprite_consistency_20261105/playback/manifest.json';manifest=json.loads(manifest_path.read_text('utf8'))
animations={a['id']:a for a in manifest['characters']['rin']['forms']['normal']['animations']}
for i in(101,123):
 a=animations[i];assert code(0x8011aff0+i*4,0x8011aff4+i*4)==bytes.fromhex(a['pointer_bytes'])
 for s in a['steps']:assert code(int(s['address'],16),int(s['address'],16)+4)==bytes.fromhex(s['bytes'])
# Native weapon id23 -> animation123 and palette row8. Its copied coordinates
# and facing are tested below, without replacing any game instructions.
assert code(0x80108b5a,0x80108b5c)==bytes([123,8])
def cpu():
 u=Uc(UC_ARCH_MIPS,UC_MODE_MIPS32|UC_MODE_LITTLE_ENDIAN);u.mem_map(0,0x200000);u.mem_map(0x1f800000,4096);u.mem_write(base&0x1fffffff,exe[2048:2048+size]);u.reg_write(m.UC_MIPS_REG_SP,0x801ff000);return u
u=cpu();objects=[0xa000,0xb000];steps=[animations[101]['steps'][2],animations[123]['steps'][0]]
for obj,s in zip(objects,steps):u.mem_write(obj+0x34,struct.pack('<I',int(s['address'],16)));u.mem_write(obj+0x44,bytes.fromhex(s['bytes']))
RETURN=0x80008000
def stop(mu,pc,size,_):
 if pc==RETURN:mu.emu_stop()
h=u.hook_add(UC_HOOK_CODE,stop);ticks=[]
for tick in range(40):
 body,effect=[bytes(u.mem_read(obj+0x44,4))for obj in objects];assert effect[3]==body[3]+1;assert effect[0]==body[0]
 ticks.append({'tick':tick,'body':body[3],'effect':effect[3],'body_duration_remaining':body[0],'effect_duration_remaining':effect[0]})
 for obj in objects:
  u.reg_write(m.UC_MIPS_REG_A0,obj|0x80000000);u.reg_write(m.UC_MIPS_REG_RA,RETURN);u.emu_start(0x80015dc8,0,count=1000);assert u.reg_read(m.UC_MIPS_REG_PC)==RETURN
u.hook_del(h)
positions=[]
for direction in(0,0x80):
 v=cpu();body,effect=objects
 v.mem_write(body+8,struct.pack('<II',0x123456,0x987654));v.mem_write(body+0x15,bytes([direction]));v.mem_write(effect+0x45,b'\x39')
 v.reg_write(m.UC_MIPS_REG_A0,effect|0x80000000);v.reg_write(m.UC_MIPS_REG_A1,body|0x80000000);v.emu_start(0x80098138,0x80098180,count=100)
 assert bytes(v.mem_read(body+8,8))==bytes(v.mem_read(effect+8,8));assert bytes(v.mem_read(body+0x15,1))==bytes(v.mem_read(effect+0x15,1));positions.append({'direction':direction,'native_copy_position_and_facing_exact':True})
pal=entry(new,9);normal=struct.unpack_from('<16H',pal);black=struct.unpack_from('<16H',pal,13*32);fire=struct.unpack_from('<16H',pal,8*32)
historical=ROOT/'work/ver_buki_riko/rise_alignment/20261025T120817448635Z/vram_04.bin';vram=historical.read_bytes();assert vram[480*2048+32:480*2048+64]==pal[8*32:9*32]
contacts=[];images={}
for n in(148,150,152,154):
 before=render(old,1,5,n)[0];after=render(new,1,5,n)[0];e=render(new,1,5,n+1)[0];assert np.array_equal(e,render(old,1,5,n+1)[0])
 ey,ex=np.nonzero(e);region=np.zeros_like(e,bool);region[120:134,140:155]=True;record={'body':n,'flame':n+1}
 for label,a in [('before',before),('after',after)]:
  yy,xx=np.nonzero((a>0)&region);dist=np.maximum(abs(yy[:,None]-ey),abs(xx[:,None]-ex));i,j=np.unravel_index(dist.argmin(),dist.shape)
  record[label]={'hand_or_grip_to_flame_chebyshev':int(dist[i,j]),'hand_or_grip_point':[int(xx[i]),int(yy[i])],'flame_point':[int(ex[j]),int(ey[j])],'overlap_in_hand_roi':int(np.count_nonzero((a>0)&(e>0)&region))};assert int(dist[i,j])==0
 for form,words in [('normal',normal),('black',black)]:
  for label,a in [('before',before),('after',after)]:
   im=rgba(a,words);im.alpha_composite(rgba(e,fire));images[form,n,label]=im
 contacts.append(record)
for form in('normal','black'):
 for ix,refs in enumerate(((148,150),(152,154))):
  board=Image.new('RGB',(960,1168),(27,33,44));draw=ImageDraw.Draw(board)
  for row,n in enumerate(refs):
   for col,label in enumerate(('before','after')):
    im=images[form,n,label].crop((96,80,176,192)).resize((400,560),Image.Resampling.NEAREST);x=col*480;y=row*584;board.paste(im,(x+40,y+22),im);draw.text((x+8,y+4),f'{form} {n}+{n+1} {label}; native 2 calls',fill='white')
  board.save(O/f'{form}_fire_{ix:02}.png')
 # A contact-only sheet at12x: black ground reveals any transparent cuff gap.
 zoom=Image.new('RGB',(4*240,2*288),(18,23,31));draw=ImageDraw.Draw(zoom)
 for col,n in enumerate((148,150,152,154)):
  for row,label in enumerate(('before','after')):
   im=images[form,n,label].crop((138,114,157,136)).resize((228,264),Image.Resampling.NEAREST);zoom.paste(im,(col*240,row*288+20),im);draw.text((col*240+4,row*288+4),f'{n}/{n+1} {label}',fill='white')
 zoom.save(O/f'{form}_contact_zoom.png')
 # Table-only fixed-origin replay; no motion/physics claim. Each pose=2/60sec.
 sequence=[]
 for row in ticks[4:20:2]:
  im=images[form,row['body'],'after'].crop((96,80,176,192)).resize((400,560),Image.Resampling.NEAREST);bg=Image.new('RGBA',im.size,(27,33,44,255));bg.alpha_composite(im);sequence.append(bg)
 sequence[0].save(O/f'{form}_native_order.webp',save_all=True,append_images=sequence[1:],duration=[33,34,33,33,34,33,33,34],loop=0,lossless=True)
report={'passed':True,'source_bin':str(source.relative_to(ROOT)),'source_bin_sha256':sha(source.read_bytes()),'exe_sha256':sha(exe),'candidate_sha256':sha(new),'native_animation_ids':[101,123],'body_spawn_event_frame':144,'body_spawn_event_bits':128,'effect_weapon_id':35,'effect_start_frame':145,'native_weapon_mapping':{'address':'0x80108b5a','bytes':'7b08','animation':123,'palette_row':8},'native_animation_calls':80,'aligned_timeline':ticks,'native_position_copy':positions,'native_copy_function_range':['0x80098138','0x80098180'],'native_code_sha256':sha(code(0x80097eec,0x800981cc)),'contacts':contacts,'flame_pixels_palette_and_composition_preserved':True,'fire_palette_historical_live_match':{'path':str(historical.relative_to(ROOT)),'sha256':sha(vram),'vram_clut':'0x7801','current_arc_row':8},'actually_viewed_pending':True,'limitations':['실제 미국판 EXE의 animate_object 시간표와 위치/방향복사 부분만 격리 실행했다. 전체 기술·물리·실기 실행은 아니다.','합성은 같은 원점의 몸체+무기0x23 불꽃이다. 별도 misc0x30 잔불과 게임 배경/가림은 재현하지 않았다.','불꽃색은 현재 팔레트8이며 과거 실제 VRAM0x7801과 일치한다. 이번 새그림의 실기 캡처가 아니다.','표시 순서와 접점 확대를 직접 열람한 결과는 별도 실제열람 기록 후 마감한다.']}
(O/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps({'passed':True,'native_calls':80,'contacts':contacts,'out':str(O)}))
