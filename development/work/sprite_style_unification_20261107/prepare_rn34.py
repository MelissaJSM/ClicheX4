from pathlib import Path
import json,hashlib
W=Path(__file__).resolve().parent;ROOT=W.parents[1];D=W/'root_nana_return/packed_return03'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();read=lambda p:json.loads(p.read_text('utf8'))
assert sha(D/'FROZEN.json')=='14a6c90fb20d01422199c6f7440517d840fea69ae57959659cd8cfbd4e15f7c6'
f=read(D/'FROZEN.json')
for q in f['files']+read(D/'INPUT_FROZEN.json')['files']:assert sha(ROOT/q['path'])==q['sha256'],q['path']
p=read(W/'staging_rn_v33.json');assert p['resources']['PL00_U.ARC']['after']==f['parent_arc_sha256']
p['resources']['PL00_U.ARC'].update(path=(D/'PL00_U.ARC').relative_to(ROOT).as_posix(),after=f['candidate_sha256'])
p['candidate_freeze_bindings']['PL00_U.ARC']={'path':(D/'FROZEN.json').relative_to(ROOT).as_posix(),'sha256':sha(D/'FROZEN.json')}
review=W/'root_review_checkpoint131.json';p['root_visual_review_records'].append({'path':review.relative_to(ROOT).as_posix(),'sha256':sha(review)})
p['output']='out/ver_rin_nana/sprite_style_unification_20261107_v34';p['checkpoint_label']='four_character_style_checkpoint_34_nana_return'
out=W/'staging_rn_v34.json';assert not out.exists()and not(ROOT/p['output']).exists();out.write_text(json.dumps(p,ensure_ascii=False,indent=2)+'\n','utf8');print(sha(out))
