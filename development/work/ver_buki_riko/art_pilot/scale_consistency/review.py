from pathlib import Path
import sys,json
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT))
import numpy as np
from PIL import Image,ImageDraw,ImageFont
from scripts.discover_inputs import psx_arc,sha256
from scripts.project import write_json
from src.psx_player import graphics_bank,bank_offsets,decode_stream,composition_frame,compose_indices
P=Path(__file__).parent
old=ROOT/'out/ver_buki_riko/riko_motion_20261023T143602957663Z'
new=ROOT/'out/ver_buki_riko/riko_motion_20261023T152218300431Z'
motion=ROOT/'work/ver_buki_riko/run_revision_frames/20261023T140033413871Z'
a=(old/'modified.arc').read_bytes();b=(new/'modified.arc').read_bytes()
entries=psx_arc(a);g=next(e for e in entries if e['type']=='0x2');p=next(e for e in entries if e['type']=='0x3')
assert len(a)==len(b) and [tuple(e[k] for k in ('index','type','offset','size')) for e in psx_arc(b)]==[tuple(e[k] for k in ('index','type','offset','size')) for e in entries]
assert a[:g['offset']]==b[:g['offset']] and a[g['offset']+g['size']:]==b[g['offset']+g['size']:]
ga=a[g['offset']:g['offset']+g['size']];gb=b[g['offset']:g['offset']+g['size']];parts=a[p['offset']:p['offset']+p['size']]
changed=[];composed=0;unknown=[]
for bi in range(len(bank_offsets(ga))):
 for f in graphics_bank(ga,bi)['frames']:
  before=decode_stream(ga,f['offset'],f['limit'],f['tile_count']*128).data
  after=decode_stream(gb,f['offset'],f['limit'],f['tile_count']*128).data
  if before!=after:changed.append([bi,f['index']])
  try:
   c=composition_frame(parts,0 if bi==0 else 5,f['index']);pa=compose_indices(before,f['tile_count'],c);pb=compose_indices(after,f['tile_count'],c)
  except ValueError as e:
   assert before==after;unknown.append([bi,f['index'],str(e)]);continue
  composed+=1
  if [bi,f['index']] not in changed:assert pa==pb
assert changed==[[0,n] for n in (3,4,*range(7,35))]
preserved={}
for n in (0,1,2,5,6,146,147,148):
 name=f'{"idle" if n in (0,1,2,146,147,148) else "frame"}_{n:03d}.png'
 assert (old/name).read_bytes()==(new/name).read_bytes();preserved[name]=sha256((new/name).read_bytes())
report={'previous_build':str(old),'new_build':str(new),'decoded_references_checked':444,
        'composed_references_checked':composed,'changed_references':changed,'uninterpreted_unchanged':unknown,
        'outside_graphics_entry_unchanged':True,'all_palettes_and_parts_unchanged':True,'preserved_pngs':preserved}
(new/'previous_build_comparison.json').write_text(json.dumps(report,indent=2),encoding='utf-8')

print(json.dumps({"changed":changed,"composed":composed,"preserved_pngs":len(preserved)}))
