import sys,json
from pathlib import Path
import numpy as np
H=Path(__file__).resolve().parent;sys.path.insert(0,str(H))
import sync_standing_selection as s
from pack_selection_mirrors import flip
g=s.entry(s.UI.read_bytes(),0x10102)[90112:];p=s.entry(s.UI.read_bytes(),10)
owned={q['page']*256+q['tile']for n in s.DY for q in s.aliased_composition(p,2,n)['parts']}
count=s.aliased_composition(p,2,0)['bank_frame_count']
other={q['page']*256+q['tile']for n in range(count)if n not in s.DY for q in s.aliased_composition(p,2,n)['parts']}
a=s.Archive(s.NEW.read_bytes());variants={}
canon=lambda z:min(flip(z,b)for b in(0,64,128,192))
for gx in range(16):
 for gy in range(16):
  patterns=set();parts=0
  for n in s.DY:
   z=a.layer(n+84)[0]
   for y in range(128+gy,208,16):
    for x in range(112+gx,208,16):
     tile=z[y:y+16,x:x+16]
     if np.any(tile):patterns.add(canon(tile.tobytes()));parts+=1
  variants[f'{gx},{gy}']={'patterns':len(patterns),'parts':parts}
best=sorted(variants.items(),key=lambda kv:(kv[1]['patterns'],kv[1]['parts']))[:12]
print(json.dumps({'owned':len(owned),'free':len(owned-other),'shared':sorted(owned&other),'best_grid':best}))
