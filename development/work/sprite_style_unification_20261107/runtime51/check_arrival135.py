from pathlib import Path
import hashlib,json,struct,sys
import numpy as np
from PIL import Image
O=Path(__file__).resolve().parent;W=O.parent;ROOT=W.parents[1];sys.path.insert(0,str(ROOT))
from scripts.export_x_consistency import Archive
from src.epsxe_state import framebuffer,match_sprite
P=O/'br32_arrival135';src=json.loads((W/'staging_br_v32.json').read_text('utf8'))['resources']['PL02_U.ARC'];data=(ROOT/src['path']).read_bytes();assert hashlib.sha256(data).hexdigest()==src['after'];a=Archive(data);rows=[];display=struct.unpack_from('<4h',(P/'ram.bin').read_bytes(),0x166c10);assert display[2:]==(320,240)
for p in sorted(P.glob('vram*.bin')):
 for page in(0,240):
  screen=framebuffer(p.read_bytes(),0,page)
  for mask in(0,15):
   im=a.composite(135,mask)[0];sprite=im.crop(im.getbbox())
   for flip in(False,True):
    pic=sprite.transpose(Image.Transpose.FLIP_LEFT_RIGHT)if flip else sprite;hits=match_sprite(screen,pic)
    if hits:rows.append({'vram':p.name,'page':page,'mask':mask,'flip':flip,'opaque_pixels':int(np.count_nonzero(np.array(sprite)[:,:,3])),'matches':hits})
report={'source_sha256':src['after'],'BIN_sha256':json.loads((P/'evidence.json').read_text('utf8'))['bin_sha256'],'display':list(display),'matches':rows,'actual_gameplay':True,'after_costume_full_match':any(r['mask']==0 for r in rows),'before_costume_observed':any(r['mask']==15 for r in rows)}
(P/'screen_matches.json').write_text(json.dumps(report,indent=2)+'\n','utf8');print(json.dumps(report))
