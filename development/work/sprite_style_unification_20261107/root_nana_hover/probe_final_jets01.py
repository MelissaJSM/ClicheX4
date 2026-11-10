"""Compare original unmoved hover jets with the final common body layers."""
from pathlib import Path
import sys,json,hashlib
import numpy as np
from PIL import Image
D=Path(__file__).resolve().parent;W=D.parent;ROOT=W.parents[1];sys.path[:0]=[str(ROOT),str(W/'nana_audit/native_restore')]
from preview_restore import Archive,helper
from scripts.export_x_consistency import entry,composition_frame
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
parent=W/'root_nana_shot87/packed_settle01/PL00_U.ARC';ult=W/'nana_audit/ultimate_vehicle_repaint/packed_vehicle_candidate_v1/PL02_U.ARC';aa=parent.read_bytes();bb=ult.read_bytes();a=Archive(aa)
assert entry(aa,0x10206)==entry(bb,0x10206)
for n in range(15):
 l=[{k:v for k,v in p.items()if k!='record_offset'}for p in composition_frame(entry(aa,3),12,n)['parts']];r=[{k:v for k,v in p.items()if k!='record_offset'}for p in composition_frame(entry(bb,3),12,n)['parts']];assert l==r
audit=W/'zero_audit/nana_ultimate_hover_relations01/conclusions.json';meta=json.loads(audit.read_text('utf8'));out=D/'final_jet_probe01';out.mkdir(exist_ok=False);pal=np.zeros((16,4),np.uint8)
for i in range(1,16):pal[i]=[65+i*10,85+i*8,115+i*6,255]
records=[]
for n in(221,223,225,227,229):
 ls={pb:np.array(Image.open(D/f'body_layers_probe01/layer{pb}_{n}.png'))for pb in(0,5,6,7,8)};rows=[]
 for form,mask in [('base_legs',8),('fourth',15)]:
  new=a.rgba(ls[0])
  for bit,pb in((8,8),(1,5),(4,7),(2,6)):
   if mask&bit:new.alpha_composite(a.rgba(ls[pb],32 if pb==7 else 16))
  old=a.composite(n,mask)[0]
  for label,body in [('old',old),('new',new)]:
   views=[];phases=[]
   for q in meta['effect_frames']:
    if n not in q['player_refs']:continue
    jet=np.load(ROOT/q['source_dump']);assert hashlib.sha256(jet.tobytes()).hexdigest()==q['indexed_sha256'];pic=Image.fromarray(pal[jet]);pic.alpha_composite(body);views.append((f'fixed jet {q["effect_frame"]}',pic));phases.append(q['effect_frame'])
   rows.append((f'{form} {n} {label}',views))
  records.append({'ref':n,'form':form,'phases':phases,'jet_transform':[0,0],'new_composite_sha256':hashlib.sha256(new.tobytes()).hexdigest()})
 helper.grid(rows,out/f'jets_{n}.png',5)
(out/'manifest.json').write_text(json.dumps({'parent_sha256':sha(parent),'source_audit_sha256':sha(audit),'all15_jet_parts_semantics_exact':True,'static_texture_exact':True,'figures':records,'neutral_palette':True,'actual_CLUT_blending_verified':False,'gameplay_verified':False},ensure_ascii=False,indent=2)+'\n','utf8');print('10 figures / all15 original jet phases; fixed effect origin; neutral diagnostic color')
