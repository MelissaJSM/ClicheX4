from pathlib import Path
import json,copy,sys
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT))
from scripts.build_riko_bank1 import read_set
from scripts.repack_zero import read_inputs
from src.psx_frame_edit import read_indexed_png
import struct
D=Path(__file__).parent
profile,_,_,_,gfx,parts,_=read_inputs(ROOT/'work/ver_buki_riko/zero_extract/20261023T062408235550Z')
P=ROOT/'out/ver_buki_riko/riko_pilot_20261023T082720987715Z';pal=(P/'candidate_palette.bin').read_bytes();ref=read_indexed_png(P/'riko_idle147_indexed.png',struct.unpack('<16H',pal))
base=json.loads((D/'recipe.json').read_text());results=[]
for name in ('wrong_source','wrong_graphics','wrong_palette','wrong_parts_bank','missing_shared_frame','wrong_png_hash','escaped_png','wrong_head','anisotropic','wrong_wall_view'):
 r=copy.deepcopy(base)
 if name=='wrong_source':r['source_sha256']='0'*64
 elif name=='wrong_graphics':r['original_graphics_sha256']='0'*64
 elif name=='wrong_palette':r['palette_sha256']='0'*64
 elif name=='wrong_parts_bank':r['parts_bank']=0
 elif name=='missing_shared_frame':del r['frames']['53']
 elif name=='wrong_png_hash':r['frames']['50']['sha256']='0'*64
 elif name=='escaped_png':r['frames']['50']['file']='../outside.png'
 elif name=='wrong_head':r['body_standard']['head_world_positions']['50'][0]+=1
 elif name=='anisotropic':r['body_standard']['anisotropic_scale']=True
 elif name=='wrong_wall_view':r['body_standard']['wall_view_config_sha256']='0'*64
 p=D/f'guard_{name}.json';p.write_text(json.dumps(r))
 try:read_set(p,profile['source_sha256'],pal,gfx,parts,ref)
 except ValueError as e:results.append({'case':name,'rejected':True,'reason':str(e)})
 else:raise AssertionError(name+' unexpectedly accepted')
(D/'guard_checks.json').write_text(json.dumps(results,indent=2));print(json.dumps({'rejected_cases':len(results)}))
