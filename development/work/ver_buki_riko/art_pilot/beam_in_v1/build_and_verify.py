from pathlib import Path
import sys,json,io,contextlib
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT))
from scripts.build_riko_idle import build as bank0_build
from scripts.build_riko_bank1 import build as bank1_build
from scripts.verify_riko_build import verify
from scripts.project import digest
from scripts.repack_zero import read_inputs
from scripts.discover_inputs import psx_arc
from src.psx_player import graphics_bank,decode_stream,composition_frame,compose_indices
from src.psx_frame_edit import edit_frame_set
D=Path(__file__).parent;E=ROOT/'work/ver_buki_riko/zero_extract/20261023T062408235550Z'
P=ROOT/'out/ver_buki_riko/riko_bank1_20261025T134737617192Z'
def call(fn,*args,log):
    capture=io.StringIO()
    with contextlib.redirect_stdout(capture):fn(*args)
    (D/log).write_text(capture.getvalue(),'utf8')
    return json.loads(capture.getvalue().splitlines()[-1])
parent=call(bank0_build,E,ROOT/'work/ver_buki_riko/art_pilot/scale_consistency/walk_design_basis',D/'motion_set.json',False,
            ROOT/'work/ver_buki_riko/art_pilot/scale_consistency/walk_design_basis/idle_revision.json',log='bank0_build.log')
recipe=ROOT/'work/ver_buki_riko/art_pilot/raijingeki_v1/recipe.json'
b=call(bank1_build,Path(parent['output']),E,recipe,log='build.log')
repeat=call(bank1_build,Path(parent['output']),E,recipe,log='repeat.log')
result={'parent':parent['output'],'build':b,'repeat':repeat};(D/'builds.json').write_text(json.dumps(result,indent=2),'utf8')
verification=call(verify,Path(b['output']),Path(repeat['output']),log='verification.log')
new=Path(b['output']);preserved=[]
for p in P.glob('*.png'):
    if not (new/p.name).exists() or p.read_bytes()!=(new/p.name).read_bytes():raise ValueError(('Previous PNG changed',p.name))
    preserved.append(p.name)
_,_,arc,gm,gfx,parts,_=read_inputs(E);bank=graphics_bank(gfx,0);seen=set();roundtrips=[]
for n in range(247,254):
    f=bank['frames'][n]
    if f['offset'] in seen:continue
    seen.add(f['offset']);raw=decode_stream(gfx,f['offset'],f['limit'],f['tile_count']*128).data
    ns=[n for n in range(247,254) if bank['frames'][n]['offset']==f['offset']]
    edits=[(composition_frame(parts,0,n),*compose_indices(raw,f['tile_count'],composition_frame(parts,0,n))[:2]) for n in ns]
    assert edit_frame_set(raw,f['tile_count'],edits)==raw
    roundtrips.extend(ns)
newarc=(new/'modified.arc').read_bytes();oldarc=(P/'modified.arc').read_bytes()
ng=newarc[gm['offset']:gm['offset']+gm['size']];og=oldarc[gm['offset']:gm['offset']+gm['size']]
same=[]
for n in range(53,61):
    f=bank['frames'][n];size=f['tile_count']*128
    assert decode_stream(ng,f['offset'],f['limit'],size).data==decode_stream(og,f['offset'],f['limit'],size).data
    same.append(n)
audit={'previous_png_byte_identical':preserved,'previous_png_count':len(preserved),
       'original_decoded_roundtrip_byte_equal':sorted(roundtrips),'pure_beam_indices_preserved':same,
       'source_sha256':json.loads((new/'manifest.json').read_text())['source_sha256'],
       'repeat_bin_equal':b['sha256']==repeat['sha256'],'verification_report':verification['report'],
       'changed_sectors':len(verification['changed_sectors']),
       'composition_changed':False,'animation_timing_changed':False,'relocated':False}
(D/'preservation_audit.json').write_text(json.dumps(audit,indent=2),'utf8')
print(json.dumps({'build':b,'repeat':repeat,'preserved_pngs':len(preserved),'changed_sectors':audit['changed_sectors']}))
