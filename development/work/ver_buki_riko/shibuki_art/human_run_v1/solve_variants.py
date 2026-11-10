from pathlib import Path
import sys,json,itertools
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT))
from scripts.solve_sprite_cover import cover
from src.psx_player import composition_frame
d=Path(__file__).parent;p=d/'paired';pairs=json.loads((p/'pairs.json').read_text());layouts=json.loads((d/'joint_layout.json').read_text());plan=json.loads((ROOT/'work/ver_buki_riko/shibuki_run_plan/20261026T044831801392Z/plan.json').read_text());parts=(ROOT/'work/ver_buki_riko/shibuki_x_extract/20261026T024200768121Z/composition_entry.bin').read_bytes()
for n in [3,19,25,27,29]:
 a=np.array(Image.open(p/f'run_{n:03d}.png'));b=np.array(Image.open(p/f'shoot_{n:03d}.png'));pair=next(q for q in plan['paired_frames'] if q['frames'][0]==n)
 writable=set(pair['common_base_tiles']+pair['nonshoot_only_tiles']+pair['shoot_only_tiles']);nr=len(composition_frame(parts,0,n)['parts']);ns=len(composition_frame(parts,0,n+1)['parts']);c=min(nr-2,ns-2,len(writable)-4)
 pools=[cover(b!=0,ns,3),cover(a!=0,nr,3)];found=None
 for pool in pools:
  if not pool['fits']:continue
  for rects in itertools.combinations(pool['rects'],c):
   mask=np.zeros(a.shape,bool)
   for x,y in rects:mask[y:y+16,x:x+16]=True
   shared=mask&(a==b)&(a!=0);ra=(a!=0)&~shared;rb=(b!=0)&~shared
   la=cover(ra,2,.8)
   if not la['fits']:continue
   lb=cover(rb,2,.8)
   if not lb['fits']:continue
   found={'frame':n,'fits':True,'mode':'variant','rects':list(rects),'run_rects':la['rects'],'shot_rects':lb['rects']};break
  if found:break
 if found:
  for i,l in enumerate(layouts):
   if l['frame']==n:layouts[i]=found
  for r in pairs['frames']:
   if r['run']==n:r['common_rects']=found['rects']
  (d/'joint_layout.json').write_text(json.dumps(layouts,indent=2));(p/'pairs.json').write_text(json.dumps(pairs,indent=2))
 print(json.dumps(found or {'frame':n,'fits':False}),flush=True)
