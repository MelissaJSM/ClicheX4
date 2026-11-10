"""두 자세의 같은 픽셀을 공유하는 사각형 배치를 동시에 찾는다. 게임 쓰기 없음."""
import numpy as np
from scipy.optimize import milp,Bounds,LinearConstraint
from scipy.sparse import csc_matrix


def paired_cover(run,shot,counts,timeout=30):
    same=(run==shot)&(run!=0);ry,rx=np.nonzero(run);sy,sx=np.nonzero(shot)
    candidates=[];indices=[];ptr=[0];costs=[];row_count=len(rx)+len(sx)
    for group,mask in enumerate((same,run!=0,shot!=0)):
        yy,xx=np.nonzero(mask);seen=set()
        for y in range(max(0,int(yy.min())-15),min(mask.shape[0]-16,int(yy.max()))+1):
            for x in range(max(0,int(xx.min())-15),min(mask.shape[1]-16,int(xx.max()))+1):
                r=np.flatnonzero((rx>=x)&(rx<x+16)&(ry>=y)&(ry<y+16)) if group!=2 else np.array([],int)
                s=np.flatnonzero((sx>=x)&(sx<x+16)&(sy>=y)&(sy<y+16)) if group!=1 else np.array([],int)
                if group==0:r=r[same[ry[r],rx[r]]];s=s[same[sy[s],sx[s]]]
                ids=np.r_[r,s+len(rx)]
                if len(ids)==0:continue
                key=ids.tobytes()
                if key in seen:continue
                seen.add(key);candidates.append((group,x,y));costs.append(float(len(ids)));indices.extend(ids);indices.append(row_count+group);ptr.append(len(indices))
    matrix=csc_matrix((np.ones(len(indices)),np.array(indices),np.array(ptr)),shape=(row_count+3,len(candidates)))
    lower=np.r_[np.ones(row_count),counts];upper=np.r_[np.full(row_count,np.inf),counts]
    result=milp(np.array(costs),integrality=np.ones(len(candidates)),bounds=Bounds(0,1),constraints=LinearConstraint(matrix,lower,upper),options={'time_limit':timeout,'mip_rel_gap':0.0})
    groups=[[],[],[]]
    if result.x is not None:
        for (group,x,y),v in zip(candidates,result.x):
            if v>.5:groups[group].append([x,y])
    return {'fits':result.x is not None,'status':int(result.status),'rects':groups[0],'run_rects':groups[1],'shot_rects':groups[2]}
