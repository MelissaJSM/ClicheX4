from pathlib import Path
import json,hashlib
W=Path(__file__).resolve().parent;ROOT=W.parents[1]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();read=lambda p:json.loads(p.read_text('utf8'))
plan=read(W/'staging_rn_v20.json');D=W/'nana_audit/ultimate_ceremony_repaint/packed_arrival_candidate_v1';f=read(D/'FROZEN.json')
assert sha(D/'FROZEN.json')=='b8127aeff1dfd9eae0577d74e445251ce9187971d09673a58de55518deb75d33'
for q in f['files']:assert sha(ROOT/q['path'])==q['sha256'],q['path']
for q in read(D/'INPUT_FROZEN.json')['files']:assert sha(ROOT/q['path'])==q['sha256'],q['path']
assert plan['resources']['PL02_U.ARC']['after']==f['parent_asset_sha256']
plan['resources']['PL02_U.ARC'].update(path=(D/'PL02_U.ARC').relative_to(ROOT).as_posix(),after=f['asset_sha256'])
plan['candidate_freeze_bindings']['PL02_U.ARC']={'path':(D/'FROZEN.json').relative_to(ROOT).as_posix(),'sha256':sha(D/'FROZEN.json')}
for n in (106,107,110):
 p=W/f'root_review_checkpoint{n}.json';plan['root_visual_review_records'].append({'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)})
plan['output']='out/ver_rin_nana/sprite_style_unification_20261107_v21';assert not (ROOT/plan['output']).exists()
plan['checkpoint_label']='four_character_style_checkpoint_21_nana_ultimate_arrival'
p=W/'staging_rn_v21.json';assert not p.exists();p.write_text(json.dumps(plan,ensure_ascii=False,indent=2)+'\n','utf8');print(sha(p))
