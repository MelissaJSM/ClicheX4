"""팔·몸체 사이 실제 같은 색인만 공유하는 여러 무손실 저장 후보."""
import numpy as np
from src.psx_compress import encode_stream
from scripts.prepare_shibuki_armor_remaining import pack_many_patterns
from native_pose_pack import need

def components(images,threshold):
    unique=[];lookup=[]
    for ar in images:
        k=next((i for i,v in enumerate(unique)if np.array_equal(ar,v)),None)
        if k is None:k=len(unique);unique.append(ar.copy())
        lookup.append(k)
    residual=[v.copy()for v in unique];pieces=[];owners=[]
    for _ in range(48):
        best=None
        for i,a in enumerate(residual):
            for j in range(i+1,len(residual)):
                m=(a==residual[j])&(a>0);area=int(m.sum())
                if area<threshold:continue
                y,x=np.nonzero(m)
                if area/((x.max()-x.min()+1)*(y.max()-y.min()+1))<.25:continue
                if best is None or area>best[0]:best=(area,i,m)
        if best is None:break
        _,i,m=best;p=np.where(m,residual[i],0).astype(np.uint8);use=[k for k,a in enumerate(residual)if np.array_equal(a[m],p[m])]
        pieces.append(p);owners.append(use)
        for k in use:residual[k][m]=0
    for k,ar in enumerate(residual):
        if ar.any():pieces.append(ar);owners.append([k])
    return pieces,[[i for i,v in enumerate(owners)if k in v]for k in lookup]

def candidates(raw,images,pool):
    out=[];errors=[]
    for threshold in(None,128,80,48):
        try:
            if threshold is None:nr,rr=pack_many_patterns(raw,32,images,pool,[24]*len(images))
            else:
                pp,which=components(images,threshold);nr,pr=pack_many_patterns(raw,32,pp,pool,[24]*len(pp));rr=[[r for k in keys for r in pr[k]]for keys in which]
            need(all(len(r)<=24 for r in rr),'Parts24 exceeded')
            out.append((len(encode_stream(nr)),nr,rr,'whole' if threshold is None else f'exact_components_{threshold}'))
        except ValueError as ex:errors.append({'threshold':threshold,'reason':str(ex)})
    need(out,'No lossless layout: '+str(errors));return sorted(out,key=lambda v:(v[0],sum(map(len,v[2])),v[3]))
