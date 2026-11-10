import sys,json
from pathlib import Path
import numpy as np
from PIL import Image
from cover_compact import paired_cover
d=Path(__file__).parent;a=d/'production05';records=json.loads((d/'layout_final.json').read_text())
a1=np.array(Image.open(a/'run_059.png'));b1=np.array(Image.open(a/'shoot_059.png'))
r=paired_cover(a1,b1,[6,1,2],40);r.update(frame=59,mode='variant');print(r,flush=True)
records=[r if x['frame']==59 else x for x in records];(d/'layout_alt.json').write_text(json.dumps(records,indent=2))
