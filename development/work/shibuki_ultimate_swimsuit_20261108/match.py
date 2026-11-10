"""실제 프레임버퍼와 재삽입 의상 픽셀을 비교한다. 게임 쓰기 없음."""
from pathlib import Path
import json,sys
import numpy as np
from PIL import Image,ImageDraw
H=Path(__file__).resolve().parent;ROOT=H.parents[1];sys.path[:0]=[str(ROOT),str(ROOT/'work/motion_fixes_20261108')]
from common import write
from scripts.export_x_consistency import Archive
from src.epsxe_state import match_sprite
a=Archive((H/'PL02_fixed.ARC').read_bytes());review=ROOT/'out/ver_buki_riko/ultimate_costume_unified_20261108_v1/review'
dirs=['runtime_fire_hover','runtime_specials','runtime_double'];screens=[]
for name in dirs:
 for p in sorted((H/name).glob('b0_*page*.png')):screens.append((p,Image.open(p).convert('RGB')))
rows=[];pics=[]
for n in [85,86,87,88,89,90,91,92,221,223,224,229,230]:
 native=a.composite(n,15 if 217<=n<=230 else 0)[0];full=native.crop(native.getbbox())
 mask=np.array(Image.open(H/f'expanded/mask_{n:03}.png'))>0;pixels=np.array(native);pixels[~mask]=0;garment=Image.fromarray(pixels);box=garment.getbbox();crop=garment.crop(box)
 full_matches=[];garment_matches=[]
 ordered=sorted(screens,key=lambda item:f'_{n:03}_' not in item[0].name)
 for p,screen in ordered:
  if not full_matches:
   found=match_sprite(screen,full)
   if found:full_matches.append({'file':p.relative_to(ROOT).as_posix(),**found[0]})
  if not garment_matches:
   found=match_sprite(screen,crop)
   if found:
    f=found[0];garment_matches.append({'file':p.relative_to(ROOT).as_posix(),**f});x,y=f['x'],f['y'];w,h=crop.size
    actual=screen.crop((x-25,y-28,x+w+25,y+h+22));actual=actual.resize((actual.width*4,actual.height*4),Image.Resampling.NEAREST)
    pics.append((f'{n}: garment {f["opaque_pixels_equal"]} exact pixels',actual))
  if full_matches and garment_matches:break
 rows.append({'ref':n,'full_sprite_matches':full_matches,'garment_matches':garment_matches})
print([(r['ref'],bool(r['full_sprite_matches']),bool(r['garment_matches'])) for r in rows],flush=True)
for offset in range(0,len(pics),6):
 selected=pics[offset:offset+6];board=Image.new('RGB',(1200,((len(selected)+2)//3)*350),(26,34,48));draw=ImageDraw.Draw(board)
 for i,(label,pic) in enumerate(selected):x=i%3*400;y=i//3*350;board.paste(pic,(x+8,y+30));draw.text((x+8,y+6),label,fill='white')
 board.save(review/f'actual_{offset//6:02}.png')
write(H/'pixel_matches.json',{'rows':rows,'full_matched':sum(bool(r['full_sprite_matches']) for r in rows),'garments_matched':sum(bool(r['garment_matches']) for r in rows),'tested_refs':len(rows),'scope':'실제 프레임버퍼에서 의상 마스크의 불투명 RGB 픽셀 전부 일치. 전신 일치와 별도 집계. 실제 특수무기 전수 검사는 아님.'})
