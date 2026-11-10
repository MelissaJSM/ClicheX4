"""앵커/영역별 bbox 관측. 자동 미술 합격 판정 아님."""
from pathlib import Path
import json,sys
import numpy as np
from PIL import Image
from scipy.ndimage import label
ROOT=Path(__file__).resolve().parents[4];D=Path(__file__).parent;N=D.parent
sys.path[:0]=[str(ROOT),str(N/'native_restore')]
from preview_restore import Archive,write,sha,digest,helper
def bb(m):
    y,x=np.nonzero(m)
    return None if not len(x) else [int(x.min()-160),int(y.min()-160),int(x.max()+1-160),int(y.max()+1-160)]
def full(a,n):
    v=a.layer(n)[0].copy()
    for pb in (8,5,7,6):
        q=a.layer(n,pb)[0];v[q>0]=q[q>0]
    return v
def info(v,eye):
    ex,ey=eye;Y,X=np.indices(v.shape);alive=v>0
    headgate=(Y<ey+160+5)&(X>=ex+160-12)&(X<ex+160+16)
    eargate=(Y<ey+160-8)&(X>=ex+160-10)&(X<ex+160+14)
    facegate=(Y>=ey+160-2)&(Y<ey+160+7)&(X>=ex+160-4)&(X<ex+160+9)
    return {'eye_world':eye,'whole_bbox':bb(alive),'front_head_window_bbox':bb(alive&headgate),
      'light_ear_texels_bbox':bb(np.isin(v,(13,15))&eargate),'face_skin_window_bbox':bb(np.isin(v,(10,11,12))&facegate),
      'head_region_note':'Windowed measurement; hair behind16px is outside, raised hand may enter. Not anatomical segmentation.',
      'sole_world_y':int(np.nonzero(alive)[0].max()-160),'opaque_pixels':int(alive.sum())}
def main():
    a=Archive((N/'native_restore/nova_sync_v1/PL02_U.ARC').read_bytes());out=D/'first_geometry_v1';out.mkdir(exist_ok=True)
    plan=json.loads((D/'inputs_first_v1/before_poses.json').read_text('utf8'));records=[]
    idle=full(a,0);Y,X=np.indices(idle.shape);gy,gx=np.nonzero((idle==14)&(Y<160));ie=[int(np.median(gx)-160),int(np.median(gy)-160)]
    for p in plan:
        n=p['ref'];eye=list(map(int,p['eye_world']));new=np.array(Image.open(D/f'before_first_registered_v2/before_{n:03}.png'))
        records.append({'ref':n,'current':info(full(a,n),eye),'new_candidate':info(new,eye)})
    write(out/'metrics.json',{'idle':info(idle,ie),'frames':records,'quantitative_observation_only':True,'art_passed':False,
      'followups':['33/39/47 skin-highlight edge too black; same-source local image correction required.','Raised39 hand is wider and 2pxhigher; hand and shoe x contact registration pending.','New rear hair may widen; compare silhouette and stage occupancy before packing.']})
    print(json.dumps({'idle':info(idle,ie),'frames':records}))
if __name__=='__main__':main()
