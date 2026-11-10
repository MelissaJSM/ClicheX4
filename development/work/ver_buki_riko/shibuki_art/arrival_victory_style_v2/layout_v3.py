import json,sys
from pathlib import Path
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT))
from scripts.solve_sprite_cover import cover
from scripts.solve_paired_cover import paired_cover
d=Path(__file__).parent;a=d/'production03';art=json.loads((a/'art.json').read_text());records=[]
existing=json.loads((a/'layout.json').read_text()) if (a/'layout.json').exists() else []
for q in art['groups']:
 n=q['frame']
 if q['kind'] in ('effect','original_grid'):continue
 old=next((r for r in existing if r['frame']==n and r['fits']),None)
 if old:records.append(old);continue
 arr=np.array(Image.open(a/f'frame_{n:03d}.png'));counts=[len(v) for v in q['part_slots'].values() if v];limit=min(min(counts),len(q['writable']))
 if q['kind']=='pair':
  other=np.array(Image.open(a/f'frame_{n+1:03d}.png'));limitb=len(q['part_slots'][str(n+1)]);result={'fits':False}
  for common in range(min(limit,limitb),1,-1):
   for rcount in range(1,limit-common+1):
    scount=min(limitb-common,len(q['writable'])-common-rcount)
    if scount<1:continue
    result=paired_cover(arr,other,[common,rcount,scount],6)
    if result['fits']:break
   if result['fits']:break
 else:result=cover(arr!=0,limit,8)
 result.update(frame=n);records.append(result);print(n,'fits',result['fits'],'rects',len(result.get('rects',[])),flush=True)
 (a/'layout.json').write_text(json.dumps(records+[r for r in existing if r['frame'] not in {v['frame'] for v in records}],indent=2))
