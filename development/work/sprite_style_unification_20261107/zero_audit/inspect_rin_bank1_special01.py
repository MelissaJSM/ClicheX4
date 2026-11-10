"""신규 지상 준비/회복 원화의 원손·검기 고정 원점 비교. 입력 쓰기 없음."""
from pathlib import Path
import sys,json,struct,hashlib
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from scripts.overhaul_sprites_audit import render,rgba
from scripts.prepare_riko_ui import entry
D=Path(__file__).parent/'rin_extension/bank1_special01';O=D/'contacts01';O.mkdir(exist_ok=True)
info=json.loads((D/'inputs.json').read_text('utf8'));arc=(ROOT/info['actual_input_arc']).read_bytes();assert hashlib.sha256(arc).hexdigest()==info['archive_sha256']
pal=struct.unpack_from('<16H',entry(arc,9));fxpal=struct.unpack_from('<16H',entry(arc,9),9*32)
rows=[]
for n in (91,93,101,105):
 old=render(arc,1,5,n)[0];new=np.array(Image.open(D/'anchor_probe_v1'/f'b1_{n:03}_indices.png'));fx=render(arc,1,5,n+1)[0]
 sheet=Image.new('RGB',(1280,680),'#5c6872');dr=ImageDraw.Draw(sheet)
 for col,(label,a)in enumerate((('old',old),('new',new))):
  body=rgba(a,pal);pic=body.copy();pic.alpha_composite(rgba(fx,fxpal))
  for j,im in enumerate((body,pic)):
   crop=im.crop((120,120,200,200)).resize((320,320),Image.Resampling.NEAREST);sheet.paste(crop,(col*640+j*320,25),crop);dr.text((col*640+j*320+4,4),f'b1_{n:03} {label}'+(' + next reference'if j else''),fill='white')
  crop=(132,151,188,178);im=body.crop(crop).resize((560,270),Image.Resampling.NEAREST);sheet.paste(im,(col*640+35,390),im)
  for x in range(crop[0],crop[2],4):dr.line((col*640+35+(x-crop[0])*10,390,col*640+35+(x-crop[0])*10,660),fill='#91a0a9');dr.text((col*640+35+(x-crop[0])*10,374),str(x),fill='white')
  for y in range(crop[1],crop[3],3):dr.line((col*640+35,390+(y-crop[1])*10,col*640+595,390+(y-crop[1])*10),fill='#91a0a9');dr.text((col*640+3,390+(y-crop[1])*10),str(y),fill='white')
 sheet.save(O/f'contact_{n:03}.png')
 rows.append({'body':n,'next_reference':n+1,'next_reference_pairing':'일단 공간 비교용. 실제 원 시간표의 몸/검기 호출 순서를 별도 확인해야 함'})
(O/'report.json').write_text(json.dumps({'source_arc_sha256':info['archive_sha256'],'pairs':rows,'runtime_verified':False},ensure_ascii=False,indent=2)+'\n','utf8')
