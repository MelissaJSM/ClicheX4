from pathlib import Path
import json,hashlib
W=Path(__file__).resolve().parent;ROOT=W.parents[1];sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();read=lambda p:json.loads(p.read_text('utf8'))
plan=read(W/'staging_br_v15.json');D=W/'shibuki_audit/prepared_ultimate_ladder01';f=read(D/'FROZEN.json')
assert sha(D/'FROZEN.json')=='71cbe5c072c5e5a2bed46397880feefe1b1c01fc2e5fabf0a3af83fe4239691d'
for name,h in f['files'].items():assert sha(D/name)==h,(name,h)
assert f['parent_arc_sha256']==plan['resources']['PL02_U.ARC']['after']
plan['resources']['PL02_U.ARC'].update(path=(D/'PL02_U.ARC').relative_to(ROOT).as_posix(),after=f['candidate_sha256'])
plan['candidate_freeze_bindings']['PL02_U.ARC']={'path':(D/'FROZEN.json').relative_to(ROOT).as_posix(),'sha256':sha(D/'FROZEN.json')}
for n in (87,89,91,94,96):
 p=W/f'root_review_checkpoint{n}.json';plan['root_visual_review_records'].append({'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)})
plan['output']='out/ver_buki_riko/sprite_style_unification_20261107_v16';assert not (ROOT/plan['output']).exists()
plan['checkpoint_label']='four_character_style_checkpoint_16_shibuki_ultimate_ladder'
out=W/'staging_br_v16.json';assert not out.exists();out.write_text(json.dumps(plan,ensure_ascii=False,indent=2)+'\n','utf8');print(out.name,sha(out))
