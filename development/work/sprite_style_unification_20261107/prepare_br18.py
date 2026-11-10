from pathlib import Path
import json,hashlib
W=Path(__file__).resolve().parent;ROOT=W.parents[1]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();read=lambda p:json.loads(p.read_text('utf8'))
plan=read(W/'staging_br_v17.json');D=W/'shibuki_audit/prepared_ultimate_hurt02';f=read(D/'FROZEN.json')
assert sha(D/'FROZEN.json')=='c692e33a77f03fc0c9a055605cc1aa4f2c5553fa92c4ccf2c1a42e5ba0dfd7a6'
for name,h in f['files'].items():assert sha(D/name)==h,name
assert plan['resources']['PL02_U.ARC']['after']==f['parent_arc_sha256']
plan['resources']['PL02_U.ARC'].update(path=(D/'PL02_U.ARC').relative_to(ROOT).as_posix(),after=f['candidate_sha256'])
plan['candidate_freeze_bindings']['PL02_U.ARC']={'path':(D/'FROZEN.json').relative_to(ROOT).as_posix(),'sha256':sha(D/'FROZEN.json')}
for n in (106,109):
 p=W/f'root_review_checkpoint{n}.json';plan['root_visual_review_records'].append({'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)})
plan['output']='out/ver_buki_riko/sprite_style_unification_20261107_v18';assert not (ROOT/plan['output']).exists()
plan['checkpoint_label']='four_character_style_checkpoint_18_shibuki_ultimate_hurt'
p=W/'staging_br_v18.json';assert not p.exists();p.write_text(json.dumps(plan,ensure_ascii=False,indent=2)+'\n','utf8');print(sha(p))
