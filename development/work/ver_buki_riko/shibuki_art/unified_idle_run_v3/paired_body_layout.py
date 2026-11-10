"""Read-only packing feasibility; uses already installed voice_env SciPy."""
from pathlib import Path
import json,time
import numpy as np
from PIL import Image
from scipy.optimize import milp,Bounds,LinearConstraint
from scipy.sparse import csc_matrix
ROOT=Path(__file__).resolve().parents[4]
work=Path(__file__).parent
art=json.loads((work/'paired_body/art.json').read_text())
plan=json.loads((ROOT/'work/ver_buki_riko/shibuki_run_plan/20261026T044831801392Z/plan.json').read_text())
def cover(mask,count,timeout=6):
    yy,xx=np.nonzero(mask);coords=np.stack([xx,yy],axis=1);candidates=[];indices=[];indptr=[0];seen=set()
    for y in range(max(0,int(yy.min())-15),int(yy.max())+1):
        for x in range(max(0,int(xx.min())-15),int(xx.max())+1):
            ids=np.flatnonzero((xx>=x)&(xx<x+16)&(yy>=y)&(yy<y+16))
            if len(ids)<4:continue
            key=ids.tobytes()
            if key in seen:continue
            seen.add(key);candidates.append((x,y));indices.extend(ids);indptr.append(len(indices))
    A=csc_matrix((np.ones(len(indices)),np.array(indices),np.array(indptr)),shape=(len(xx),len(candidates)))
    from scipy.sparse import vstack
    A=vstack([A,np.ones((1,len(candidates)))],format='csc')
    result=milp(np.ones(len(candidates)),integrality=np.ones(len(candidates)),bounds=Bounds(0,1),
                constraints=LinearConstraint(A,np.r_[np.ones(len(xx)),0],np.r_[np.full(len(xx),np.inf),count]),
                options={'time_limit':timeout,'mip_rel_gap':0.0})
    rectangles=[] if result.x is None else [candidates[i] for i,v in enumerate(result.x) if v>.5]
    check=mask.copy()
    for x,y in rectangles:check[y:y+16,x:x+16]=False
    return {'rects':rectangles,'fits':not np.any(check),'status':int(result.status),'message':result.message,'count':count}

results=[]
for record in art['frames']:
    n=record['frame'];pair=next(p for p in plan['paired_frames'] if p['frames'][0]==n)
    a=np.array(Image.open(work/'paired_body'/record['image']));left,top=record['world_position'];ax,ay=left+48,top+40+20
    m=a!=0
    start=time.monotonic();r=cover(m,len(pair['common_base_tiles'])+len(pair['nonshoot_only_tiles']));r.update(frame=n,arm_rect=[ax,ay,16,16],seconds=round(time.monotonic()-start,2))
    print(json.dumps(r),flush=True);results.append(r)
    (work/'paired_body_layout.json').write_text(json.dumps(results,indent=2))
