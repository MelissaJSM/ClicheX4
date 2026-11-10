from pathlib import Path
import sys,json
import numpy as np
from PIL import Image
from scipy.ndimage import label
D=Path(__file__).resolve().parent;W=D.parent;ROOT=W.parents[1];sys.path[:0]=[str(ROOT),str(W/'nana_audit/native_restore')]
from preview_restore import Archive
a=Archive((W/'root_nana_shot87/packed_settle01/PL00_U.ARC').read_bytes());ls={pb:np.array(Image.open(D/f'body_layers_probe01/layer{pb}_229.png'))for pb in(0,8)};new=ls[0].copy();new[ls[8]>0]=ls[8][ls[8]>0];old=a.layer(229,0)[0];leg=a.layer(229,8)[0];old[leg>0]=leg[leg>0]
meta=json.loads((W/'zero_audit/nana_ultimate_hover_relations01/conclusions.json').read_text('utf8'));q=next(q for q in meta['effect_frames']if q['effect_frame']==12);jet=np.load(ROOT/q['source_dump'])
for name,z in [('old',old),('new',new),('jet12',jet)]:
 print(name,'x=-20..12,y=-1..35')
 for y in range(-1,36):print(str(y).rjust(3)+''.join('.'if not v else format(int(v),'x')for v in z[y+160,140:173]))
