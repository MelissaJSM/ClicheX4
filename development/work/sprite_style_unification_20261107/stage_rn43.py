from pathlib import Path
import json,hashlib
W=Path(__file__).resolve().parent;ROOT=W.parents[1]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();read=lambda p:json.loads(p.read_text('utf8'))
p=read(W/'staging_rn_v42.json');p['output']='out/ver_rin_nana/sprite_style_unification_20261107_v43';p['checkpoint_label']='four_character_style_checkpoint_43_nana_arrival_flash'
d=W/'nana_audit/base_flash140_restore01/packed_flash_candidate_v1';f=d/'PL00_U.ARC';lock=d/'FROZEN.json';want='2822a9387a69119e6a3f6ba0f3cc830676280309b139494221940e0e9a005c59';freeze='b057d4694609466a50483c58d049867987ac46d5c842ae080c8bced334511904'
assert sha(f)==want and sha(lock)==freeze
p['resources']['PL00_U.ARC'].update(path=f.relative_to(ROOT).as_posix(),after=want);p['candidate_freeze_bindings']['PL00_U.ARC']={'path':lock.relative_to(ROOT).as_posix(),'sha256':freeze}
f=W/'root_review_checkpoint157.json';p['root_visual_review_records'].append({'path':f.relative_to(ROOT).as_posix(),'sha256':sha(f)})
out=W/'staging_rn_v43.json';assert not out.exists();out.write_text(json.dumps(p,ensure_ascii=False,indent=2)+'\n','utf8');print(sha(out))
