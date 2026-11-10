"""Freeze the reviewed 50 native layers, including the local folded-shoe fix."""
from pathlib import Path
import json,hashlib,shutil
import numpy as np
from PIL import Image
D=Path(__file__).resolve().parent;W=D.parent;ROOT=W.parents[1]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
out=D/'final_targets01';out.mkdir(exist_ok=False)
rows=[]
for n in range(221,231):
 folder=D/('body_layers_probe01' if n%2 else 'shoot_layers_probe02')
 m=json.loads((folder/'manifest.json').read_text('utf8'));prior=next(q for q in m['frames'] if q['ref']==n)
 row={'ref':n,'layer_hashes':{},'sources':{}}
 for pb in (0,5,6,7,8):
  original=folder/f'layer{pb}_{n}.png';z=np.array(Image.open(original))
  assert hashlib.sha256(z.tobytes()).hexdigest()==prior['layer_hashes'][str(pb)]
  f=D/f'rearfoot_registered01/layer8_{n}.png' if pb==8 and n in(229,230) else original
  dst=out/f'layer{pb}_{n}.png';shutil.copyfile(f,dst)
  a=np.array(Image.open(dst));assert a.shape==(384,384) and a.max()<16
  if f!=original:
   mask=np.zeros_like(a,dtype=bool);mask[172:179,152:167]=True
   assert np.array_equal(a[~mask],z[~mask]);assert np.count_nonzero(a!=z)==20
  row['layer_hashes'][str(pb)]=hashlib.sha256(a.tobytes()).hexdigest()
  row['sources'][str(pb)]={'path':f.relative_to(ROOT).as_posix(),'sha256':sha(f),'output_sha256':sha(dst)}
 rows.append(row)
for n in range(221,231,2):
 assert np.array_equal(np.array(Image.open(out/f'layer8_{n}.png')),np.array(Image.open(out/f'layer8_{n+1}.png')))
(out/'manifest.json').write_text(json.dumps({'scope':'나나 기본/포스 호버10참조50층; 229/230 굽힌신발20px 국소수정 포함','parent':json.loads((D/'input_audit.json').read_text('utf8'))['input'],'frames':rows,'valid_hover_masks':list(range(8,16)),'packed':False,'runtime_verified':False},ensure_ascii=False,indent=2)+'\n','utf8')
print('50 final native targets assembled; five idle/fire leg pairs identical')
