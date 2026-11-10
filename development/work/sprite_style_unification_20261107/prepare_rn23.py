from pathlib import Path
import json,hashlib
W=Path(__file__).resolve().parent;ROOT=W.parents[1]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();read=lambda p:json.loads(p.read_text('utf8'))
plan=read(W/'staging_rn_v22.json');D=W/'nana_audit/ultimate_victory_repaint/packed_victory_candidate_v1';f=read(D/'FROZEN.json')
assert sha(D/'FROZEN.json')=='3e6ebf052656b00c2404d428a2b9f63a4a7bd5575712d9aecffd9ca75fb00901'
for q in f['files']:assert sha(ROOT/q['path'])==q['sha256'],q['path']
for q in read(D/'INPUT_FROZEN.json')['files']:assert sha(ROOT/q['path'])==q['sha256'],q['path']
assert plan['resources']['PL02_U.ARC']['after']==f['parent_asset_sha256']
plan['resources']['PL02_U.ARC'].update(path=(D/'PL02_U.ARC').relative_to(ROOT).as_posix(),after=f['asset_sha256'])
plan['candidate_freeze_bindings']['PL02_U.ARC']={'path':(D/'FROZEN.json').relative_to(ROOT).as_posix(),'sha256':sha(D/'FROZEN.json')}
p=W/'root_review_checkpoint112.json';plan['root_visual_review_records'].append({'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)})
plan['output']='out/ver_rin_nana/sprite_style_unification_20261107_v23';assert not (ROOT/plan['output']).exists()
plan['checkpoint_label']='four_character_style_checkpoint_23_nana_ultimate_victory'
p=W/'staging_rn_v23.json';assert not p.exists();p.write_text(json.dumps(plan,ensure_ascii=False,indent=2)+'\n','utf8');print(sha(p))
