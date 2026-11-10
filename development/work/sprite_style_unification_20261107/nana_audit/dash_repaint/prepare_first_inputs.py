"""다음 대시 4키 생성 입력만 준비한다. 게임 자원과 그림을 새로 수정하지 않는다."""
from pathlib import Path
import sys,json
import numpy as np
from scipy.ndimage import label
D=Path(__file__).resolve().parent;N=D.parent;ROOT=N.parents[2];sys.path[:0]=[str(ROOT),str(N),str(N/'native_restore')]
from preview_restore import Archive,sha,digest,need,write
from prepare_air_inputs import page
SOURCE=N/'air_repaint/packed_air_candidate_v1/PL00_U.ARC';EXPECTED='721457a50ea48e76c1ac592eec21db274b43c5863cc5b3df310ac981d5890dca'
def main():
    need(digest(SOURCE)==EXPECTED,'Source');a=Archive(SOURCE.read_bytes());page(a,[(f'POSE {n}',n,0)for n in(67,71,79,93)],D/'basic_first4.png');page(a,[('PRIMARY STYLE IDLE 0',0,0),('NEW RUN 7',7,0),('NEW AIR 39',39,0),('NEW WALL 63',63,0)],D/'style_master.png');page(a,[(f'FOURTH POSE {n}',n,15)for n in(67,71,79,93)],D/'fourth_first4.png')
    component=[]
    for n in(71,73,75):
        ar=a.layer(n)[0];labs,total=label(ar>0,np.ones((3,3)));counts=np.bincount(labs.flat);counts[0]=0;body=np.where(labs==counts.argmax(),ar,0).astype(np.uint8);effect=np.where((labs>0)&(labs!=counts.argmax()),ar,0).astype(np.uint8);component.append({'ref':n,'components':int(total),'largest_pixels':int((body>0).sum()),'outside_pixels':int((effect>0).sum()),'largest_sha256':sha(body.tobytes()),'outside_sha256':sha(effect.tobytes())})
    write(D/'first_inputs.json',{'parent_arc_sha256':EXPECTED,'first_keys':[67,71,79,93],'full_scope':[*range(67,85),93,94],'style_master':'idle0 is primary; new run7/air39/wall63 show adopted detail continuity','component_diagnostic_only':component,'annotation':'73 분리 픽셀은 효과 후보로 보호해야 하지만 connected component만으로 효과 의미를 확정하지 않는다.93/94는 사격짝이 아니다.','images':{f:digest(D/f)for f in('basic_first4.png','style_master.png','fourth_first4.png')},'new_art_generated':False})
    print(json.dumps(component))
if __name__=='__main__':main()
