"""Register only newly authored calf/boot texels; keep refined upper bodies."""
from pathlib import Path
import sys,json,struct,hashlib
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from scripts.overhaul_sprites_audit import render,rgba
from scripts.prepare_riko_ui import entry
from scripts.export_x_consistency import page
D=Path(__file__).parent/'rin_extension';O=D/'rear_registered_legfix_v1';assert not O.exists();O.mkdir()
arc=(D/'prepared_third_saber_v1/PL01_U.ARC').read_bytes();pal=struct.unpack_from('<16H',entry(arc,9));black=struct.unpack_from('<16H',entry(arc,9),13*32);items={v:[]for v in('normal','black')};rows=[]
for n in(178,182,186,190):
 original=render(arc,0,0,n)[0];base=np.array(Image.open(D/f'rear_continuation01/native/b0_{n:03}_indices.png'));a=base.copy();mask=np.zeros_like(a,bool);registration=[]
 if n in(186,190):
  base=np.array(Image.open(D/f'rear_leg_fix_{n}/refined_base_indices.png'));a=base.copy();src=np.array(Image.open(D/f'rear_leg_fix_{n}/generated_native_indices.png'))
  if n==186:
   mask[166:169,155:162]=True;mask[169:181,154:169]=True
  else:
   mask[163,158:165]=True;mask[164,159:166]=True;mask[165:180,158:169]=True
   # Foot-only anchor registration: preserve the head and calf in place.
   before=src.copy();src[170:180,158:169]=0;src[170:177,158:169]=before[171:178,158:169]
   registration.append({'part':'newly authored lower boot','source_roi':[158,171,169,178],'translation':[0,-1],'reason':'발끝 y176 복원. 머리/상체/종아리 전체 이동 없음.'})
  a[mask]=src[mask];assert np.array_equal(a[~mask],base[~mask])
 Image.fromarray(a).save(O/f'b0_{n:03}_indices.png');Image.fromarray(mask.astype(np.uint8)*255).save(O/f'b0_{n:03}_edit_mask.png')
 for form,words in[('normal',pal),('black',black)]:items[form]+=[(f'{n} old',rgba(original,words)),(f'{n} initial detailed',rgba(base,words)),(f'{n} leg corrected',rgba(a,words))]
 rows.append({'ref':n,'mask_pixels':int(mask.sum()),'changed_from_refined_base':int(np.count_nonzero(a!=base)),'outside_leg_mask_exact':True,'registration':registration,'head190_generic_dy_undone':n==190,'source_old_body_pixels_copied':0,'after_sha256':hashlib.sha256((O/f'b0_{n:03}_indices.png').read_bytes()).hexdigest()})
for form,words in[('normal',pal),('black',black)]:page(items[form],rgba(render(arc,0,0,147)[0],words),O/f'{form}_comparison.png',cols=3,scale=5)
(O/'registration.json').write_text(json.dumps({'rows':rows,'scope':'새 상세원화 몸통은 보존하고 생성한 종아리/부츠 부분만 등록. 손목 위치는 후속 정합 전.','root_review_pending':True,'user_accepted':False},ensure_ascii=False,indent=2)+'\n','utf8');print(O)
