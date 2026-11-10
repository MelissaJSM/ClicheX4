from pathlib import Path
import hashlib,json,struct,sys
import numpy as np
from PIL import Image
O=Path(__file__).resolve().parent;W=O.parent;ROOT=W.parents[1];sys.path.insert(0,str(ROOT))
from scripts.export_x_consistency import Archive
from src.epsxe_state import framebuffer,match_sprite
P=O/'rn43_fourth_flash01';plan=json.loads((W/'staging_rn_v43.json').read_text('utf8'));src=plan['resources']['PL00_U.ARC'];blob=(ROOT/src['path']).read_bytes();assert hashlib.sha256(blob).hexdigest()==src['after'];a=Archive(blob)
im=a.composite(140,15)[0];base=a.composite(140,0)[0];bb=im.getbbox();rows=[];display=struct.unpack_from('<4h',(P/'ram.bin').read_bytes(),0x166c10);assert display==(0,240,320,240)
for p in sorted(P.glob('vram*.bin')):
    video=p.read_bytes()
    for page in (0,240):
        screen=framebuffer(video,0,page);hits=match_sprite(screen,im.crop(bb))
        rows.append({'vram':p.name,'page':page,'matches':hits})
report={'matches':rows,'opaque_pixels':int(np.count_nonzero(np.array(im)[:,:,3])),'extra_armor_pixels':int(np.count_nonzero((np.array(im)[:,:,3]>0)&(np.array(base)[:,:,3]==0))),'bbox':bb,'source_arc_sha256':src['after'],'costume':'full Fourth armor','any_full_match':any(r['matches']for r in rows)}
report.update(display_environment=display,framebuffer_pages=[0,240]);(P/'fourth_screen_match_display.json').write_text(json.dumps(report,indent=2)+'\n','utf8');framebuffer((P/'vram02.bin').read_bytes(),0,240).resize((640,480),Image.Resampling.NEAREST).save(P/'capture02_page240.png');print(json.dumps(report))
