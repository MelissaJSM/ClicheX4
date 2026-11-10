from pathlib import Path
import json,hashlib
W=Path(__file__).resolve().parent;ROOT=W.parents[1]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();read=lambda p:json.loads(p.read_text('utf8'))
p=read(W/'staging_rn_v41.json');p['output']='out/ver_rin_nana/sprite_style_unification_20261107_v42';p['checkpoint_label']='four_character_style_checkpoint_42_nana_base_fourth_nova'
d=W/'nana_audit/base_nova_repaint/packed_nova_candidate_v1';f=d/'PL00_U.ARC';lock=d/'FROZEN.json';want='94cf560530c87ac11a03c029a9b6e98be44c06ea6d30d6c5ce66204c8a8e3cb3';freeze='5c4d4b84c531b1dc5fba89f37557048ec5245a569471bc0ea82379178cb13d5e'
assert sha(f)==want and sha(lock)==freeze
p['resources']['PL00_U.ARC'].update(path=f.relative_to(ROOT).as_posix(),after=want);p['candidate_freeze_bindings']['PL00_U.ARC']={'path':lock.relative_to(ROOT).as_posix(),'sha256':freeze}
f=W/'root_review_checkpoint156.json';p['root_visual_review_records'].append({'path':f.relative_to(ROOT).as_posix(),'sha256':sha(f)})
out=W/'staging_rn_v42.json';assert not out.exists();out.write_text(json.dumps(p,ensure_ascii=False,indent=2)+'\n','utf8');print(sha(out))
