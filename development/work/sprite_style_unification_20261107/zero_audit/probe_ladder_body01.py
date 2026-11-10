"""새 원화 머리와 몸체를 두 레이어로 나누어 목 길이만 등록하는 비교."""
from pathlib import Path
import sys,json,struct,hashlib
import numpy as np
from PIL import Image
from scipy.ndimage import binary_fill_holes
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from scripts.overhaul_sprites_audit import render,rgba
from scripts.prepare_riko_ui import entry
from scripts.export_x_consistency import page
D=Path(__file__).parent/'rin_extension';A=D/'ladder_dash01';S=A/'anchor_probe';O=A/'body_probe';assert not O.exists();O.mkdir()
info=json.loads((A/'inputs.json').read_text('utf8'));arc=(ROOT/info['actual_input_arc']).read_bytes();pal=info['palette_words'];black=struct.unpack_from('<16H',entry(arc,9),13*32)
rows=[];items={k:[]for k in('normal','black')}
for n in(199,202,155,156):
 key=f'b0_{n:03}';src=np.array(Image.open(S/(key+'_indices.png')));z=src.copy();record={'key':key}
 if n in(199,202):
  box=(143,125,176,144 if n==199 else 143);x0,y0,x1,y1=box;head=np.zeros_like(src);head[y0:y1,x0:x1]=src[y0:y1,x0:x1];mask=binary_fill_holes(head>0);body=src.copy();body[mask]=0;z=np.roll(body,-2,axis=0);z[mask]=head[mask]
  record.update(head_box=box,head_mask_pixels=int(mask.sum()),head_original_rgba_exact=bool(np.array_equal(src[mask],z[mask])),body_translation=[0,-2],head_translation=[0,0],no_new_pixel_colors=True)
  Image.fromarray(mask.astype('uint8')*255).save(O/(key+'_head_mask.png'))
 Image.fromarray(z).save(O/(key+'_indices.png'));old=render(arc,0,0,n)[0];record.update(old_floor=int(np.nonzero(old)[0].max()),new_floor=int(np.nonzero(z)[0].max()),new_bounds=rgba(z,pal).getbbox());rows.append(record)
 for form,words in [('normal',pal),('black',black)]:items[form].extend([(key+' old',rgba(old,words)),(key+' source positioned',rgba(src,words)),(key+' body -2 / head exact' if n in(199,202) else key+' candidate',rgba(z,words))])
for form,words in [('normal',pal),('black',black)]:page(items[form],rgba(render(arc,0,0,147)[0],words),O/(form+'_comparison.png'),cols=3,scale=6)
(O/'registration.json').write_text(json.dumps({'records':rows,'candidate_only':True,'root_review_pending':True,'game_unchanged':True},ensure_ascii=False,indent=2)+'\n','utf8')
print(json.dumps(rows))
