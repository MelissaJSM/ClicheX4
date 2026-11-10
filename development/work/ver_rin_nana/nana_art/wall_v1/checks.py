import json,sys,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT))
import numpy as np
from PIL import Image
from scripts.prepare_nana_idle_shot import write
from scripts.build_nana_run import validate,configure_scope
from scripts.project import digest
configure_scope('wall')
source=ROOT/'work/ver_rin_nana/nana_wall/20261029T224256603234Z';out=ROOT/'work/ver_rin_nana/nana_wall/rejection_checks_v1';out.mkdir(exist_ok=False);rows=[]
for case in ('wrong_parent','wrong_frame_scope','changed_style','tampered_arc','previous_dash_changed'):
 a=out/case/'a';b=out/case/'b';a.mkdir(parents=True);b.mkdir();r=json.loads((source/'recipe.json').read_text('utf8'))
 if case=='wrong_parent':r['parent_bin_sha256']='0'*64
 elif case=='wrong_frame_scope':r['changed_bitmap_references'][0]=[0,85]
 elif case=='changed_style':r['master_sha256']='0'*64
 elif case=='previous_dash_changed':r['dash_frames_preserved']=False
 else:
  raw=bytearray((source/'modified.arc').read_bytes());raw[-1]^=1;(a/'modified.arc').write_bytes(raw);shutil.copyfile(source/'modified.arc',b/'modified.arc')
 for p in (a,b):write(p/'recipe.json',r)
 try:validate(a,b)
 except ValueError as e:rows.append({'case':case,'rejected_before_disc_write':True,'error':str(e)})
 else:raise AssertionError('Accepted '+case)
write(out/'results.json',rows)
d=Path(__file__).parent;art=json.loads((d/'normalized02/art.json').read_text('utf8'));yy,xx=np.indices((80,96));checks=[]
for r in art['frames']:
 n=r['frame'];a=np.array(Image.open(d/'normalized02'/r['image']));b=np.array(Image.open(d/'paired03'/f'shoot_{n:03d}.png'));ex,ey=r['eye']
 assert np.array_equal(a[(xx>=ex-3)&(yy<ey+4)],b[(xx>=ex-3)&(yy<ey+4)])
 assert np.array_equal(a[yy>=ey+15],b[yy>=ey+15])
 assert np.array_equal(a[xx>=ex+2],b[xx>=ex+2])
 if n in (57,59):assert ex==44
 checks.append({'frame':n,'eye':r['eye'],'wall_contact':r['wall_contact'],'head_lower_body_rear_hand_preserved_when_firing':True,'size':r['native_size']})
assert not art['per_frame_scale']
assert art['master_sha256']==digest(ROOT/'out/ver_rin_nana/nana_pilot_v9/nana_000_indexed.png')
write(d/'alignment_checks.json',{'single_scale':art['scale'],'width_factor':art['common_width_factor'],'rows':checks,'runtime_verified':False});print(json.dumps({'negative_checks':rows,'alignment_frames':len(checks)}))
