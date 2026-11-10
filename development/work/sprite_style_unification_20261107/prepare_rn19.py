from pathlib import Path
import json,hashlib
W=Path(__file__).resolve().parent;ROOT=W.parents[1]
read=lambda p:json.loads(p.read_text('utf8'));sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
D=W/'nana_audit/ultimate_hurt_repaint/packed_hurt_candidate_v1';arc=D/'PL02_U.ARC';f=read(D/'FROZEN.json')
assert sha(D/'FROZEN.json')=='73771c951309e07a56db31b3da3f887c1374ed219c74365bf7bcaf6b3c88799a'
assert f['frozen'] and sha(arc)==f['asset_sha256']=='c9e68442829a7f149ae86317c88172e27dbce545e454687b98310fad28ef83a5'
for item in f['files']:assert sha(ROOT/item['path'])==item['sha256'],item['path']
plan=read(W/'staging_rn_v18.json');assert plan['resources']['PL02_U.ARC']['after']==f['parent_asset_sha256']=='4132738ac872750507538cd8d150e13a510422df81cea99b502e7371b6753cd9'
plan['resources']['PL02_U.ARC'].update(path=arc.relative_to(ROOT).as_posix(),after=sha(arc))
plan['candidate_freeze_bindings']['PL02_U.ARC']={'path':(D/'FROZEN.json').relative_to(ROOT).as_posix(),'sha256':sha(D/'FROZEN.json')}
for row in plan['resources'].values():assert sha(ROOT/row['path'])==row['after']
for row in plan['candidate_freeze_bindings'].values():assert sha(ROOT/row['path'])==row['sha256']
plan['output']='out/ver_rin_nana/sprite_style_unification_20261107_v19';assert not (ROOT/plan['output']).exists()
plan['checkpoint_label']='four_character_style_checkpoint_19_nana_ultimate_hurt'
for i in (88,90,95,97,99):
 p=W/f'root_review_checkpoint{i}.json';plan['root_visual_review_records'].append({'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)})
p=W/'staging_rn_v19.json';assert not p.exists();p.write_text(json.dumps(plan,ensure_ascii=False,indent=2)+'\n','utf8');print(p.name,sha(p))
