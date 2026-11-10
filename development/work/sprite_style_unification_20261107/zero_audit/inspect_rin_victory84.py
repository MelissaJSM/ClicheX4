"""Inspect remaining victory artwork and effect sharing; no art/ARC writes."""
from pathlib import Path
import sys,json,hashlib,struct
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from scripts.overhaul_sprites_audit import render,rgba
from scripts.prepare_riko_ui import entry
from scripts.export_x_consistency import page
from src.psx_player import graphics_bank
D=Path(__file__).parent/'rin_extension';P=D/'prepared_rising_rear_v1/PL01_U.ARC';O=D/'victory_after84';O.mkdir(exist_ok=True)
arc=P.read_bytes();assert hashlib.sha256(arc).hexdigest()=='223e553f97ecc85d52b085f3e0e6cd46ecc914063f1adcef43fd1d34c25d298e';bank=graphics_bank(entry(arc,2),1)
arrays={n:render(arc,1,5,n)[0]for n in range(8)};rows=[]
for n,a in arrays.items():
 y,x=np.nonzero(a);f=bank['frames'][n]
 rows.append({'ref':n,'bbox':None if not len(x)else[int(x.min()),int(y.min()),int(x.max()+1),int(y.max()+1)],'opaque':int(len(x)),'tiles':f['tile_count'],'shared_stream':[s['index']for s in bank['frames']if s['offset']==f['offset']],'exact_display_aliases':[m for m,z in arrays.items()if m!=n and np.array_equal(a,z)]})
for form,row in [('normal',0),('black',13)]:
 pal=struct.unpack_from('<16H',entry(arc,9),row*32)
 page([(f'b1:{n}',rgba(a,pal))for n,a in arrays.items()],rgba(render(arc,0,0,147)[0],pal),O/f'{form}_0_to_7.png',cols=4,scale=5)
 # Effect rendering uses original32 palette words for mixed CLUT references.
mixed=struct.unpack_from('<64H',entry(arc,9));rgba(arrays[7],mixed).save(O/'b1_007_actual_palette.png')
diff=[]
for a,b in[(0,1),(1,2),(3,4),(5,6),(6,7)]:
 mask=arrays[a]!=arrays[b];y,x=np.nonzero(mask);diff.append({'a':a,'b':b,'changed_pixels':int(len(x)),'bbox':None if not len(x)else[int(x.min()),int(y.min()),int(x.max()+1),int(y.max()+1)]})
j={'source':str(P.relative_to(ROOT)),'sha256':hashlib.sha256(arc).hexdigest(),'rows':rows,'differences':diff,'art_review_pending':True,'game_unchanged':True}
(O/'analysis.json').write_text(json.dumps(j,ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps(j))
