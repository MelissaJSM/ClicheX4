from pathlib import Path
import json,hashlib
W=Path(__file__).resolve().parent;ROOT=W.parents[1];D=W/'root_nana_victory/packed_victory02'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();read=lambda p:json.loads(p.read_text('utf8'))
assert sha(D/'FROZEN.json')=='06cc50e8399edd6825e96d33d8e1f57e0baaf0c34a29912b5e8be005f954977e'
f=read(D/'FROZEN.json')
for q in f['files']+read(D/'INPUT_FROZEN.json')['files']:assert sha(ROOT/q['path'])==q['sha256'],q['path']
p=read(W/'staging_rn_v31.json');assert p['resources']['PL00_U.ARC']['after']==f['parent_arc_sha256']
p['resources']['PL00_U.ARC'].update(path=(D/'PL00_U.ARC').relative_to(ROOT).as_posix(),after=f['candidate_sha256'])
p['candidate_freeze_bindings']['PL00_U.ARC']={'path':(D/'FROZEN.json').relative_to(ROOT).as_posix(),'sha256':sha(D/'FROZEN.json')}
review=W/'root_review_checkpoint129.json';p['root_visual_review_records'].append({'path':review.relative_to(ROOT).as_posix(),'sha256':sha(review)})
p['output']='out/ver_rin_nana/sprite_style_unification_20261107_v32';p['checkpoint_label']='four_character_style_checkpoint_32_nana_victory'
out=W/'staging_rn_v32.json';assert not out.exists()and not(ROOT/p['output']).exists();out.write_text(json.dumps(p,ensure_ascii=False,indent=2)+'\n','utf8');print(sha(out))
