from pathlib import Path
import sys,json
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT))
from scripts.discover_inputs import psx_arc
from scripts.repack_zero import read_inputs
from src.psx_player import graphics_bank,bank_offsets,decode_stream,composition_frame,compose_indices
from src.psx_bank_patch import patch_bank
from src.psx_ryuenjin import NEW_BODY
D=Path(__file__).parent;B=Path(json.loads((D/'builds.json').read_text())['build']['output']);P=ROOT/'out/ver_buki_riko/riko_bank1_20261025T111007087049Z'
before=(P/'modified.arc').read_bytes();after=(B/'modified.arc').read_bytes();e=next(e for e in psx_arc(after) if e['type']=='0x2');lo=e['offset'];hi=lo+e['size']
assert before[:lo]==after[:lo] and before[hi:]==after[hi:]
unchanged=[p.name for p in P.glob('*.png') if p.read_bytes()==(B/p.name).read_bytes()];changed=[p.name for p in P.glob('*.png') if p.name not in unchanged]
assert len(unchanged)==276 and changed==[]
_,_,_,_,g,parts,_=read_inputs(ROOT/'work/ver_buki_riko/zero_extract/20261023T062408235550Z')
actual=[];b,a=before[lo:hi],after[lo:hi]
for bi in range(len(bank_offsets(g))):
 for f in graphics_bank(g,bi)['frames']:
  x=decode_stream(b,f['offset'],f['limit'],f['tile_count']*128).data;y=decode_stream(a,f['offset'],f['limit'],f['tile_count']*128).data
  if x!=y:
   c=composition_frame(parts,0 if bi==0 else 5,f['index'])
   if compose_indices(x,f['tile_count'],c)[:2]!=compose_indices(y,f['tile_count'],c)[:2]:actual.append((bi,f['index']))
assert set(actual)=={(1,n) for n in NEW_BODY}
recipe=json.loads((D/'recipe.json').read_text());originals={}
for key in recipe['frames']:
 n=int(key);f=graphics_bank(g,1)['frames'][n];raw=decode_stream(g,f['offset'],f['limit'],f['tile_count']*128).data;originals[n]=compose_indices(raw,f['tile_count'],composition_frame(parts,5,n))[:2]
same,checks=patch_bank(g,parts,1,5,originals,recipe['preserved_effect_frames'],clear_unreferenced=True);assert same==g
result={'build':str(B),'previous_build':str(P),'previous_pngs_byte_identical':276,'changed_previous_pngs':changed,'changed_composed_references':actual,'original_unmodified_roundtrip_references':len(originals),'original_unmodified_roundtrip_byte_identical':True,'graphics_entry_only_changed':True,'preserved_effects':recipe['preserved_effect_frames'],'external_parts6_unchanged':True,'all_spin_body_pngs_byte_identical':True,'new_body':sorted(NEW_BODY),'shared_extra_techniques_runtime_not_verified':True}
rejected=ROOT/'out/ver_buki_riko/riko_bank1_20261025T113810331552Z'
revised=[p.name for p in rejected.glob('*.png') if p.read_bytes()!=(B/p.name).read_bytes()]
assert set(revised)=={f'bank1_{n:03d}.png' for n in (144,146,148,150,152,154,156,158)}
from src.sprite_scale import validate_fixed_reference
from src.psx_frame_edit import read_indexed_png
from PIL import Image
import numpy as np,struct
pal=struct.unpack('<16H',(ROOT/'out/ver_buki_riko/riko_pilot_20261023T082720987715Z/candidate_palette.bin').read_bytes())
rear=read_indexed_png(D.parent/'ladder_v1/rear_head_indexed.png',pal)
f=graphics_bank(g,1)['frames'][148];raw=decode_stream(g,f['offset'],f['limit'],f['tile_count']*128).data
bounds={148:compose_indices(raw,f['tile_count'],composition_frame(parts,5,148))[2]}
placement={'148':recipe['body_standard']['head_world_positions']['148']}
validate_fixed_reference({148:read_indexed_png(B/'bank1_148.png',pal)},bounds,*rear,(0,0,23,19),placement)
try:validate_fixed_reference({148:read_indexed_png(rejected/'bank1_148.png',pal)},bounds,*rear,(0,0,23,19),placement)
except ValueError:wrong_front_rejected=True
else:raise ValueError('Front-facing regression passed rear-view guard')
result.update(rejected_build=str(rejected),revised_since_rejected=revised,rear_view_frames=[148,150,152,154],front_pose_substitution_rejected=wrong_front_rejected)
(D/'preservation_audit.json').write_text(json.dumps(result,indent=2),'utf8');print(json.dumps(result))

