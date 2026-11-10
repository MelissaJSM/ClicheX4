from pathlib import Path
import sys,json,time
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT))
from scripts.solve_sprite_cover import cover
work=Path(__file__).parent;art=json.loads((work/'paired_body/art.json').read_text());plan=json.loads((ROOT/'work/ver_buki_riko/shibuki_run_plan/20261026T044831801392Z/plan.json').read_text());results=[]
for r in art['frames']:
 n=r['frame'];a=np.array(Image.open(work/'paired_body'/r['image']));pair=next(p for p in plan['paired_frames'] if p['frames'][0]==n)
 count=len(pair['common_base_tiles'])+len(pair['nonshoot_only_tiles'])-1
 yy,xx=np.nonzero(a);ey,ex=np.nonzero(a==7);left=int(xx.min());eye=round(float(np.median(ey)));best=None
 for dx,dy in [(0,0),(0,1),(1,0),(0,-1),(1,1),(-1,0),(0,-2),(2,0),(1,-1),(0,2)]:
  x,y=left+dx,eye+dy;m=a!=0;m[y:y+16,x:x+16]=False;test=cover(m,count)
  if test['fits']:
   best={**test,'frame':n,'arm_rect':[x,y]};break
 if best is None:best={'frame':n,'fits':False}
 results.append(best);print(json.dumps(best),flush=True);(work/'joint_layout.json').write_text(json.dumps(results,indent=2)+'\n')
