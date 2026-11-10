from pathlib import Path
import sys,json,random,itertools,time
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT))
from src.psx_player import graphics_bank,decode_stream,composition_frame
from src.psx_frame_edit import edit_frame_indices
from src.psx_compress import encode_stream
from PIL import Image
import numpy as np
ex=(ROOT/json.loads((ROOT/'projects/ver_buki_riko/shibuki_source_inventory.json').read_text())['inventory']).parent
gfx=(ex/'graphics_entry.bin').read_bytes();parts=(ex/'composition_entry.bin').read_bytes()
desc=graphics_bank(gfx,0,allow_bank_aliases=True)['frames'][0];raw=decode_stream(gfx,desc['offset'],desc['limit'],desc['tile_count']*128)
a=np.array(Image.open(Path(__file__).parent/'candidate01/shibuki_idle000_indexed.png'));comp=composition_frame(parts,0,0)
mapping=np.arange(16,dtype=np.uint8);best=1348;start=time.monotonic();trials=0
for iteration in range(12):
 improved=False
 for i,j in itertools.combinations(range(1,16),2):
  trial=mapping.copy();trial[i],trial[j]=trial[j],trial[i]
  packed=edit_frame_indices(raw.data,desc['tile_count'],comp,trial[a].tobytes(),(48,48));encoded=encode_stream(packed);trials+=1
  if len(encoded)<best:
   best=len(encoded);mapping=trial;improved=True
   print(trials,best,mapping.tolist(),flush=True)
   (Path(__file__).parent/'palette_probe_best.json').write_text(json.dumps({'old_index_to_new':mapping.tolist(),'encoded_bytes':best,'attempt':trials,'source':'candidate01'},indent=2))
  if best<=1322:break
 if best<=1322 or not improved:break
print('done',trials,best,round(time.monotonic()-start,2),flush=True)
