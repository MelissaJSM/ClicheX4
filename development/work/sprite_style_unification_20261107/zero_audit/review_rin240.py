"""원뇌신격 시간표의 회복128~131과 전후동작을 정수배로 비교."""
from pathlib import Path
import sys,json,hashlib,struct
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from scripts.overhaul_sprites_audit import render,rgba
from scripts.prepare_riko_ui import entry
D=Path(__file__).parent/'rin_extension';O=D/'bank1_recovery240_review';O.mkdir(exist_ok=True);P=D/'prepared_bank1_recovery128';old=(D/'prepared_bank1_special02/PL01_U.ARC').read_bytes();new=(P/'PL01_U.ARC').read_bytes();sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(P/'PL01_U.ARC')=='07ec6077969f17d08c51ffd8e4326b476e1c6ab5635bea8420faee9528b39a89'
source=D/'bank1_special228_review/report.json';timeline=json.loads(source.read_text('utf8'));assert timeline['passed'];rows=timeline['timelines']['95'][62:96];refs=[]
for r in rows:
 if not refs or refs[-1]!=r['body']:refs.append(r['body'])
assert refs==[125,128,129,130,131,107,98,95,87,86];sheets=[]
for form,clut in [('normal',0),('black',13)]:
 pal=struct.unpack_from('<16H',entry(new,9),clut*32)
 for start in range(0,len(refs),5):
  subset=refs[start:start+5];im=Image.new('RGB',(320*len(subset),680),'#64717b');dr=ImageDraw.Draw(im)
  for col,n in enumerate(subset):
   for iy,(label,arc)in enumerate([('old',old),('new',new)]):
    p=rgba(render(arc,1,5,n)[0],pal).crop((112,112,192,192)).resize((320,320),Image.Resampling.NEAREST);im.paste(p,(col*320,iy*340+20),p);dr.text((col*320+4,iy*340+3),f'{n} {label}',fill='white')
  path=O/f'recovery_{form}_{start//5:02}.png';im.save(path);sheets.append(path.name)
 frames=[]
 for r in rows:
  pic=Image.new('RGB',(640,320),'#64717b')
  for x,arc in enumerate((old,new)):
   p=rgba(render(arc,1,5,r['body'])[0],pal).crop((112,112,192,192)).resize((320,320),Image.Resampling.NEAREST);pic.paste(p,(x*320,0),p)
  frames.append(pic)
 frames[0].save(O/f'recovery_{form}.webp',save_all=True,append_images=frames[1:],duration=[round((i+1)*1000/60)-round(i*1000/60)for i in range(len(frames))],loop=0,lossless=True)
j={'passed':True,'candidate_sha256':sha(P/'PL01_U.ARC'),'source_native_timeline':{'path':str(source.relative_to(ROOT)),'sha256':sha(source)},'ordered_refs':refs,'actual_duration_calls':{'128':2,'129':2,'130':3,'131':4},'sheets':sheets,'native_integer_scale':4,'external_state_or_effect_simulated':False,'runtime_verified':False,'limitations':['동일 EXE의 실제 MIPS 시간표 증거를 재사용하며 추가 네이티브 호출로 중복 집계하지 않는다.','원 회복 순서/유지시간의 검토용 반복이다. 실제 게임 물리/상태전환/효과삭제·가림은 별도다.']}
(O/'report.json').write_text(json.dumps(j,ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps(j))
