"""Registered crops from real window recordings; no sprite editing."""
from pathlib import Path
import json,math,hashlib
from PIL import Image,ImageDraw
R=Path(__file__).resolve().parent;sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
cases={'nana_fourth_recoil28':{'right_recoil':(2.8,4.2),'left_recoil':(8.6,10.0)},'nana_fourth_settle28':{'charged_left':(6.4,7.4),'charged_right':(13.4,14.4)}}
for name,groups in cases.items():
 play=R/(name+'_play');out=R/(name+'_review');assert not out.exists();out.mkdir()
 rec=json.loads((play/'evidence.json').read_text('utf8'));im=Image.open(play/'play.webp');pages=[];box=(150,100,400,550);cw,ch=250,450
 for label,(lo,hi) in groups.items():
  ids=[i for i,t in enumerate(rec['capture_times']) if lo<=t<=hi]
  for part,start in enumerate(range(0,len(ids),12)):
   selected=ids[start:start+12];board=Image.new('RGB',(cw*4,(ch+24)*math.ceil(len(selected)/4)),'#202630');draw=ImageDraw.Draw(board)
   for j,index in enumerate(selected):
    im.seek(index);x,y=j%4*cw,j//4*(ch+24);board.paste(im.convert('RGB').crop(box),(x,y+24));draw.text((x+4,y+5),f'{label} #{index} {rec["capture_times"][index]:.3f}s',fill='white')
   p=out/f'{label}_{part:02}.png';board.save(p);pages.append({'path':p.as_posix(),'sha256':sha(p),'window_indices':selected,'crop':list(box)})
 (out/'manifest.json').write_text(json.dumps({'source':(play/'play.webp').as_posix(),'source_sha256':sha(play/'play.webp'),'actual_window_crops':True,'sprite_pixels_edited':False,'resampled':False,'pages':pages},indent=2)+'\n','utf8');print(name,len(pages))
