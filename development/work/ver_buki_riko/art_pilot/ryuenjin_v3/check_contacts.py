from pathlib import Path
import sys,json
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT))
import numpy as np
from work.ver_buki_riko.art_pilot.wall_saber_v1.fit_wall import original
D=Path(__file__).parent;worlds=np.load(D/'final_worlds.npz');rows=[]
anchors={144:(-9,8),146:(-27,14),148:(-14,-39),150:(-14,-39),152:(-14,-39),154:(-14,-39),156:(5,-37),158:(9,-30)}
for n,(x,y) in anchors.items():
 e,b,_=original(n+1);ey,ex=np.nonzero(e);ex+=b[0];ey+=b[1];distance=np.maximum(abs(ex-x),abs(ey-y));best=int(distance.argmin());row={'body':n,'effect':n+1,'hilt_tip':[x,y],'body_tip_opaque':bool(worlds[str(n)][96+y,96+x]),'nearest_effect_pixel':[int(ex[best]),int(ey[best])],'chebyshev_distance':int(distance[best])};rows.append(row)
(D/'contact_checks.json').write_text(json.dumps(rows,indent=2),'utf8');print(json.dumps(rows))
