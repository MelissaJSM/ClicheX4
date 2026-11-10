from pathlib import Path
import json,hashlib
W=Path(__file__).resolve().parent;ROOT=W.parents[1];D=W/'nana_audit/ultimate_recoil_repaint/packed_recoil_candidate_v1'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();read=lambda p:json.loads(p.read_text('utf8'))
assert sha(D/'FROZEN.json')=='389f8be8e90e71a45c3259c81a1ca7b1cdb65e1dc362a74d5547a000b4e19f94'
f=read(D/'FROZEN.json')
for q in f['files']+read(D/'INPUT_FROZEN.json')['files']:assert sha(ROOT/q['path'])==q['sha256'],q['path']
p=read(W/'staging_rn_v32.json');assert p['resources']['PL02_U.ARC']['after']==f['parent_asset_sha256']
p['resources']['PL02_U.ARC'].update(path=(D/'PL02_U.ARC').relative_to(ROOT).as_posix(),after=f['asset_sha256'])
p['candidate_freeze_bindings']['PL02_U.ARC']={'path':(D/'FROZEN.json').relative_to(ROOT).as_posix(),'sha256':sha(D/'FROZEN.json')}
review=W/'root_review_checkpoint130.json';p['root_visual_review_records'].append({'path':review.relative_to(ROOT).as_posix(),'sha256':sha(review)})
p['output']='out/ver_rin_nana/sprite_style_unification_20261107_v33';p['checkpoint_label']='four_character_style_checkpoint_33_nana_ultimate_recoil'
out=W/'staging_rn_v33.json';assert not out.exists()and not(ROOT/p['output']).exists();out.write_text(json.dumps(p,ensure_ascii=False,indent=2)+'\n','utf8');print(sha(out))
