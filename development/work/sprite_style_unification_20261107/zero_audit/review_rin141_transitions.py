"""Fixed-origin transition and head-band sheets; no sprite edits."""
from pathlib import Path
import sys,struct,json,hashlib
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from scripts.prepare_riko_ui import entry
from scripts.overhaul_sprites_audit import render,rgba
D=Path(__file__).parent/'rin_extension';O=D/'ground_wall141_review'
old=(D/'prepared_ground_first_v1/PL01_U.ARC').read_bytes()
new=(D/'prepared_ground_wall_v1/PL01_U.ARC').read_bytes()
assert hashlib.sha256(new).hexdigest()=='247b47bcbf91eea64697305ba5a705de02207682c46fbbab0b527f9df00d6bb6'
groups={'ground_transitions':(0,[69,71,73,82,131,133]),'wall_transitions':(1,[50,51,54,57,56,53])}
for name,(bank,refs) in groups.items():
 for form,p in [('normal',0),('black',13)]:
  words=struct.unpack_from('<16H',entry(new,9),p*32)
  sheet=Image.new('RGB',(1152,624),'#64717b');dr=ImageDraw.Draw(sheet)
  for i,n in enumerate(refs):
   for row,(arc,label) in enumerate([(old,'old'),(new,'new')]):
    im=rgba(render(arc,bank,bank*5,n)[0],words).crop((112,112,208,208)).resize((192,192),Image.Resampling.NEAREST)
    x=i*192;y=row*312;sheet.paste(im,(x,y+36),im);dr.text((x+4,y+6),f'{label} b{bank}:{n}',fill='white')
  sheet.save(O/f'{name}_{form}.png')
head=Image.new('RGB',(960,384),'#64717b');dr=ImageDraw.Draw(head)
words=struct.unpack_from('<16H',entry(new,9))
for i,(label,arc,n)in enumerate([('idle',new,147),('old71',old,71),('new71',new,71),('old73',old,73),('new73',new,73)]):
 im=rgba(render(arc,0,0,n)[0],words).crop((130,128,170,166)).resize((160,152),Image.Resampling.NEAREST)
 head.paste(im,(i*192+16,32),im);dr.text((i*192+4,4),label,fill='white')
head.save(O/'head_band_comparison.png')
print(O)
