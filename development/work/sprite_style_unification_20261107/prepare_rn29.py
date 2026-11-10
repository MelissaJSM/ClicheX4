from pathlib import Path
import json,hashlib
W=Path(__file__).resolve().parent;ROOT=W.parents[1]
D=W/'nana_audit/ultimate_ladder_repaint/packed_first7_diagnostic_v1'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();read=lambda p:json.loads(p.read_text('utf8'))
assert sha(D/'FROZEN.json')=='65caa1005d98abd370c9f0178b7bd2a9f0ec8eab3d4b13587f174bb09cbd1ea8'
f=read(D/'FROZEN.json')
print(list(f))
p=read(W/'staging_rn_v28.json')
assert p['resources']['PL02_U.ARC']['after'].startswith('493bf270')
assert sha(D/'PL02_U.ARC')=='dcaf1343747fabeab3054c59fc384c3bbd598209eccb6c5a37ac84c1d340d339'
for q in f['files']:
 assert sha(ROOT/q['path'])==q['sha256'],q['path']
p['resources']['PL02_U.ARC'].update(path=(D/'PL02_U.ARC').relative_to(ROOT).as_posix(),after=sha(D/'PL02_U.ARC'))
p['candidate_freeze_bindings']['PL02_U.ARC']={'path':(D/'FROZEN.json').relative_to(ROOT).as_posix(),'sha256':sha(D/'FROZEN.json')}
review=W/'root_review_checkpoint124.json';p['root_visual_review_records'].append({'path':review.relative_to(ROOT).as_posix(),'sha256':sha(review)})
p['output']='out/ver_rin_nana/sprite_style_unification_20261107_v29';p['checkpoint_label']='four_character_style_checkpoint_29_nana_ultimate_ladder_first7'
out=W/'staging_rn_v29.json';assert not out.exists()and not(ROOT/p['output']).exists()
out.write_text(json.dumps(p,ensure_ascii=False,indent=2)+'\n','utf8');print(sha(out))
