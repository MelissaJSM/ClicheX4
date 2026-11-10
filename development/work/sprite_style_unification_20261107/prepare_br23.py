from pathlib import Path
import json,hashlib
W=Path(__file__).resolve().parent;ROOT=W.parents[1]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();read=lambda p:json.loads(p.read_text('utf8'))
p=read(W/'staging_br_v22.json');D=W/'shibuki_audit/prepared_standing_fire_base01'
fp=D/'FROZEN.json';assert sha(fp)=='fb32b06ca8b18fa7202001905a97f8a35d3b0bd247919d0af9a472aa890511e8';f=read(fp)
for name,digest in f['files'].items():assert sha(D/name)==digest,name
assert p['resources']['PL00_U.ARC']['after']==f['parent_arc_sha256']
p['resources']['PL00_U.ARC'].update(path=(D/'PL00_U.ARC').relative_to(ROOT).as_posix(),after=f['candidate_sha256'])
p['candidate_freeze_bindings']['PL00_U.ARC']={'path':fp.relative_to(ROOT).as_posix(),'sha256':sha(fp)}
review=W/'root_review_checkpoint135.json';assert sha(review)=='59bf9ea7d827f2dc8c3dd7190a3744a80372fbae7836c74726890ed107ace3f8'
p['root_visual_review_records'].append({'path':review.relative_to(ROOT).as_posix(),'sha256':sha(review)})
p['output']='out/ver_buki_riko/sprite_style_unification_20261107_v23';p['checkpoint_label']='four_character_style_checkpoint_23_shibuki_basic_standing_fire'
p['build_entrypoint']='scripts/build_sprite_style_selection_v3.py'
dest=W/'staging_br_v23.json';assert not dest.exists()and not(ROOT/p['output']).exists();dest.write_text(json.dumps(p,ensure_ascii=False,indent=2)+'\n','utf8');print(sha(dest))
