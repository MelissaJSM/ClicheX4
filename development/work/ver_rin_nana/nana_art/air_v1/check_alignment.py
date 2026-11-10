"""대기 기준 눈·착지 발·사격 공유 몸 및 공중 자세 등록을 검사한다."""
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT))
import numpy as np
from PIL import Image
from scripts.prepare_nana_idle_shot import write
from scripts.project import digest
d=Path(__file__).parent;art=json.loads((d/'normalized01/art.json').read_text('utf8'));pairs=json.loads((d/'paired03/pairs.json').read_text('utf8'));rows=[];yy,xx=np.indices((80,96))
for r in art['frames']:
 n=r['frame'];a=np.array(Image.open(d/'normalized01'/r['image']));b=np.array(Image.open(d/'paired03'/f'shoot_{n:03d}.png'));gun=np.array(Image.open(d/'paired03'/f'gun_{n:03d}.png'));ex,ey=r['eye']
 assert ex==44
 assert np.array_equal(a[(yy<ey+4)&(xx>=ex-3)],b[(yy<ey+4)&(xx>=ex-3)])
 assert np.array_equal(a[yy>=ey+15],b[yy>=ey+15])
 mask=(xx<ex+1)&(yy>=np.where(xx<ex-3,ey+2,ey+5))&(yy<ey+15)
 assert not np.any((a!=b)&~mask&(gun==0))
 ys,xs=np.nonzero(a);bottom=int(ys.max())
 if n>=49:assert bottom==62
 rows.append({'frame':n,'eye_canvas':r['eye'],'body_opaque_bounds':[int(xs.min()),int(ys.min()),int(xs.max()+1),bottom+1],'landing_sole_world_y':bottom-40 if n>=49 else None,'head_and_lower_body_identical_in_shooting':True,'changes_limited_to_front_arm_window_and_authored_gun':True})
assert not art['per_frame_scale'];assert art['master_sha256']==digest(ROOT/'out/ver_rin_nana/nana_pilot_v9/nana_000_indexed.png')
write(d/'alignment_checks.json',{'one_shared_scale':art['scale'],'idle_eye_canvas_x':44,'landing_sole_world_y':22,'rows':rows,'runtime_verified':False})
print(json.dumps({'frames':len(rows),'eye_x':44,'landing_sole_y':22,'shared_body_checks':'passed'}))
