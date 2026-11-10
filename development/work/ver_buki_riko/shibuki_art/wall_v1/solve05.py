import json,sys
from pathlib import Path
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT))
from scripts.solve_paired_cover import paired_cover
d=Path(__file__).parent;a=d/'production05';plan=json.loads((d/'plan.json').read_text());results=[]
for p in plan['paired_frames']:
    n=p['frames'][0];normal=np.array(Image.open(a/f'run_{n:03d}.png'));shot=np.array(Image.open(a/f'shoot_{n:03d}.png'))
    counts=[len(p[k]) for k in ('common_base_tiles','nonshoot_only_tiles','shoot_only_tiles')]
    r={**paired_cover(normal,shot,counts,15),'frame':n,'mode':'variant'};results.append(r);print({'frame':n,'counts':counts,'fits':r['fits']},flush=True)
    (d/'layout05.json').write_text(json.dumps(results,indent=2))
