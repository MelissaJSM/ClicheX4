from pathlib import Path
import sys,json,hashlib
import numpy as np
D=Path(__file__).resolve().parent;W=D.parent;ROOT=W.parents[1];sys.path.insert(0,str(ROOT))
from scripts.export_x_consistency import Archive,page
src=W/'root_nana_return/packed_return03/PL00_U.ARC';data=src.read_bytes();sha=lambda b:hashlib.sha256(b).hexdigest();assert sha(data)=='6823c51d79f45beb3eeee8a9a2ec4a73aa1e067c5e1465d4325d6e4cf8c8ebf9';a=Archive(data)
out=D/'existing01';out.mkdir(exist_ok=False);refs=list(range(162,175));rows=[]
for form,mask in [('base',0),('fourth',15)]:
 page([(str(n),a.composite(n,mask)[0])for n in refs],a.composite(0,mask)[0],out/f'{form}.png',cols=4,scale=4)
 for n in refs:
  q=a.composite(n,mask)[0];q.save(out/f'{form}_{n:03}.png');rows.append({'ref':n,'form':form,'rgba_sha256':sha(q.tobytes()),'bbox':q.getbbox()})
matches=[]
for n in refs:
 if n in (162,166,170,174):continue
 group=162 if n<166 else 166 if n<170 else 170
 for form,mask in [('base',0),('fourth',15)]:
  b=np.array(a.composite(group,mask)[0]);q=np.array(a.composite(n,mask)[0]);found=[]
  for dy in range(-4,5):
   for dx in range(-4,5):
    if np.array_equal(np.roll(np.roll(b,dy,0),dx,1),q):found.append([dx,dy])
  matches.append({'form':form,'ref':n,'source':group,'exact_rgba_translations':found})
(out/'manifest.json').write_text(json.dumps({'parent_arc':src.relative_to(ROOT).as_posix(),'parent_sha256':sha(data),'refs':refs,'frames':rows,'translation_checks':matches,'runtime_verified':False},indent=2)+'\n','utf8');print(json.dumps(matches))
