from pathlib import Path
import json,sys
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT))
from scripts.extract_zero import save_image
d=Path(__file__).parent;src=d/'normalized';out=d/'production';out.mkdir(exist_ok=False)
art=json.loads((src/'art.json').read_text());inv=json.loads((ROOT/art['source_inventory']).read_text())
idle=np.array(Image.open(ROOT/'work/ver_buki_riko/shibuki_art/idle_chubby_v2/candidate09/shibuki_idle000_indexed.png'))
for r in art['frames']:
 n=r['frame'];a=np.array(Image.open(src/r['image']));target=np.zeros_like(a)
 if n in (1,3):
  target[15:63,29:77]=idle;r['reuses_accepted_idle_exactly']=True
 else:
  oldx,oldy=r['world_position'];w,h=r['native_size'];pic=a[oldy+40:oldy+40+h,oldx+48:oldx+48+w]
  top=inv['base_frames'][n]['opaque_bbox'][3]+inv['base_frames'][n]['bounds'][1]-h
  target[top+40:top+40+h,oldx+48:oldx+48+w]=pic;r['world_position']=[oldx,top]
 save_image(target.tobytes(),(96,80),art['palette_words'],out/r['image'])
 r['opaque_pixels']=int(np.count_nonzero(target))
art.update(design_basis='idle_chubby_v2/candidate09 human face and clothing; user rollback',idle_art_changed=False,game_applied=False,runtime_verified=False)
(out/'art.json').write_text(json.dumps(art,indent=2));print(out)
