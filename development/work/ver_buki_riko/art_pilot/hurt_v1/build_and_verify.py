from pathlib import Path
import sys,json,io,contextlib
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT))
from scripts.build_riko_idle import build as bank0_build
from scripts.build_riko_bank1 import build as bank1_build
from scripts.verify_riko_build import verify
from scripts.riko_master_sheet import export,split
D=Path(__file__).parent
E=ROOT/'work/ver_buki_riko/zero_extract/20261023T062408235550Z'
IDLE=ROOT/'work/ver_buki_riko/art_pilot/scale_consistency/walk_design_basis'
def invoke(function,*args):
 out=io.StringIO()
 with contextlib.redirect_stdout(out):function(*args)
 return json.loads(out.getvalue())
def run():
 if (D/'builds.json').exists():raise ValueError('Build record exists; preserve it')
 p0=invoke(bank0_build,E,IDLE,D/'motion_set.json',False,IDLE/'idle_revision.json')
 wall=ROOT/'work/ver_buki_riko/art_pilot/wall_saber_v2/recipe.json'
 b=invoke(bank1_build,Path(p0['output']),E,wall);repeat=invoke(bank1_build,Path(p0['output']),E,wall)
 record={'parent':p0,'build':b,'repeat':repeat};(D/'builds.json').write_text(json.dumps(record,indent=2)+'\n','utf8')
 print(json.dumps(record),flush=True)
 v=invoke(verify,Path(b['output']),Path(repeat['output']));(D/'verify_result.json').write_text(json.dumps(v,indent=2),'utf8');print(json.dumps(v),flush=True)
 m=invoke(export,Path(b['output']),E,ROOT/'work/ver_buki_riko/animation_inventory/20261023T095844768051Z')
 (D/'master_export.json').write_text(json.dumps(m,indent=2),'utf8');print(json.dumps(m),flush=True)
 mp=Path(m['output']);s=invoke(split,mp/'master.local.json',mp/'riko_master_indexed.png')
 (D/'master_split.json').write_text(json.dumps(s,indent=2),'utf8');print(json.dumps(s),flush=True)
if __name__=='__main__':run()
