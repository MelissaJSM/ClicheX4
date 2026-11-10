"""Register cumulative stage manifests after preserving all previous pointers."""
import hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from src.steam_region_routes import SHARED
W=ROOT/'work/steam_port_20261109';D=W/'completion_audit'
def sha(b):return hashlib.sha256(b).hexdigest()
def encoded(v):return (json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode('utf8')
def main():
 builds=json.loads((W/'stage_completion_builds.json').read_text('utf8'));by={r['target_arc']:r for r in builds}
 proof=json.loads((D/'stage_completion_verification.json').read_text('utf8'))
 if not proof['passed'] or proof['archives']!=len(builds):raise ValueError('Stage verification required')
 if (D/'registration.json').exists():raise ValueError('Stage manifests already registered')
 updates={}
 for name in ['portrait_builds.json','audio_builds.json']:
  path=W/name;rows=json.loads(path.read_text('utf8'))
  for row in rows:
   target=row.get('target_arc',row.get('relative_path','').split('/')[-1]);new=by.get(target)
   if new:
    if row['output_sha256']!=new['parent_sha256']:raise ValueError('Cumulative manifest source differs: '+target)
    row.update({'output':new['output'],'output_sha256':new['output_sha256'],'stage_completion_parent':row['output_sha256'],'stage_completion_manifest':'stage_completion_builds.json'})
  if name=='portrait_builds.json':
   # These two stages need regional routing only; they contain no new portraits.
   for target in ['cliche_br_st0b_0z.arc','cliche_br_st0c_00.arc']:
    if any(r.get('target_arc')==target for r in rows):raise ValueError('New shared stage already registered')
    rows.append(by[target])
  updates[path]=encoded(rows)
 def requirements(name):
  rows=json.loads(updates[W/name]);return {r.get('relative_path','nativeDX10/X4/romPC/'+r.get('target_arc','')):r['output_sha256'] for r in rows}
 portraits=requirements('portrait_builds.json');audio=requirements('audio_builds.json')
 for name,key,req in [('portrait_routes.json','requirements',portraits),('dialogue_variant_runtime.json','installed_requirements',portraits),('audio_runtime.json','installed_requirements',audio)]:
  path=W/name;data=json.loads(path.read_text('utf8'));data[key]=req
  if name=='portrait_routes.json':
   data['routes']=[{'original_arc':n+'.arc','private_arc':'cliche_br_'+n+'.arc','sha256':portraits['nativeDX10/X4/romPC/cliche_br_'+n+'.arc']} for n in SHARED]
  updates[path]=encoded(data)
 parents=D/'parents';parents.mkdir(exist_ok=True)
 for path,raw in updates.items():
  old=path.read_bytes();backup=parents/path.name
  if backup.exists() and backup.read_bytes()!=old:raise ValueError('Parent backup collision')
  backup.write_bytes(old)
 # All inputs and candidates have been checked before committing any pointer.
 done=[]
 try:
  for path,raw in updates.items():path.write_bytes(raw);done.append(path)
 except Exception:
  for path in reversed(done):path.write_bytes((parents/path.name).read_bytes())
  raise
 (D/'registration.json').write_bytes(encoded({'files':[{'name':p.name,'sha256':sha(b)}for p,b in updates.items()],'shared_resources':list(SHARED),'previous_manifests':'completion_audit/parents','ps1_pointers_untouched':True}))
 print({'cumulative_manifests':len(updates),'shared_resources':len(SHARED)})
if __name__=='__main__':main()
