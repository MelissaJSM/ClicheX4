from pathlib import Path
import sys,json,struct,itertools
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT))
from scripts.prepare_shibuki_idle import breathe
from src.psx_player import graphics_bank,decode_stream,composition_frame
from src.psx_frame_edit import edit_frame_indices
from src.psx_compress import encode_stream
work=Path(__file__).parent;sel=json.loads((ROOT/'projects/ver_buki_riko/shibuki_unified_revision.json').read_text(encoding='utf-8'))
ex=ROOT/'work/ver_buki_riko/shibuki_x_extract/20261026T024200768121Z';gfx=(ex/'graphics_entry.bin').read_bytes();parts=(ex/'composition_entry.bin').read_bytes();bank=graphics_bank(gfx,0,allow_bank_aliases=True)
base=np.array(Image.open(ROOT/sel['indexed_png']));shift=sel['world_x_shift'];result={}
for n in (0,119):
 desc=bank['frames'][n];raw=decode_stream(gfx,desc['offset'],desc['limit'],desc['tile_count']*128);target=base if n==0 else breathe(base,-1)
 cases=[{}]+[{str(t):f} for t in range(7) for f in (64,128,192) if t!=0 or not f&64]
 cases += [{str(a):fa,str(b):fb} for a,b in itertools.combinations(range(7),2) for fa in (64,128) for fb in (64,128) if (a!=0 or fa!=64) and (b!=0 or fb!=64)]
 best=None
 for flips in cases:
  p=bytearray(parts)
  for q in composition_frame(parts,0,n)['parts']:
   struct.pack_into('<b',p,q['record_offset']+2,q['x']+shift);p[q['record_offset']]=q['flags']^flips.get(str(q['tile']),0)
  packed=edit_frame_indices(raw.data,desc['tile_count'],composition_frame(p,0,n),target.tobytes(),(48,48));size=len(encode_stream(packed))
  if best is None or size<best['bytes']:best={'bytes':size,'flips':flips};print(n,best,flush=True)
  if size<=raw.end-raw.start:break
 result[str(n)]=best
(work/'idle_packing.json').write_text(json.dumps(result,indent=2)+'\n')
