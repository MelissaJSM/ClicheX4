from pathlib import Path
import json,hashlib
W=Path(__file__).resolve().parent;ROOT=W.parents[1];sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();read=lambda p:json.loads(p.read_text('utf8'))
p=read(W/'staging_br_v30.json');p['output']='out/ver_buki_riko/sprite_style_unification_20261107_v31';p['checkpoint_label']='four_character_style_checkpoint_31_shibuki_base_hover_vehicle_heads'
jobs=[('PL00_U.ARC',W/'root_shibuki_hover/packed_hover_candidate03','8b4cc387a59c5cc04b365bac7bc31cacfca79a02054e891e90049e2943b53397','abee2c72ab2515162e05fe05792986c4a9a312a456f2d58523d92fbbabf4b9fe'),('PL02_U.ARC',W/'shibuki_audit/prepared_vehicle_head_ultimate01','a0629d169d6b5a0d88f31faa5dc4866c7fef99245b278caedc92f523acb3f024','0ea640a9e7e944a739fdaec94b4d6601e805e30e0d0018cb7b02c6968ae4c5e1')]
for name,d,want,freeze in jobs:
 f=d/name;lock=d/'FROZEN.json';assert sha(f)==want and sha(lock)==freeze and read(lock)['frozen']
 for rel,digest in read(lock)['files'].items():assert sha(d/rel)==digest,rel
 p['resources'][name].update(path=f.relative_to(ROOT).as_posix(),after=want);p['candidate_freeze_bindings'][name]={'path':lock.relative_to(ROOT).as_posix(),'sha256':freeze}
for n in(160,161,162,163):
 f=W/f'root_review_checkpoint{n}.json';p['root_visual_review_records'].append({'path':f.relative_to(ROOT).as_posix(),'sha256':sha(f)})
dest=W/'staging_br_v31.json';assert not dest.exists();dest.write_text(json.dumps(p,ensure_ascii=False,indent=2)+'\n','utf8');print(sha(dest))
