"""Place new gloved hands back at prior contact locations, without old art."""
from pathlib import Path
import sys,json,hashlib,struct
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from scripts.overhaul_sprites_audit import render,rgba
from scripts.prepare_riko_ui import entry
from scripts.export_x_consistency import page
D=Path(__file__).parent/'rin_extension';P=D/'rear_registered_legfix_v1';O=D/'rear_registered_grips_v1';assert not O.exists();O.mkdir()
arc=(D/'prepared_third_saber_v1/PL01_U.ARC').read_bytes();pal=struct.unpack_from('<16H',entry(arc,9));black=struct.unpack_from('<16H',entry(arc,9),13*32);items={f:[]for f in('normal','black')};records=[]
for n in(178,182,186,190):
 a=np.array(Image.open(P/f'b0_{n:03}_indices.png'));new=a.copy();moves=[]
 if n==178:
  moves+=[(y,x,0,1)for y in range(122,129)for x in range(148,155)]
  moves+=[(y,x,0,1)for y in range(129,131)for x in range(149,154)]
 if n==182:
  moves+=[(y,x,2,0)for y in range(125,133)for x in range(168,178)]
  moves+=[(y,x,2,0)for y in range(133,136)for x in range(166,174)]
  moves+=[(y,x,1,0)for y in range(136,141)for x in range(166,172)]
 if n==186:
  moves+=[(y,x,1,1)for y in range(123,131)for x in range(165,176)]
  moves+=[(y,x,1,1)for y in range(131,135)for x in range(166,173)]
  moves+=[(135,x,1,1)for x in range(167,173)]
 mask=np.zeros_like(a,bool);dest=set();moved=[]
 for y,x,dx,dy in moves:new[y,x]=0;mask[y,x]=True
 # Only opaque authored texels move; transparent cells never erase preserved head.
 for y,x,dx,dy in moves:
  if not a[y,x]:continue
  assert(y+dy,x+dx)not in dest;dest.add((y+dy,x+dx));new[y+dy,x+dx]=a[y,x];mask[y+dy,x+dx]=True;moved.append({'from':[x,y],'to':[x+dx,y+dy],'index':int(a[y,x])})
 assert np.array_equal(new[~mask],a[~mask])
 Image.fromarray(new).save(O/f'b0_{n:03}_indices.png');Image.fromarray(mask.astype(np.uint8)*255).save(O/f'b0_{n:03}_grip_mask.png')
 for form,words in[('normal',pal),('black',black)]:items[form]+=[(f'{n} original',rgba(render(arc,0,0,n)[0],words)),(f'{n} refined before grip',rgba(a,words)),(f'{n} anchored grip',rgba(new,words))]
 records.append({'ref':n,'old_authored_body_copied':0,'whole_body_translation':[0,0],'moved_native_texels':moved,'changed_pixels':int(np.count_nonzero(new!=a)),'outside_grip_scope_exact':True,'after_sha256':hashlib.sha256((O/f'b0_{n:03}_indices.png').read_bytes()).hexdigest()})
for form,words in[('normal',pal),('black',black)]:page(items[form],rgba(render(arc,0,0,147)[0],words),O/f'{form}_comparison.png',cols=3,scale=5)
(O/'registration.json').write_text(json.dumps({'records':records,'method':'178 새 장갑1px 아래,182 새 장갑/손목2px 오른쪽(상완끝1px),186 새 장갑/손목1px 오른쪽·아래. 새원화 texel만 이동하며 손 위치를 맞추기 위해 몸 전체를 이동하지 않는다.','source_legfix':str(P.relative_to(ROOT)),'root_review_pending':True,'user_accepted':False},ensure_ascii=False,indent=2)+'\n','utf8');print(O)
