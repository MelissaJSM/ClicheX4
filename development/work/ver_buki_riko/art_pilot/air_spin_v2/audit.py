from inspect_fit import *
from src.psx_player import graphics_bank,decode_stream,compose_indices,composition_frame,bank_offsets
from src.psx_bank_patch import patch_bank
from scripts.discover_inputs import psx_arc,sha256
from scripts.build_riko_bank1 import read_set
from scripts.extract_zero import save_image
from src.psx_air_spin import BODY as SPIN_BODY,EFFECTS as SPIN_FX

def run():
 builds=json.loads((D/'builds.json').read_text());b=Path(builds['build']['output']);old=ROOT/'out/ver_buki_riko/riko_bank1_20261025T090314908139Z'
 a=(old/'modified.arc').read_bytes();z=(b/'modified.arc').read_bytes();gm=next(r for r in psx_arc(z) if r['type']=='0x2');lo,hi=gm['offset'],gm['offset']+gm['size']
 assert a[:lo]==z[:lo] and a[hi:]==z[hi:]
 unchanged=[p.name for p in old.glob('*.png') if p.read_bytes()==(b/p.name).read_bytes()]
 assert len(unchanged)==len(list(old.glob('*.png')))==236
 before,after=a[lo:hi],z[lo:hi];changed=[];composed=[]
 for bi in range(len(bank_offsets(before))):
  for f in graphics_bank(before,bi)['frames']:
   args=(f['offset'],f['limit'],f['tile_count']*128);x=decode_stream(before,*args).data;y=decode_stream(after,*args).data
   if x!=y:
    assert bi==1 and f['index'] in SPIN_BODY|SPIN_FX
    changed.append([bi,f['index']]);c=composition_frame(parts,5,f['index'])
    if compose_indices(x,f['tile_count'],c)[:2]!=compose_indices(y,f['tile_count'],c)[:2]:composed.append(f['index'])
 assert set(composed)==SPIN_BODY
 originals={}
 for n in sorted(SPIN_BODY|SPIN_FX):
  f=bank['frames'][n];raw=decode_stream(gfx,f['offset'],f['limit'],f['tile_count']*128).data
  originals[n]=compose_indices(raw,f['tile_count'],composition_frame(parts,5,n))[:2]
 same,report=patch_bank(gfx,parts,1,5,originals,SPIN_FX,clear_unreferenced=True);assert same==gfx
 result={'build':str(b),'previous':str(old),'previous_pngs_byte_identical':len(unchanged),'archive_outside_graphics_identical':True,
  'changed_decoded_stream_references':changed,'changed_composed_body_frames':composed,'original_effect_images_preserved':sorted(SPIN_FX),
  'original_unmodified_roundtrip_byte_identical':True,'source_bin_sha256':profile['source_sha256'],'original_roundtrip':report,
  'live_opposite_direction_priority':'Deferred by user; reflected U=0 boundary checks remain enforced by unchanged master split.',
  'image_tool':'built-in image_gen','external_original_sprite_inputs':False}
 (D/'preservation_audit.json').write_text(json.dumps(result,indent=2),'utf8');print(json.dumps({k:v for k,v in result.items() if k!='original_roundtrip'}))
if __name__=='__main__':run()
