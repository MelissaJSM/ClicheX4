"""읽기 전용 16x16 사각형 배치 탐색. SciPy는 작업용 환경에서만 사용한다."""
import numpy as np
from scipy.optimize import milp,Bounds,LinearConstraint
from scipy.sparse import csc_matrix,vstack

def cover(mask,count,timeout=4):
    yy,xx=np.nonzero(mask);candidates=[];indices=[];indptr=[0];seen=set()
    if not len(xx):return {'fits':True,'rects':[],'status':0}
    for y in range(max(0,int(yy.min())-15),min(mask.shape[0]-16,int(yy.max()))+1):
        for x in range(max(0,int(xx.min())-15),min(mask.shape[1]-16,int(xx.max()))+1):
            ids=np.flatnonzero((xx>=x)&(xx<x+16)&(yy>=y)&(yy<y+16))
            if len(ids)<1:continue
            key=ids.tobytes()
            if key in seen:continue
            seen.add(key);candidates.append([x,y]);indices.extend(ids);indptr.append(len(indices))
    A=csc_matrix((np.ones(len(indices)),np.array(indices),np.array(indptr)),shape=(len(xx),len(candidates)))
    A=vstack([A,np.ones((1,len(candidates)))],format='csc')
    result=milp(np.ones(len(candidates)),integrality=np.ones(len(candidates)),bounds=Bounds(0,1),
        constraints=LinearConstraint(A,np.r_[np.ones(len(xx)),0],np.r_[np.full(len(xx),np.inf),count]),options={'time_limit':timeout,'mip_rel_gap':0.0})
    rectangles=[] if result.x is None else [candidates[i] for i,v in enumerate(result.x) if v>.5]
    check=mask.copy()
    for x,y in rectangles:check[y:y+16,x:x+16]=False
    return {'rects':rectangles,'fits':not np.any(check),'status':int(result.status),'count':count}
