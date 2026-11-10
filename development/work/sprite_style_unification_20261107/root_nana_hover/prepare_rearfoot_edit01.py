from pathlib import Path
import sys,json,hashlib
import numpy as np
from PIL import Image,ImageDraw
D=Path(__file__).resolve().parent;W=D.parent;ROOT=W.parents[1];sys.path[:0]=[str(ROOT),str(W/'nana_audit/native_restore')]
from preview_restore import Archive
a=Archive((W/'root_nana_shot87/packed_settle01/PL00_U.ARC').read_bytes());ls={pb:np.array(Image.open(D/f'body_layers_probe01/layer{pb}_229.png'))for pb in(0,5,6,7,8)};out=D/'rearfoot_edit01';out.mkdir(exist_ok=False)
source=Image.new('RGBA',(1536,768));old=source.copy();guide=source.copy()
for i,mask in enumerate((8,15)):
 im=a.rgba(ls[0])
 for bit,pb in((8,8),(1,5),(4,7),(2,6)):
  if mask&bit:im.alpha_composite(a.rgba(ls[pb],32 if pb==7 else 16))
 part=im.crop((112,112,208,208)).resize((768,768),Image.Resampling.NEAREST);source.alpha_composite(part,(i*768,0));guide.alpha_composite(part,(i*768,0));old.alpha_composite(a.composite(229,mask)[0].crop((112,112,208,208)).resize((768,768),Image.Resampling.NEAREST),(i*768,0))
 dr=ImageDraw.Draw(guide);x=i*768+(48-3)*8;y=(48+16)*8;dr.ellipse((x-10,y-10,x+10,y+10),outline='#00ffff',width=3)
for name,im in [('current',source),('original_pose',old),('contact_guide',guide)]:im.save(out/f'{name}.png')
prompt='''Edit the FIRST transparent pixel-art sprite image. Two identical adult game-character hover poses side by side: LEFT short dark cap outfit, RIGHT long dark veil outfit. Make only one tiny anatomical correction to the folded leg and its small dark magenta shoe. The third image marks the required position with a cyan circle: the sole/toe of the shoe of the BENT leg must extend slightly LEFT to that circle, about four native pixels left, while its knee stays fixed. The SECOND image shows the older accepted pose for leg/propulsion alignment only; do not copy its simpler art or alter the rest of the current design. The other leg hangs vertically, with its foot at the very bottom: leave that straight leg and bottom shoe exactly unchanged. Keep the folded thigh/knee fixed, bend its lower shin naturally to connect to the tiny left-facing dark magenta shoe with a clear ankle and readable toe. Preserve the continuous fine dark contour and small lighter edge accents. No thick black ankle blob and no bare disconnected foot.
Keep exactly the same two-cell framing, pixel scale, transparent background, head, green eyes, hair strands, veil, raised arm, lowered hand, uniform, skirt, torso, hips and all pixels outside this small folded-leg shin/shoe region. Preserve the same costume coverage. Do not shift or resize either whole character. Both outfits use the same corrected leg/foot pose. Remove all cyan guides from the result. No effect, flames, labels, scenery, motion blur or extra parts. Pixel-art sheet, same 1536 by768 framing. This is only a small lower-shin/boot pose edit, not a character redesign.'''
(out/'prompt.txt').write_text(prompt,'utf8');(out/'manifest.json').write_text(json.dumps({'target_refs':[229,230],'target_toe_world':[-3,16],'straight_leg_and_other_body_fixed':True,'input_files':{p.name:hashlib.sha256(p.read_bytes()).hexdigest()for p in out.iterdir()if p.is_file()},'reason':'최저발Y만 맞춘229의 접힌쪽 발이 왼쪽 원추진기에서 벌어진 정적 후보. 국소 발원화만 새로 검토.'},ensure_ascii=False,indent=2)+'\n','utf8')
print('rearfoot fixed-cell edit inputs ready')
