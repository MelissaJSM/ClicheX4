from pathlib import Path
import sys,json,random,struct,itertools,time
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT))
from src.psx_player import graphics_bank,decode_stream,composition_frame,compose_indices,indexed_atlas
from src.psx_frame_edit import edit_frame_indices
from src.psx_compress import encode_stream
from PIL import Image
import numpy as np
ex=(ROOT/json.loads((ROOT/'projects/ver_buki_riko/shibuki_source_inventory.json').read_text())['inventory']).parent
gfx=(ex/'graphics_entry.bin').read_bytes();parts=(ex/'composition_entry.bin').read_bytes()
desc=graphics_bank(gfx,0,allow_bank_aliases=True)['frames'][0];raw=decode_stream(gfx,desc['offset'],desc['limit'],desc['tile_count']*128)
a=np.array(Image.open(Path(__file__).parent/'candidate01/shibuki_idle000_indexed.png'))
best=9999;start=time.monotonic();rng=random.Random(42)
perms=[tuple(range(7))]*2048
for i,perm in enumerate(perms):
 p=bytearray(parts)
 flips=[rng.choice([0,64,128,192]) for _ in range(7)]
 for q in composition_frame(parts,0,0)['parts']:
  p[q['record_offset']+1]=perm[q['tile']]
  p[q['record_offset']]=q['flags']^flips[q['tile']]
 comp=composition_frame(p,0,0)
 packed=edit_frame_indices(raw.data,desc['tile_count'],comp,a.tobytes(),(48,48))
 encoded=encode_stream(packed)
 if len(encoded)<best:
  best=len(encoded);print(i,best,perm,flips,flush=True)
  (Path(__file__).parent/'packing_flip_best.json').write_text(json.dumps({'frame':0,'tile_permutation':perm,'tile_flips':flips,'encoded_bytes':best,'attempt':i,'source':'candidate01'},indent=2))
 if best<=1322:break
print('done',i,best,round(time.monotonic()-start,2),flush=True)
