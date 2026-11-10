from pathlib import Path
import sys,json
import numpy as np
from PIL import Image,ImageDraw
H=Path(__file__).resolve().parent;ROOT=H.parents[1];sys.path[:0]=[str(ROOT),str(ROOT/'work/motion_fixes_20261108')]
from common import write
from scripts.export_x_consistency import Archive
from src.epsxe_state import match_sprite
a=Archive((H/'PL02_fixed.ARC').read_bytes());review=ROOT/'out/ver_buki_riko/ultimate_wrist_20261108_v3/review';rows=[]
for form,mask in [('before',15),('after',0)]:
 d=H/('final_runtime_'+form);r=json.loads((d/'report.json').read_text('utf8'));assert r['visual_mask']==mask
 screens=[(p,Image.open(p).convert('RGB')) for p in sorted(d.glob('b0_*page*.png'))];pics=[]
 for n in (68,70,72,74,76):
  native=a.composite(n,mask)[0];bbox=native.getbbox();full=native.crop(bbox);matches=[]
  for p,screen in screens:
   found=match_sprite(screen,full)
   if found:matches.append({'file':p.relative_to(ROOT).as_posix(),**found[0]});break
  arm=np.array(native);allowed=np.array(Image.open(H/f'candidate/mask_{n:03}.png'))>0;arm[~allowed]=0;arm=Image.fromarray(arm);box=arm.getbbox();crop=arm.crop(box);hands=[]
  for p,screen in screens:
   found=match_sprite(screen,crop)
   if found:
    f=found[0];hands.append({'file':p.relative_to(ROOT).as_posix(),**f});x,y=f['x'],f['y'];w,h=crop.size
    actual=screen.crop((x-5,y-8,x+w+5,y+h+5));pics.append((f'{form} {n}: arm pixels {f["opaque_pixels_equal"]}',actual.resize((actual.width*6,actual.height*6),Image.Resampling.NEAREST)));break
  rows.append({'form':form,'ref':n,'full_sprite_matches':matches,'arm_matches':hands})
 board=Image.new('RGB',(900,((len(pics)+2)//3)*260),(26,34,48));draw=ImageDraw.Draw(board)
 for i,(label,pic) in enumerate(pics):x=i%3*300;y=i//3*260;board.paste(pic,(x+8,y+30));draw.text((x+8,y+6),label,fill='white')
 board.save(review/('actual_'+form+'.png'))
write(H/'pixel_matches.json',{'rows':rows,'full_matched':sum(bool(r['full_sprite_matches']) for r in rows),'arms_matched':sum(bool(r['arm_matches']) for r in rows),'tested_displays':len(rows),'scope':'실제 화면 불투명 픽셀 비교. 팔 비교는 수정 영역에 한정하고, 전신 비교와 별도 집계한다.'})
print([(r['form'],r['ref'],bool(r['full_sprite_matches']),bool(r['arm_matches'])) for r in rows])
