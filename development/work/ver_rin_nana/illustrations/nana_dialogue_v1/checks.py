import json,sys
from pathlib import Path
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT))
from scripts.prepare_nana_dialogue import *
from scripts.build_nana_dialogue import validate
from scripts.prepare_riko_ui import replace_entry
art=ART/'native01';repro=ART/'repro01';r=json.loads((art/'recipe.json').read_text('utf8'));records,raw=read_sources();inv=locate(records,raw);orig={q['file']:raw[q['file']]for q in r['files']};new={n:(art/n).read_bytes()for n in orig};targets={n:np.array(Image.open(art/f'frame_{n}.png'))for n in range(8)};passed=[]
def reject(name,fn):
    try:fn()
    except ValueError:passed.append(name)
    else:raise AssertionError('Accepted bad input: '+name)
def corrupt_entry(file,kind,at):
    m=dict(new);data=bytearray(entry(m[file],kind));data[at]^=1;m[file]=replace_entry(m[file],kind,bytes(data));return m
for name,f,k,at in [('rin_texture','ST00_00.ARC',0x10102,217100),('unrelated_texture','ST00_00.ARC',0x10102,100),('rin_palette','COL00_0Z.ARC',5,63*32+2),('frame_header','ST00_00.ARC',10,30588+4)]:
    reject(name,lambda f=f,k=k,at=at:verify(orig,corrupt_entry(f,k,at),inv,targets,PAL))
for n in(0,4,7):
    c=aliased_composition(entry(new['ST00_00.ARC'],10),11,n);m=dict(new);p=bytearray(entry(m['ST00_00.ARC'],10));p[c['parts'][0]['record_offset']]|=4;m['ST00_00.ARC']=replace_entry(m['ST00_00.ARC'],10,bytes(p));reject('aux_clut_'+str(n),lambda m=m:verify(orig,m,inv,targets,PAL))
for name,y,x in [('face_drift',40,70),('bottom_gap',93,3)]:
    t={n:a.copy()for n,a in targets.items()};t[4][y,x]=0;reject(name,lambda t=t:verify(orig,new,inv,t,PAL))
reject('missing_resource',lambda:verify(orig,{n:a for n,a in new.items()if n!='COL00_0Z.ARC'},inv,targets,PAL))
reject('same_reproduction',lambda:validate(art,art));reject('outside_art_path',lambda:validate(ROOT,repro))
verify(orig,new,inv,targets,PAL);validate(art,repro)
(ART/'checks.json').write_text(json.dumps({'negative_cases_passed':passed,'count':len(passed),'valid_candidate_passed':True},indent=2)+'\n','utf8');print(json.dumps({'passed':len(passed)}))
