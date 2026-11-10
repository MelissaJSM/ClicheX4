from pathlib import Path
import sys,json
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT))
from scripts.solve_sprite_cover import cover
from src.psx_player import composition_frame
d=Path(__file__).parent;comp=(ROOT/'work/ver_buki_riko/shibuki_x_extract/20261026T024200768121Z/composition_entry.bin').read_bytes();results=[]
for n in range(1,33,2):
 a=np.array(Image.open(d/f'production/run_{n:03d}.png'));count=len(composition_frame(comp,0,n)['parts'])
 result={'frame':n,**cover(a!=0,count,2)};results.append(result);print(json.dumps(result),flush=True)
(d/'whole_body_fit.json').write_text(json.dumps(results,indent=2))
