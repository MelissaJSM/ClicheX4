"""Bind Nana hurt13 only after final frozen art and validation evidence exist."""
from pathlib import Path
import json,hashlib
W=Path(__file__).resolve().parent;ROOT=W.parents[1]
read=lambda p:json.loads(p.read_text('utf8'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
D=W/'nana_audit/hurt_repaint/packed_hurt_candidate_v1';arc=D/'PL00_U.ARC';f=read(D/'FROZEN.json')
assert f['frozen'] and sha(arc)==f['asset_sha256']=='978a9fc18e31f221d20568d747078f098f37fb120c303c64afc916442721be9f'
for item in f['files']:assert sha(ROOT/item['path'])==item['sha256'],item['path']
plan=read(W/'staging_rn_v17.json')
assert plan['resources']['PL00_U.ARC']['after']==f['parent_asset_sha256']=='3bd156730cb932f2a97b43acc85f0d2209537c76cbab6d298c973438bc251b42'
plan['resources']['PL00_U.ARC'].update(path=arc.relative_to(ROOT).as_posix(),after=sha(arc))
plan['candidate_freeze_bindings']['PL00_U.ARC']={'path':(D/'FROZEN.json').relative_to(ROOT).as_posix(),'sha256':sha(D/'FROZEN.json')}
for row in plan['resources'].values():assert sha(ROOT/row['path'])==row['after']
for row in plan['candidate_freeze_bindings'].values():assert sha(ROOT/row['path'])==row['sha256']
plan['output']='out/ver_rin_nana/sprite_style_unification_20261107_v18'
plan['checkpoint_label']='four_character_style_checkpoint_18_nana_base_fourth_hurt'
for i in (77,78,81,83,84,85,86):
 p=W/f'root_review_checkpoint{i}.json';plan['root_visual_review_records'].append({'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)})
p=W/'staging_rn_v18.json';assert not p.exists();p.write_text(json.dumps(plan,ensure_ascii=False,indent=2)+'\n','utf8');print(p)
