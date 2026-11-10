import sys,json,shutil
from pathlib import Path
import numpy as np
R=Path(__file__).resolve().parents[3];sys.path.insert(0,str(R))
from scripts.prepare_nana_life_revision import ART,sources,head,patch
from scripts.build_nana_life_revision import validate
_,_,raw,pal=sources();h,_=head(pal);a=raw['PL00_U.ARC'];passed=[]
def rejects(name,f):
 try:f()
 except ValueError:passed.append(name);return
 raise AssertionError(name+' was accepted')
rejects('wrong_head_shape',lambda:patch(a,h[:15]))
rejects('out_of_range_index',lambda:patch(a,np.full((16,16),16,np.uint8)))
rejects('float_indices',lambda:patch(a,h.astype(float)))
rejects('same_reproduction',lambda:validate(ART/'face_v2',ART/'face_v2'))
pair=ART/'face_negative_unowned_palette';pair.mkdir()
from scripts.discover_inputs import psx_arc,sha256
e=next(e for e in psx_arc(a)if e['type']=='0x9')
for side in('a','b'):
 d=pair/side;shutil.copytree(ART/'face_v2',d);p=d/'PL00_U.ARC';b=bytearray(p.read_bytes());b[e['offset']+4]^=1;p.write_bytes(b);rp=d/'recipe.json';r=json.loads(rp.read_text('utf8'))
 for q in r['files']:
  if q['file']=='PL00_U.ARC':q['sha256']=sha256(b)
 rp.write_text(json.dumps(r,indent=2)+'\n','utf8')
rejects('rebound_unowned_palette',lambda:validate(pair/'a',pair/'b'))
validate(ART/'face_v2',ART/'face_repro_v2');(ART/'face_checks.json').write_text(json.dumps({'negative_cases':passed,'count':len(passed),'valid_candidate_passed':True},indent=2)+'\n','utf8');print(passed)
