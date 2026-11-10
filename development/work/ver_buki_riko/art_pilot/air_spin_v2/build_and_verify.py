from pathlib import Path
import sys,json,io,contextlib
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT))
from scripts.build_riko_bank1 import build
from scripts.verify_riko_build import verify
from scripts.riko_master_sheet import export,split
D=Path(__file__).parent
E=ROOT/'work/ver_buki_riko/zero_extract/20261023T062408235550Z'
def invoke(fn,*args):
 out=io.StringIO()
 with contextlib.redirect_stdout(out):fn(*args)
 return json.loads(out.getvalue())
def run():
 if (D/'builds.json').exists():raise ValueError('Preserve existing builds')
 parent=ROOT/'out/ver_buki_riko/riko_motion_20261025T090302549047Z'
 b=invoke(build,parent,E,D/'recipe.json');repeat=invoke(build,parent,E,D/'recipe.json')
 rec={'parent':str(parent),'build':b,'repeat':repeat};(D/'builds.json').write_text(json.dumps(rec,indent=2),'utf8');print(json.dumps(rec),flush=True)
 v=invoke(verify,Path(b['output']),Path(repeat['output']));(D/'verify_result.json').write_text(json.dumps(v,indent=2),'utf8');print('BIN verification passed',flush=True)
 m=invoke(export,Path(b['output']),E,ROOT/'work/ver_buki_riko/animation_inventory/20261023T095844768051Z');(D/'master_export.json').write_text(json.dumps(m,indent=2),'utf8');print(json.dumps(m),flush=True)
 mp=Path(m['output']);s=invoke(split,mp/'master.local.json',mp/'riko_master_indexed.png');(D/'master_split.json').write_text(json.dumps(s,indent=2),'utf8');print(json.dumps(s),flush=True)
if __name__=='__main__':run()
