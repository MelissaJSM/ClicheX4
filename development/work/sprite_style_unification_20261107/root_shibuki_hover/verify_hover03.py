from pathlib import Path
import json,sys
D=Path(__file__).resolve().parent;sys.path.insert(0,str(D))
from pack_hover03 import build,validate,sha,need,LOCK,LOCK_SHA,ROOT,H
candidate=D/'packed_hover_candidate03/PL00_U.ARC';expected='8b4cc387a59c5cc04b365bac7bc31cacfca79a02054e891e90049e2943b53397'
need(sha(candidate.read_bytes())==expected,'Candidate hash');parent=(H/'prepared_vehicle_head_base01/PL00_U.ARC').read_bytes();repros=[]
for i in range(2):
 result,r=build(parent);need(result==candidate.read_bytes(),'Reproduction mismatch');repros.append(sha(result));print(json.dumps({'reproduction':i+2,'sha256':sha(result)}),flush=True)
rejected=[]
def refuse(name,data,reader):
 try:validate(data,reader)
 except(ValueError,OSError,json.JSONDecodeError)as e:rejected.append({'case':name,'reason':str(e)});return
 raise ValueError('Invalid input accepted: '+name)
normal=lambda p:p.read_bytes()
refuse('truncated_parent',parent[:-1],normal);bad=bytearray(parent);bad[100]^=1;refuse('wrong_parent',bytes(bad),normal)
paths=[LOCK,D/'body_layers_probe04/layer0_221.png',D/'shot_composed02/layer7_224.png',D/'shot_composed02/layer0_228.png',D/'sharing_optimized03/229.raw',D/'sharing_optimized03/229.json',H/'hover_existing_tileorder01/049_trial_raw.bin',D/'packed_hover_shared_optimized02/input_lock.json']
for p in paths:
 def reader(q,p=p):
  b=normal(q);return bytes([b[0]^1])+b[1:]if q.resolve()==p.resolve()else b
 refuse('changed_'+p.name,parent,reader)
report={'passed':True,'candidate_sha256':expected,'input_lock_sha256':LOCK_SHA,'total_identical_builds':3,'reproductions':repros,'rejected':rejected,'readers_only_no_disk_mutation':True,'input_files':len(json.loads(LOCK.read_text('utf8'))['files']),'runtime_verified':False}
p=D/'packed_hover_candidate03/reproduction_checks.json';need(not p.exists(),'Fresh report');p.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps({'passed':True,'rejected':len(rejected)}))
