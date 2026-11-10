"""새 찌르기8참조를 검증된 원뇌신격 시간표·검기와 재합성한다."""
from pathlib import Path
import sys,json,hashlib,struct
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from scripts.overhaul_sprites_audit import render,rgba
from scripts.prepare_riko_ui import entry
from scripts.export_x_consistency import page
D=Path(__file__).parent/'rin_extension';P=D/'prepared_bank1_special02';O=D/'bank1_special236_review';O.mkdir(exist_ok=True)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();old=(D/'prepared_bank1_special01/PL01_U.ARC').read_bytes();new=(P/'PL01_U.ARC').read_bytes();assert sha(P/'PL01_U.ARC')=='0f6073c262c0b851a1330b86fec51d1bae62838a73241b3e9140a0b7727a5d1e'
native=D/'bank1_special228_review/report.json';timeline=json.loads(native.read_text('utf8'));assert timeline['passed']and timeline['effect_palette_row']==5
selected={108,110,112,114,116,119,122,125};pairs=list(dict.fromkeys((r['body'],r['effect'])for ts in timeline['timelines'].values()for r in ts if r['body']in selected));assert {n for n,e in pairs}==selected
fxpal=struct.unpack_from('<16H',entry(new,9),5*32);sheets=[];sequence=[r for i,r in enumerate(timeline['timelines']['95'])if i==0 or(r['body'],r['effect'])!=(timeline['timelines']['95'][i-1]['body'],timeline['timelines']['95'][i-1]['effect'])]
for form,row in [('normal',0),('black',13)]:
 pal=struct.unpack_from('<16H',entry(new,9),row*32)
 for start in range(0,len(pairs),4):
  items=[]
  for n,e in pairs[start:start+4]:
   fx=render(new,1,5,e)[0];assert np.array_equal(fx,render(old,1,5,e)[0])
   for label,arc in [('old',old),('new',new)]:
    im=rgba(render(arc,1,5,n)[0],pal);im.alpha_composite(rgba(fx,fxpal));items.append((f'{n}+{e} {label}',im))
  p=O/f'effects_{form}_{start//4:02}.png';page(items,rgba(render(new,0,0,147)[0],pal),p,cols=2,scale=5);sheets.append(p.name)
 # Actual ordered source sequence, including repeated thrusts and old terminal128.
 refs=[r['body']for i,r in enumerate(sequence)if i==0 or r['body']!=sequence[i-1]['body']]
 for start in range(0,len(refs),8):
  subset=refs[start:start+8];im=Image.new('RGB',(320*len(subset),680),'#64717b');dr=ImageDraw.Draw(im)
  for col,n in enumerate(subset):
   for iy,(label,arc)in enumerate([('old',old),('new',new)]):
    p=rgba(render(arc,1,5,n)[0],pal).crop((112,112,192,192)).resize((320,320),Image.Resampling.NEAREST);im.paste(p,(col*320,iy*340+20),p);dr.text((col*320+4,iy*340+3),f'{n} {label}',fill='white')
  p=O/f'ordered95_{form}_{start//8:02}.png';im.save(p);sheets.append(p.name)
 # Preview timeline is only the unchanged original order/duration; not physics.
 frames=[]
 for r in timeline['timelines']['95']:
  pair=Image.new('RGB',(640,320),'#64717b')
  for ix,arc in enumerate((old,new)):
   im=rgba(render(arc,1,5,r['body'])[0],pal);im.alpha_composite(rgba(render(arc,1,5,r['effect'])[0],fxpal));v=im.crop((80,112,192,192)).resize((448,320),Image.Resampling.NEAREST);pair.paste(v.crop((128,0,448,320)),(ix*320,0),v.crop((128,0,448,320)))
  frames.append(pair)
 frames[0].save(O/f'isolated_timeline95_{form}.webp',save_all=True,append_images=frames[1:],duration=[round((i+1)*1000/60)-round(i*1000/60)for i in range(len(frames))],loop=0,lossless=True)
j={'passed':True,'candidate_sha256':sha(P/'PL01_U.ARC'),'source_arc_sha256':sha(D/'prepared_bank1_special01/PL01_U.ARC'),'source_native_timeline':{'path':str(native.relative_to(ROOT)),'sha256':sha(native),'actual_native_calls':timeline['native_animation_calls']},'selected_body_effect_pairs':pairs,'ordered_body_refs':refs,'effect_palette_row':5,'sheets':sheets,'runtime_verified':False,'limitations':timeline['limitations']+['이번 검사는 기존 동일 EXE의 실제 MIPS 시간표 증거를 재사용하며 새 MIPS 타이밍 호출로 중복 집계하지 않는다. WEBP는60calls/sec 가정의 검토용 반복이며 외부 종료가 있는 실제게임 전체주기가 아니다.']}
(O/'report.json').write_text(json.dumps(j,ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps({'pairs':pairs,'sheets':sheets,'ordered':refs}))
