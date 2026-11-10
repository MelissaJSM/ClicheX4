from pathlib import Path
import json,sys,itertools
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT))
from scripts.solve_sprite_cover import cover
from src.psx_player import composition_frame
d=Path(__file__).parent;p=d/'paired02';pairs=json.loads((p/'pairs.json').read_text());plan=json.loads((ROOT/'work/ver_buki_riko/shibuki_run_plan/20261026T044831801392Z/plan.json').read_text());parts=(ROOT/'work/ver_buki_riko/shibuki_x_extract/20261026T024200768121Z/composition_entry.bin').read_bytes();results=json.loads((d/'layout03.json').read_text())
for r in pairs['frames']:
 n=r['run']
 if n not in [3,27,29]:continue
 a=np.array(Image.open(p/f'run_{n:03d}.png'));b=np.array(Image.open(p/f'shoot_{n:03d}.png'));pair=next(q for q in plan['paired_frames'] if q['frames'][0]==n)
 writable=set(pair['common_base_tiles']+pair['nonshoot_only_tiles']+pair['shoot_only_tiles']);nr=len(composition_frame(parts,0,n)['parts']);ns=len(composition_frame(parts,0,n+1)['parts'])
 count=min(nr-1,ns-2,len(writable)-3);mask=np.array(Image.open(p/f'common_{n:03d}.png'))!=0;layout=cover(mask,count,2)
 result={**layout,'frame':n,'mode':'arm_and_gun','arm_rect':r['run_arm_rect']}
 if not layout['fits']:
  diff=a!=b;yy,xx=np.nonzero(diff);xmin,xmax=int(xx.min()),int(xx.max());ymin,ymax=int(yy.min()),int(yy.max());count=min(nr-2,ns-2,len(writable)-4)
  full=cover(b!=0,ns,2);candidates=[]
  if full['fits']:candidates.extend(itertools.combinations(full['rects'],2))
  for gy in (ymin-3,ymin-4,ymin-2,ymin-1,ymin,ymax-15):
   for gx in (xmin-1,xmin,xmin-2):
    for ax in (xmax-15,xmax-14,xmax-16,xmax-13):
     for ay in (ymax-15,ymax-14,ymin,ymin-1):candidates.append(([gx,gy],[ax,ay]))
  seen=set()
  for rects in candidates:
   rects=sorted(rects);key=tuple(map(tuple,rects))
   if key in seen:continue
   seen.add(key);left=diff.copy();common=a!=0
   for x,y in rects:left[y:y+16,x:x+16]=False;common[y:y+16,x:x+16]=False
   if np.any(left):continue
   gx,gy=rects[0]
   if np.any(a[gy:gy+16,gx]):continue
   layout=cover(common,count,.65)
   if layout['fits']:
    result={**layout,'frame':n,'mode':'joint','unique_rects':rects};break
 if result['fits']:r['common_rects']=result['rects']
 results=[q for q in results if q['frame']!=n]+[result];results.sort(key=lambda q:q['frame']);print(json.dumps(result),flush=True)
 (d/'layout03.json').write_text(json.dumps(results,indent=2));(p/'pairs.json').write_text(json.dumps(pairs,indent=2))
if not all(r['fits'] for r in results):raise RuntimeError('Some paired bodies need revision')
