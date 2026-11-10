from pathlib import Path
import sys,json,hashlib,struct
from PIL import Image
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from scripts.overhaul_sprites_audit import render,rgba
from scripts.prepare_riko_ui import entry
P=Path(__file__).resolve().parent/'prepared_rising_clothes_v1/PL01_U.ARC';arc=P.read_bytes();assert hashlib.sha256(arc).hexdigest()=='dd61d2f1b77cab1c43256dd6e2553f631067100338352c86aaea1d5d41eddec7'
D=P.parent.parent/'ceremony_clothes16';D.mkdir(exist_ok=False);pal=struct.unpack_from('<16H',entry(arc,9));crop=(112,112,208,208)
for page,refs in enumerate([[(0,249),(0,250)],[(0,251),(0,252)],[(0,253),(1,2)],[(1,3),(1,4)],[(1,6)]],1):
 p=D/f'page{page}';p.mkdir();sheet=Image.new('RGBA',(1536,1536));frame_keys=refs+([(1,5)]if len(refs)==1 else[])+[(0,147),(1,5)];rows=[]
 for i,(b,n)in enumerate(frame_keys):
  im=rgba(render(arc,b,b*5,n)[0],pal);im.save(p/f'b{b}_{n:03}_source.png');sheet.paste(im.crop(crop).resize((768,768),Image.Resampling.NEAREST),(i%2*768,i//2*768));rows.append({'bank':b,'ref':n,'cell':i})
 sheet.save(p/'targets.png')
 prompt='''Locally refine ONLY the TOP TWO sprites of this transparent 2x2 game sprite sheet; BOTTOM TWO are finished reference sprites that must stay exactly as supplied. Each cell is96x96 original game pixels shown8x. Keep all four cell positions, exact original body size, head outline, face, hand, foot, knee and cape positions. Do not enlarge or recenter any sprite. Character is Riko in Mega Man X4: green bob hair, white fitted military jacket with thin navy/gray lapel and cuff seams, short white pleated skirt, teal-lined attached white cape, white segmented knee boots. Match the fine native pixel clusters of the BOTTOM idle and side-facing finished victory reference. Refine only the upper two sprites' too-flat sleeves, collar, skirt folds and boot joints. Keep their original body facing, gestures, silhouettes and head/foot coordinates unchanged. No extra gold buttons, weapons, glow, labels, floor or shadows. Selective thin outlines and compact clear shadow clusters, no blur or soft illustration. Do not repaint the fine hair or alter the head proportions. Transparent background. Preserve all positions and sizes exactly: this is a pixel-art clothing detail correction, not a new composition.'''
 if len(refs)==1:prompt=prompt.replace('ONLY the TOP TWO sprites','ONLY the TOP LEFT sprite').replace('BOTTOM TWO are finished reference sprites','the other THREE are locked finished reference sprites').replace("upper two sprites'","top-left sprite's")
 (p/'prompt.txt').write_text(prompt,'utf8');(p/'inputs.json').write_text(json.dumps({'parent':str(P.relative_to(ROOT)),'sha256':hashlib.sha256(arc).hexdigest(),'native_cell':[96,96],'grid':[2,2],'crop':crop,'frames':rows,'apply_only_keys':[list(x)for x in refs]},indent=2),'utf8')
print(D)
