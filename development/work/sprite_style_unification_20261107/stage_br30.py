from pathlib import Path
import json,hashlib
W=Path(__file__).resolve().parent;ROOT=W.parents[1]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();read=lambda p:json.loads(p.read_text('utf8'))
p=read(W/'staging_br_v29.json');p['output']='out/ver_buki_riko/sprite_style_unification_20261107_v30';p['checkpoint_label']='four_character_style_checkpoint_30_shibuki_ultimate_hover'
d=W/'shibuki_audit/prepared_hover_ultimate01';f=d/'PL02_U.ARC';lock=d/'FROZEN.json';want='3f16886331dd693e841450cbaebc8c2c3ad226681cfb26478463481ce05048ba';freeze='f8e76d86955e35ec731947d2a589604bdbc32b96d81c566c8f6f954ea4fe97fe'
assert sha(f)==want and sha(lock)==freeze
p['resources']['PL02_U.ARC'].update(path=f.relative_to(ROOT).as_posix(),after=want);p['candidate_freeze_bindings']['PL02_U.ARC']={'path':lock.relative_to(ROOT).as_posix(),'sha256':freeze}
f=W/'root_review_checkpoint159.json';p['root_visual_review_records'].append({'path':f.relative_to(ROOT).as_posix(),'sha256':sha(f)})
out=W/'staging_br_v30.json';assert not out.exists();out.write_text(json.dumps(p,ensure_ascii=False,indent=2)+'\n','utf8');print(sha(out))
