import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT))
from scripts.prepare_nana_pause import *
from scripts.build_nana_pause import validate
art=ART/'native01';repro=ART/'repro01';m,records,raw=sources();new={n:(art/n).read_bytes()for n in raw};indices=Image.open(art/'portrait.png').tobytes();passed=[]
def reject(name,fn):
    try:fn()
    except ValueError:passed.append(name)
    else:raise AssertionError('Bad input accepted: '+name)
for n in raw:
    for label,kind,pos in [('body',2,64),('coordinates',0x12,80),('other_menu_pixel',0x10007,64),('other_palette',0x11,2)]:
        b=bytearray(entry(new[n],kind));b[pos]^=1;bad=replace_entry(new[n],kind,bytes(b));reject(n+label,lambda n=n,bad=bad:verify(raw[n],bad,indices))
reject('same_reproduction',lambda:validate(art,art));reject('outside_art_path',lambda:validate(ROOT,repro));validate(art,repro)
(ART/'checks.json').write_text(json.dumps({'negative_cases_passed':passed,'count':len(passed),'valid_candidate_passed':True},indent=2)+'\n','utf8');print(json.dumps({'passed':len(passed)}))
