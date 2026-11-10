import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from scripts.prepare_nana_hud_theme import *
from scripts.build_nana_hud_theme import validate
art=ART/'native01';repro=ART/'repro01';m,recs,raw,pal=sources();a=np.array(Image.open(art/'overlay.png'));passed=[]
def reject(name,fn):
    try:fn()
    except(ValueError,AssertionError):passed.append(name)
    else:raise AssertionError('Bad input accepted: '+name)
reject('wrong_size',lambda:patch(raw['PL00_U.ARC'],a[:12]));b=a.copy();b[2,8]=16;reject('invalid_index',lambda:patch(raw['PL00_U.ARC'],b));b=a.astype(float);reject('float_indices',lambda:patch(raw['PL00_U.ARC'],b));b=a.copy();b[a==0]=14;reject('paint_transparent',lambda:patch(raw['PL00_U.ARC'],b));b=a.copy();b[a!=0]=0;reject('erase_native_alpha',lambda:patch(raw['PL00_U.ARC'],b));reject('same_reproduction',lambda:validate(art,art));reject('outside_art_path',lambda:validate(ROOT,repro));validate(art,repro)
(ART/'checks.json').write_text(json.dumps({'negative_cases_passed':passed,'count':len(passed),'valid_candidate_passed':True},indent=2)+'\n','utf8');print(json.dumps({'passed':len(passed)}))
