import json,sys,struct
from pathlib import Path
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT))
from src.epsxe_state import framebuffer,match_sprite
rows=[]
for suffix in ('20261026T093239392898Z','20261026T093250205909Z'):
 d=ROOT/'work/ver_buki_riko/shibuki_run_runtime'/suffix;r=json.loads((d/'verification.local.json').read_text());v=(d/'diagnostic_vram_086.bin').read_bytes();src=Image.open(d/'expected_086.png');best=None
 for pal in r['observed_palette_hex']:
  rgb=[]
  for w in struct.unpack('<16H',bytes.fromhex(pal)):rgb.extend(((w&31)*255//31,((w>>5)&31)*255//31,((w>>10)&31)*255//31))
  p=src.copy();p.putpalette(rgb+[0]*(768-len(rgb)));full=np.array(p.convert('RGBA'));masked=full.copy();masked[:-15,:,3]=0;target=Image.fromarray(masked)
  for page in (0,256):
   screen=framebuffer(v,0,page);a=np.array(screen)
   for match in match_sprite(screen,target):
    if match['flip_x']!=(r['direction']=='right'):continue
    ref=full[:,::-1] if match['flip_x'] else full;x,y=match['x'],match['y'];crop=a[y:y+ref.shape[0],x:x+ref.shape[1]];opaque=ref[:,:,3]!=0;diff=opaque&np.any(ref[:,:,:3]!=crop,2);ys,xs=np.nonzero(diff);count=int(diff.sum())
    row={'direction':r['direction'],'source':str(d.relative_to(ROOT)),'palette_hex':pal,'page':page,'origin':[x,y],'opaque_pixels':int(opaque.sum()),'different_pixels':count,'difference_bbox':None if not count else [int(xs.min()),int(ys.min()),int(xs.max()+1),int(ys.max()+1)],'difference_coordinates':list(map(list,zip(xs.tolist(),ys.tolist())))}
    if best is None or count<best['different_pixels']:
     best=row;Image.fromarray(ref).save(d/'flash_expected_086.png');screen.save(d/'flash_actual_086.png')
 rows.append(best)
print(json.dumps(rows));(Path(__file__).parent/'flash_diagnostics.json').write_text(json.dumps(rows,indent=2))
