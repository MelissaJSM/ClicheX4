from pathlib import Path
import json,hashlib
W=Path(__file__).resolve().parent;ROOT=W.parents[1]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();read=lambda p:json.loads(p.read_text('utf8'))
plan=read(W/'staging_rn_v21.json');D=W/'root_nana_lowhp/packed_lowhp01';f=read(D/'FROZEN.json')
assert f['frozen'] and f['candidate_sha256']=='ac1e35b7131d3909a93ea3466859aa9d7278c431d72defcb261b2b76cd1f6e16'
for q in f['files']:assert sha(ROOT/q['path'])==q['sha256'],q['path']
for q in read(D/'INPUT_FROZEN.json')['files']:assert sha(ROOT/q['path'])==q['sha256'],q['path']
assert plan['resources']['PL00_U.ARC']['after']==f['parent_arc_sha256']
plan['resources']['PL00_U.ARC'].update(path=(D/'PL00_U.ARC').relative_to(ROOT).as_posix(),after=f['candidate_sha256'])
plan['candidate_freeze_bindings']['PL00_U.ARC']={'path':(D/'FROZEN.json').relative_to(ROOT).as_posix(),'sha256':sha(D/'FROZEN.json')}
p=W/'root_review_checkpoint111.json';plan['root_visual_review_records'].append({'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)})
plan['output']='out/ver_rin_nana/sprite_style_unification_20261107_v22';assert not (ROOT/plan['output']).exists()
plan['checkpoint_label']='four_character_style_checkpoint_22_nana_base_fourth_lowhp'
p=W/'staging_rn_v22.json';assert not p.exists();p.write_text(json.dumps(plan,ensure_ascii=False,indent=2)+'\n','utf8');print(sha(p))
