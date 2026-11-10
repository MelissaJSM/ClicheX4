from pathlib import Path
import sys,json
from PIL import Image,ImageDraw
H=Path(__file__).resolve().parent;ROOT=H.parents[1];sys.path.insert(0,str(ROOT))
from common import write
from scripts.export_x_consistency import Archive
from src.epsxe_state import match_sprite
reports=[];review=ROOT/'out/motion_fixes_20261108_review'
for folder,mode,resource,refs in [('runtime_nana_base2','ver_rin_nana','PL00',[0,33,37,43,47,49,51,67,69,71,75,68,72,76]),('runtime_rin_dash','ver_rin_nana','PL01',[0,44,46,47,48,50]),('runtime_shibuki_dash','ver_buki_riko','PL00',[0,68,70,72,74,76,78,80,84])]:
 d=H/folder
 if not (d/'report.json').exists():continue
 a=Archive((H/mode/(resource+'_fixed.ARC')).read_bytes());rows=[];pics=[]
 for n in refs:
  sprite=a.rgba(a.layer(n)[0]) if resource=='PL01' else a.composite(n)[0]
  bbox=sprite.getbbox();crop=sprite.crop(bbox);matches=[]
  # Uploaded frame can lead displayed framebuffer by one native draw cycle.
  for p in sorted(d.glob('b0_*_page*.png')):
   screen=Image.open(p);m=match_sprite(screen,crop)
   if m:
    match=m[0];matches.append({'file':p.relative_to(ROOT).as_posix(),**match})
    x,y=match['x'],match['y'];w,h=crop.size;piece=screen.crop((x-8,y-8,x+w+8,y+h+8)).resize(((w+16)*4,(h+16)*4),Image.Resampling.NEAREST)
    pics.append((f'{n} '+('right' if match['flip_x'] else 'left'),piece));break
  rows.append({'frame':n,'matched':bool(matches),'evidence':matches})
 board=Image.new('RGB',(1000,((len(pics)+3)//4)*320),(25,32,44));dr=ImageDraw.Draw(board)
 for i,(label,pic) in enumerate(pics):x=i%4*250;y=i//4*320;board.paste(pic,(x+8,y+30));dr.text((x+8,y+8),label,fill='white')
 board.save(review/(folder+'_actual.png'));reports.append({'runtime':folder,'rows':rows,'matched_count':sum(r['matched'] for r in rows),'requested':len(refs)})
write(H/'live_pixel_matches.json',reports);print([(r['runtime'],r['matched_count'],r['requested']) for r in reports])
