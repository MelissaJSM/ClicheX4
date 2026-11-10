from pathlib import Path
import json,hashlib
W=Path(__file__).resolve().parent;ROOT=W.parents[1];sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();read=lambda p:json.loads(p.read_text('utf8'))
plan=read(W/'staging_rn_v23.json');D=W/'root_nana_special/packed_special02';f=read(D/'FROZEN.json');assert sha(D/'FROZEN.json')=='eb8e6240fb557124fb7a8d7c54ef775a1593795272db0022e914f502406f009b'
for q in f['files']+read(D/'INPUT_FROZEN.json')['files']:assert sha(ROOT/q['path'])==q['sha256'],q['path']
assert plan['resources']['PL00_U.ARC']['after']==f['parent_arc_sha256']
plan['resources']['PL00_U.ARC'].update(path=(D/'PL00_U.ARC').relative_to(ROOT).as_posix(),after=f['candidate_sha256'])
plan['candidate_freeze_bindings']['PL00_U.ARC']={'path':(D/'FROZEN.json').relative_to(ROOT).as_posix(),'sha256':sha(D/'FROZEN.json')}
for n in(113,114):
 p=W/f'root_review_checkpoint{n}.json';plan['root_visual_review_records'].append({'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)})
plan['output']='out/ver_rin_nana/sprite_style_unification_20261107_v24';assert not(ROOT/plan['output']).exists();plan['checkpoint_label']='four_character_style_checkpoint_24_nana_base_fourth_special'
p=W/'staging_rn_v24.json';assert not p.exists();p.write_text(json.dumps(plan,ensure_ascii=False,indent=2)+'\n','utf8');print(sha(p))
