from pathlib import Path
import sys,json,itertools,random,math
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT))
from scripts.discover_inputs import psx_arc
from src.psx_player import graphics_bank,decode_stream
from src.psx_compress import encode_stream
from src.psx_paired_layout import pack_joint_pair
from src.psx_tile_layout import remap_tiles
d=Path(__file__).parent;p=d/'paired';layout=json.loads((d/'pair23_union_layout.json').read_text())
arc=(ROOT/'out/ver_buki_riko/shibuki_idle_20261026T064845428866Z/modified.arc').read_bytes()
e=next(e for e in psx_arc(arc) if int(e['type'],16)==2);gfx=arc[e['offset']:e['offset']+e['size']];f=graphics_bank(gfx,0,allow_bank_aliases=True)['frames'][23]
dec=decode_stream(gfx,f['offset'],f['limit'],f['tile_count']*128)
raw,rp,sp,blank,target=pack_joint_pair(dec.data,f['tile_count'],np.array(Image.open(p/'run_023.png')),np.array(Image.open(p/'shoot_023.png')),layout['rects'],layout['unique_rects'],set(range(9)))
mapping={t:t for t in range(9)};flips={};size=len(encode_stream(raw));budget=dec.end-dec.start
print(json.dumps({'initial':size,'budget':budget}),flush=True)
if size>budget:
 for a,b in itertools.combinations(range(9),2):
  m={t:t for t in range(9)};m[a],m[b]=b,a
  try:packed=remap_tiles(raw,f['tile_count'],m)
  except ValueError:continue
  trial=len(encode_stream(packed))
  if trial<size:size,mapping=trial,m
  if size<=budget:break
for sweep in range(8):
 if size<=budget:break
 improved=False;candidates=[]
 for a,b in itertools.combinations(range(9),2):
  m=dict(mapping);m[a],m[b]=m[b],m[a];candidates.append((m,dict(flips)))
 for t in range(9):
  for flag in (64,128,192):
   f2=dict(flips);f2[t]=f2.get(t,0)^flag;candidates.append((dict(mapping),f2))
 for m,f2 in candidates:
  try:packed=remap_tiles(raw,f['tile_count'],m,f2)
  except ValueError:continue
  trial=len(encode_stream(packed))
  if trial<size:size,mapping,flips=trial,m,f2;improved=True
  if size<=budget:break
 print(json.dumps({'sweep':sweep,'best':size,'budget':budget}),flush=True)
 if not improved:break
if size>budget:raise RuntimeError(f'Joint packing overflow {size}/{budget}')
record={'frame':23,'encoded_bytes':size,'budget':budget,'fits':True,'mapping':mapping,'flips':flips,'common_rects':layout['rects'],'joint_unique_rects':layout['unique_rects']}
records=json.loads((p/'packing.json').read_text());records=[record if r['frame']==23 else r for r in records]
(p/'packing.json').write_text(json.dumps(records,indent=2));print(json.dumps(record))
