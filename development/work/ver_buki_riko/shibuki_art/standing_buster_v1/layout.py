import sys,json
from pathlib import Path
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT))
from scripts.solve_sprite_cover import cover
d=Path(__file__).parent/'production01';rows=[]
for n in (85,86,87,92):
 r=cover(np.array(Image.open(d/f'standing_{n:03d}.png'))!=0,6 if n==92 else 7,20);r['frame']=n;rows.append(r);print(r,flush=True)
(d/'layout.json').write_text(json.dumps(rows,indent=2))
