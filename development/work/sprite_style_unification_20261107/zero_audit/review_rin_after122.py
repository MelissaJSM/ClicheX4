"""Read new source/native pixels and make fixed-origin contact evidence only."""
from pathlib import Path
import sys,json,struct,hashlib
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from scripts.overhaul_sprites_audit import render,rgba
from scripts.prepare_riko_ui import entry
D=Path(__file__).parent/'rin_extension';O=D/'after122_contact_review';O.mkdir(exist_ok=True)
arc=(D/'prepared_ground_first_v1/PL01_U.ARC').read_bytes()
assert hashlib.sha256(arc).hexdigest()=='cf01c08e17c742983abcd566e08f165c2c48205b453d051ce64ea58ca1a8c0c1'
pal=struct.unpack_from('<16H',entry(arc,9));records=[]
for page in ('ground_followup01','wall_saber01'):
 info=json.loads((D/page/'inputs.json').read_text('utf8'))
 for f in info['frames']:
  old=render(arc,f['bank'],f['bank']*5,f['ref'])[0];new=np.array(Image.open(D/page/'native'/(f['key']+'_indices.png')))
  crop=(124,128,192,192);scale=10;panels=[]
  for title,a in [('before',old),('source-native',new)]:
   p=Image.new('RGB',(720,680),(24,32,44));p.paste(rgba(a,pal).crop(crop).resize((680,640),Image.Resampling.NEAREST),(36,30));dr=ImageDraw.Draw(p)
   dr.text((5,5),f['key']+' '+title,fill='white')
   for x in range(124,193):
    xx=36+(x-124)*scale
    dr.line((xx,30,xx,670),fill=(36,45,60) if x%4 else (65,75,90))
    if x%4==0:dr.text((xx-7,16),str(x-160),fill=(180,190,210))
   for y in range(128,193):
    yy=30+(y-128)*scale
    dr.line((36,yy,716,yy),fill=(36,45,60) if y%4 else (65,75,90))
    if y%4==0:dr.text((4,yy-4),str(y-160),fill=(180,190,210))
   panels.append(p)
  sheet=Image.new('RGB',(1440,680));sheet.paste(panels[0],(0,0));sheet.paste(panels[1],(720,0));sheet.save(O/(f['key']+'_grid.png'))
  records.append({'key':f['key'],'page':page,'source_native':str((D/page/'native'/(f['key']+'_indices.png')).relative_to(ROOT)),'old_bounds':rgba(old,pal).getbbox(),'new_bounds':rgba(new,pal).getbbox()})
(O/'inventory.json').write_text(json.dumps({'records':records,'palette':list(pal),'source_sha256':hashlib.sha256(arc).hexdigest(),'reviewed':False},indent=2)+'\n','utf8')
print(str(O))
