import sys,json
from pathlib import Path
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT))
from scripts.solve_paired_cover import paired_cover
d=Path(__file__).parent;p=d/'paired02';plan=json.loads((d/'plan.json').read_text());results=[]
previous=json.loads((d/'layout02.json').read_text()) if (d/'layout02.json').exists() else []
for pair in plan['paired_frames']:
 n=pair['frames'][0];old=next((r for r in previous if r['frame']==n and r['fits']),None)
 if old:results.append(old);continue
 a=np.array(Image.open(p/f'run_{n:03d}.png'));b=np.array(Image.open(p/f'shoot_{n:03d}.png'));counts=[len(pair[k]) for k in ('common_base_tiles','nonshoot_only_tiles','shoot_only_tiles')]
 r=paired_cover(a,b,counts,12);r.update(frame=n,mode='variant',counts=counts);results.append(r);(d/'layout02.json').write_text(json.dumps(results+[q for q in previous if q['frame']>n],indent=2));print(json.dumps(r),flush=True)
(d/'layout02.json').write_text(json.dumps(results,indent=2))
