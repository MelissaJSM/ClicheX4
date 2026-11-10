from pathlib import Path
import sys,json,hashlib
D=Path(__file__).resolve().parent;W=D.parent;ROOT=W.parents[1];sys.path.insert(0,str(ROOT))
from scripts.export_x_consistency import Archive,page
src=W/'root_nana_arrival/packed_arrival01/PL00_U.ARC';data=src.read_bytes();sha=lambda b:hashlib.sha256(b).hexdigest()
assert sha(data)=='9599ca5fc21828df5ef4d865eafab4d27aa06a7b2391873a063c887120e70f91'
a=Archive(data);out=D/'existing01';out.mkdir(exist_ok=False)
for form,mask in [('base',0),('fourth',15)]:
 page([(str(n),a.composite(n,mask)[0]) for n in (156,157,158,204,205,206,207)],a.composite(0,mask)[0],out/f'{form}.png',cols=3,scale=4)
(out/'manifest.json').write_text(json.dumps({'parent_arc':src.relative_to(ROOT).as_posix(),'parent_sha256':sha(data),'refs':[156,157,158,204,205,206,207],'runtime_verified':False},indent=2)+'\n','utf8')
print('existing base/Fourth victory and return contact sheets prepared')
