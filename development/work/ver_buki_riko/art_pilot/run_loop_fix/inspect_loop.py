from pathlib import Path
import sys,json
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT))
import numpy as np
from PIL import Image,ImageDraw,ImageFont
from scripts.repack_zero import read_inputs
from src.psx_player import graphics_bank,composition_frame,decode_stream
from src.psx_frame_edit import frame_coverage
P=Path(__file__).parent
B=ROOT/'out/ver_buki_riko/riko_motion_20261023T140114425399Z'
_,_,_,_,g,p,_=read_inputs(ROOT/'work/ver_buki_riko/zero_extract/20261023T062408235550Z')
bank=graphics_bank(g,0);world={};images={};geo={}
for n in range(7,21):
 f=bank['frames'][n];c=composition_frame(p,0,n);raw=decode_stream(g,f['offset'],f['limit'],f['tile_count']*128).data
 coverage,size,b=frame_coverage(raw,f['tile_count'],c);geo[n]={'size':size,'bounds':b}
 a=np.array(Image.open(B/f'frame_{n:03d}.png'));w=np.zeros((72,96),dtype=np.uint8);w[40+b[1]:40+b[3],48+b[0]:48+b[2]]=a;world[n]=w
 im=Image.new('RGBA',(64,72));im.alpha_composite(Image.open(B/f'frame_{n:03d}.png').convert('RGBA'),(32+b[0],40+b[1]));images[n]=im
report=[]
for n in range(7,21):
 nxt=7 if n==20 else n+1;a,b=world[n],world[nxt];ua=(a!=0)|(b!=0)
 report.append({'from':n,'to':nxt,'changed_pixels':int(np.sum(a!=b)),
  'upper_changed_pixels':int(np.sum(a[:48]!=b[:48])),
  'silhouette_xor':int(np.sum((a!=0)^(b!=0))),
  'foot_bottom_delta':int(np.nonzero(b)[0].max()-np.nonzero(a)[0].max())})
(P/'before_loop_metrics.json').write_text(json.dumps(report,indent=2))
(P/'geometry.json').write_text(json.dumps(geo,indent=2))
font=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',17)
board=Image.new('RGBA',(256*6,320*2),(42,45,54,255));d=ImageDraw.Draw(board)
for row,seq in enumerate(([11,12,13,14,15,16],[18,19,20,7,8,9])):
 for j,n in enumerate(seq):
  board.alpha_composite(images[n].resize((256,288),Image.Resampling.NEAREST),(j*256,row*320+32));d.text((j*256+6,row*320+3),str(n),font=font,fill='white')
board.save(P/'before_boundaries.png')
reference=Image.new('RGBA',(128,72))
for j,n in enumerate((14,7)):reference.alpha_composite(images[n],(j*64,0))
reference.resize((1024,576),Image.Resampling.NEAREST).save(P/'next_contact_reference.png')
print(json.dumps([r for r in report if r['from'] in (12,13,19,20)]))
