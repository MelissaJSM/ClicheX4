from pathlib import Path
import sys,json,io,contextlib
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT))
from scripts.build_riko_bank1 import build
from scripts.verify_riko_build import verify
from scripts.repack_zero import read_inputs
from src.psx_player import graphics_bank,decode_stream,composition_frame,compose_indices
from src.psx_frame_edit import edit_frame_set
D=Path(__file__).parent;E=ROOT/'work/ver_buki_riko/zero_extract/20261023T062408235550Z'
P=ROOT/'out/ver_buki_riko/riko_bank1_20261025T172453977111Z'
parent=Path(json.loads((D.parent/'beam_in_v2/builds.json').read_text())['parent'])
def call(fn,*args,log):
    capture=io.StringIO()
    with contextlib.redirect_stdout(capture):fn(*args)
    (D/log).write_text(capture.getvalue(),'utf8');return json.loads(capture.getvalue().splitlines()[-1])
if '--audit-existing' in sys.argv:
    previous=json.loads((D/'builds.json').read_text());b=previous['build'];repeat=previous['repeat'];verification=json.loads((D/'verification.log').read_text().splitlines()[-1])
else:
    b=call(build,parent,E,D/'recipe.json',log='build.log')
    repeat=call(build,parent,E,D/'recipe.json',log='repeat.log')
    (D/'builds.json').write_text(json.dumps({'parent':str(parent),'build':b,'repeat':repeat},indent=2),'utf8')
    verification=call(verify,Path(b['output']),Path(repeat['output']),log='verification.log')
new=Path(b['output']);preserved=[]
for p in P.glob('*.png'):
    if not (new/p.name).exists() or p.read_bytes()!=(new/p.name).read_bytes():raise ValueError(('Previous PNG changed',p.name))
    preserved.append(p.name)
_,_,arc,gm,gfx,parts,_=read_inputs(E);bank=graphics_bank(gfx,1);seen=set();roundtrips=[]
for n in range(14):
    f=bank['frames'][n]
    if f['offset'] in seen:continue
    seen.add(f['offset']);raw=decode_stream(gfx,f['offset'],f['limit'],f['tile_count']*128).data
    ns=[n for n in range(14) if bank['frames'][n]['offset']==f['offset']]
    edits=[(composition_frame(parts,5,n),*compose_indices(raw,f['tile_count'],composition_frame(parts,5,n))[:2]) for n in ns if n<9]
    assert edit_frame_set(raw,f['tile_count'],edits,preserved_compositions=[composition_frame(parts,5,n) for n in ns if n>=9])==raw
    roundtrips.extend(ns)
newarc=(new/'modified.arc').read_bytes();ng=newarc[gm['offset']:gm['offset']+gm['size']];same=[]
for n in range(9,14):
    f=bank['frames'][n];size=f['tile_count']*128;c=composition_frame(parts,5,n)
    assert compose_indices(decode_stream(ng,f['offset'],f['limit'],size).data,f['tile_count'],c)==compose_indices(decode_stream(gfx,f['offset'],f['limit'],size).data,f['tile_count'],c)
    same.append(n)
audit={'previous_png_byte_identical':preserved,'previous_png_count':len(preserved),'original_decoded_roundtrip_byte_equal':sorted(roundtrips),'pure_beam_compositions_preserved':same,'repeat_bin_equal':b['sha256']==repeat['sha256'],'verification_report':verification['report'],'changed_sectors':len(verification['changed_sectors']),'composition_changed':False,'animation_timing_changed':False,'relocated':False}
(D/'preservation_audit.json').write_text(json.dumps(audit,indent=2),'utf8');print(json.dumps({'build':b,'repeat':repeat,'preserved_pngs':len(preserved),'changed_sectors':audit['changed_sectors']}))
