"""Compare new air-saber art contacts without editing either input."""
from pathlib import Path
import sys,json,hashlib,struct
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from scripts.overhaul_sprites_audit import render,rgba
from scripts.prepare_riko_ui import entry
D=Path(__file__).parent/'rin_extension';A=D/'air_saber01';O=D/'air_saber_contacts01';O.mkdir(exist_ok=True)
arc=(D/'prepared_ground_remaining_v1/PL01_U.ARC').read_bytes();sha=lambda b:hashlib.sha256(b).hexdigest();pal=struct.unpack_from('<16H',entry(arc,9));words=list(struct.unpack_from('<64H',entry(arc,9)))
refs=[213,215,217,219];metrics=[]
sheet=Image.new('RGB',(1280,256*4),'#657580');dr=ImageDraw.Draw(sheet)
for row,n in enumerate(refs):
 old=render(arc,0,0,n)[0];new=np.array(Image.open(A/'native'/f'b0_{n:03}_indices.png'));effect=render(arc,0,0,n+1)[0]
 for col,(label,a)in enumerate([('old',old),('new',new)]):
  pic=rgba(a,pal).crop((128,120,208,184)).resize((640,512),Image.Resampling.NEAREST)
  # Top half focuses on hands/head. A separate full effect page retains the complete legs.
  sheet.paste(pic.crop((0,0,640,232)),(640*col,256*row+24));dr.text((640*col+4,256*row+3),f'{n} {label}: world x=-32..47 y=-40..-12',fill='white')
  for x in range(128,209,8):dr.text((col*640+(x-128)*8,row*256+220),str(x-160),fill='#ffff00')
 for typ,a in [('old',old),('new',new)]:
  face=(a==15);face[155:,:]=False;yy,xx=np.where(face);metrics.append({'ref':n,'type':typ,'eye_xy':[[int(x),int(y)]for y,x in zip(yy,xx)],'bounds':rgba(a,pal).getbbox()})
 for form,palette in [('normal',words),('black',list(struct.unpack_from('<16H',entry(arc,9),13*32))+words[16:])]:
  s=Image.new('RGB',(1024,560),'#657580');d=ImageDraw.Draw(s)
  for col,(label,a)in enumerate([('old',old),('new',new)]):
   for line,v in enumerate((a,np.where(effect,effect,a))):
    p=rgba(v,palette).crop((96,112,224,240)).resize((256,256),Image.Resampling.NEAREST);s.paste(p,(col*512+line*256,25),p);d.text((col*512+line*256+4,4),f'{n} {label}'+(' + effect'if line else''),fill='white')
   p=rgba(a,palette).crop((128,128,200,184)).resize((432,336),Image.Resampling.NEAREST);s.paste(p.crop((0,100,432,336)),(col*512+40,300));d.text((col*512+4,282),'6x contact view',fill='white')
  s.save(O/f'{form}_{n:03}.png')
sheet.save(O/'head_hand_coordinates.png')
(O/'metrics.json').write_text(json.dumps({'source_sha256':sha(arc),'metrics':metrics,'effect_pairs':[[n,n+1]for n in refs],'same_origin_static_only':True},indent=2)+'\n','utf8')
g=A/'generation.json';g.write_text(json.dumps({'tool':'builtin image_gen','source':'<LOCAL_PATH>','sha256':sha((A/'generated.png').read_bytes()),'size':Image.open(A/'generated.png').size,'prompt_sha256':sha((A/'prompt.txt').read_bytes()),'inputs':['input.png','idle147.png','refined_air21.png','refined_attack109.png'],'runtime_verified':False,'user_accepted':False},ensure_ascii=False,indent=2)+'\n','utf8')
print(json.dumps(metrics))
