from pathlib import Path
import sys,json,struct,hashlib
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from scripts.prepare_rin_run import quantize
from scripts.prepare_riko_ui import entry
from scripts.overhaul_sprites_audit import rgba
D=Path(__file__).parent/'rin_extension';arc=(D/'prepared_third_saber_v1/PL01_U.ARC').read_bytes();pal=struct.unpack_from('<16H',entry(arc,9));colors=np.array([[(w>>s&31)*255//31 for s in(0,5,10)]for w in pal[1:]],np.int32)
for n,h in[(186,'b079b9f7220371ef15d0bc6c3473396df73f3d710fc1d8cd8b81a5a581a13089'),(190,'e83cd48ddd3facb5a6aa931225724954dabc4c311bcc1763b16c5562107bb195')]:
 O=D/f'rear_leg_fix_{n}';p=O/'generated.png';assert hashlib.sha256(p.read_bytes()).hexdigest()==h;im=Image.open(p).convert('RGBA');assert im.size==(1536,1024)
 a=np.zeros((384,384),np.uint8);a[120:184,112:208]=quantize(im,colors,1/16);Image.fromarray(a).save(O/'generated_native_indices.png');rgba(a,pal).save(O/'generated_native_normal.png')
 rows=[]
 for y in range(159,181):
  xs=np.where(a[y,154:171]>0)[0]+154;rows.append([y,xs.tolist()])
 print(n,rows)
