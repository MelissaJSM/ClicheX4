"""Verify the local folded-shoe correction against the unmoved propulsion phases."""
from pathlib import Path
import sys,json,hashlib
import numpy as np
from PIL import Image
D=Path(__file__).resolve().parent;W=D.parent;ROOT=W.parents[1]
sys.path[:0]=[str(ROOT),str(W/'nana_audit/native_restore')]
from preview_restore import Archive,helper
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
a=Archive((W/'root_nana_shot87/packed_settle01/PL00_U.ARC').read_bytes())
meta=json.loads((W/'zero_audit/nana_ultimate_hover_relations01/conclusions.json').read_text('utf8'))
out=D/'rearfoot_jet_probe02';out.mkdir(exist_ok=False)
pal=np.zeros((16,4),np.uint8)
for i in range(1,16):pal[i]=[65+i*10,85+i*8,115+i*6,255]
records=[]
for n in (229,230):
 folder=D/('body_layers_probe01' if n==229 else 'shoot_layers_probe02')
 ls={pb:np.array(Image.open(folder/f'layer{pb}_{n}.png')) for pb in(0,5,6,7,8)}
 corrected=np.array(Image.open(D/f'rearfoot_registered01/layer8_{n}.png'))
 rows=[]
 for form,mask in [('base_legs',8),('fourth',15)]:
  for label,legs in [('prior new',ls[8]),('local shoe fix',corrected)]:
   body=a.rgba(ls[0])
   for bit,pb in((8,8),(1,5),(4,7),(2,6)):
    if mask&bit:body.alpha_composite(a.rgba(legs if pb==8 else ls[pb],32 if pb==7 else 16))
   views=[]
   for q in meta['effect_frames']:
    if 229 not in q['player_refs']:continue
    jet=np.load(ROOT/q['source_dump']);assert hashlib.sha256(jet.tobytes()).hexdigest()==q['indexed_sha256']
    pic=Image.fromarray(pal[jet]);pic.alpha_composite(body);views.append((f'fixed jet {q["effect_frame"]}',pic))
   rows.append((f'{form} {n} {label}',views))
  records.append({'ref':n,'form':form,'fixed_effect_origin':True,'body_unchanged_except_local_leg_roi':True})
 helper.grid(rows,out/f'jets_{n}.png',5)
 partials=[]
 for mask in range(8,16):
  body=a.rgba(ls[0])
  for bit,pb in((8,8),(1,5),(4,7),(2,6)):
   if mask&bit:body.alpha_composite(a.rgba(corrected if pb==8 else ls[pb],32 if pb==7 else 16))
  partials.append((str(mask),body))
 helper.grid([(f'{n} valid hover partials',partials[:4]),('continued',partials[4:])],out/f'partials_{n}.png',5)
(out/'manifest.json').write_text(json.dumps({'correction_manifest_sha256':sha(D/'rearfoot_registered01/manifest.json'),'figures':records,'neutral_palette':True,'actual_effect_CLUT_verified':False,'runtime_verified':False},indent=2)+'\n','utf8')
print('229/230 x two forms x three original fixed jet phases; eight valid part combinations each')
