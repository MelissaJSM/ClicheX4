from pathlib import Path
import sys,json,hashlib
import numpy as np
W=Path(__file__).resolve().parent;ROOT=W.parents[1];sys.path.insert(0,str(ROOT))
from scripts.export_x_consistency import Archive,page
D=W/'root_nana_special';D.mkdir(exist_ok=False)
data=(W/'root_nana_lowhp/packed_lowhp01/PL00_U.ARC').read_bytes();assert hashlib.sha256(data).hexdigest()=='ac1e35b7131d3909a93ea3466859aa9d7278c431d72defcb261b2b76cd1f6e16';a=Archive(data)
for form,mask in(('base',0),('fourth',15)):
 page([(f'{form} {n}',a.composite(n,mask)[0])for n in(85,89,95,96,97,98,99)],a.composite(0,mask)[0],D/f'{form}_current.png',cols=3,scale=5)
rows=[]
for n in(85,89,95,96,97,98,99):
 rows.append({'ref':n,'stream':a.banks[0]['frames'][n]['offset'],'layers':{pb:a.layer(n,pb)[1]['bounds']for pb in(0,5,6,7,8)}})
(D/'source.json').write_text(json.dumps({'parent_sha256':hashlib.sha256(data).hexdigest(),'frames':rows},indent=2)+'\n','utf8');print('native inspection ready')
