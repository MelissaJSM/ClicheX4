import json,sys
from pathlib import Path
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT))
from scripts.solve_sprite_cover import cover
d=Path(__file__).parent;a=d/'production02';p=json.loads((d/'plan.json').read_text());records=[]
for n in (143,144,146,149,151,153,154,183):
 q=next(r for r in p['groups'] if r['frame']==n);count=min(q['part_count'],len(q['writable'])-(n in (144,146,149,151)));mask=np.array(Image.open(a/f'frame_{n:03d}.png'))!=0;r=cover(mask,count,8);r.update(frame=n);records.append(r);print(r,flush=True)
(a/'draft_layout.json').write_text(json.dumps(records,indent=2))
