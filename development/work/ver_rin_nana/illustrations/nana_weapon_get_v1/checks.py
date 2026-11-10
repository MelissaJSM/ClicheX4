import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT))
from scripts.prepare_nana_weapon_get import *
from scripts.build_nana_weapon_get import validate
art=ART/'native01';repro=ART/'repro01';records,original=sources();new={n:(art/n).read_bytes()for n in original};picture=np.array(Image.open(art/'action.png'));passed=[]
def reject(name,fn):
    try:fn()
    except(ValueError,AssertionError):passed.append(name)
    else:raise AssertionError('Bad input accepted: '+name)
for n in SCREENS:
    bad=dict(new);bad[n]=original[n];reject('missing_copy_'+n,lambda bad=bad:verify(original,bad,picture))
for name,file,kind,at in [('rin_palette','COL0F_U0.ARC',5,80*32+2),('other_palette','COL0E_U0.ARC',5,0),('logo_map','ST0F_UX.ARC',0,0)]:
    bad=dict(new);a=bytearray(entry(bad[file],kind));a[at]^=1;bad[file]=replace_entry(bad[file],kind,bytes(a));reject(name,lambda bad=bad:verify(original,bad,picture))
bad=dict(new);name='ST0E_U0.ARC';g=bytearray(entry(bad[name],0x10000));tid=struct.unpack_from('<I',entry(bad[name],1))[0]>>16&4095;g[tid//16*2048+tid%16*8]^=1;bad[name]=replace_entry(bad[name],0x10000,bytes(g));reject('transparent_tile',lambda:verify(original,bad,picture))
badpic=picture.copy();badpic[20,220]=1;reject('outside_art_box',lambda:verify(original,new,badpic))
reject('same_reproduction',lambda:validate(art,art));reject('outside_art_directory',lambda:validate(ROOT,repro));validate(art,repro)
(ART/'checks.json').write_text(json.dumps({'negative_cases_passed':passed,'count':len(passed),'valid_candidate_passed':True},indent=2)+'\n','utf8');print(json.dumps({'passed':len(passed)}))
