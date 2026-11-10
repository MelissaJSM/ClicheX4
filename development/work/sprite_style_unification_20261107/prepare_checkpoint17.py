"""Bind the reviewed Ultimate Rising asset only after a complete freeze exists."""
from pathlib import Path
import json,hashlib
W=Path(__file__).resolve().parent;ROOT=W.parents[1]
read=lambda p:json.loads(p.read_text('utf8'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
d=W/'nana_audit/rising_repaint/packed_ultimate_candidate_v1'
f=read(d/'FROZEN.json');arc=d/'PL02_U.ARC'
assert f['frozen'] and sha(arc)==f['asset_sha256']=='4132738ac872750507538cd8d150e13a510422df81cea99b502e7371b6753cd9'
for item in f['files']:assert sha(ROOT/item['path'])==item['sha256'],item['path']
plan=read(W/'staging_rn_v16.json')
assert plan['resources']['PL02_U.ARC']['after']==f['parent_asset_sha256']
plan['resources']['PL02_U.ARC'].update(path=arc.relative_to(ROOT).as_posix(),after=sha(arc))
plan['candidate_freeze_bindings']['PL02_U.ARC']={'path':(d/'FROZEN.json').relative_to(ROOT).as_posix(),'sha256':sha(d/'FROZEN.json')}
for item in plan['candidate_freeze_bindings'].values():assert sha(ROOT/item['path'])==item['sha256']
for item in plan['resources'].values():assert sha(ROOT/item['path'])==item['after']
plan['output']='out/ver_rin_nana/sprite_style_unification_20261107_v17'
plan['checkpoint_label']='four_character_style_checkpoint_17_nana_ultimate_rising'
for i in (71,73,74):
    p=W/f'root_review_checkpoint{i}.json'
    plan['root_visual_review_records'].append({'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)})
p=W/'staging_rn_v17.json';assert not p.exists();p.write_text(json.dumps(plan,ensure_ascii=False,indent=2)+'\n','utf8')
print(p)
