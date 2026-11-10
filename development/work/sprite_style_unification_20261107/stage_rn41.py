from pathlib import Path
import json,hashlib
W=Path(__file__).resolve().parent;ROOT=W.parents[1];D=W/'root_nana_hover/packed_hover_final01';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
p=json.loads((W/'staging_rn_v40.json').read_text('utf8'));asset=D/'PL00_U.ARC';freeze=D/'FROZEN.json'
assert sha(asset)=='9c1ff453a2308ddc40f39e5790de0aa6a5cf41dda43165b0fa16808f8c3a643c'and sha(freeze)=='6bef565ff4b04672679ad82e22fd4f54f1c71daa1aaffb99b2544e1a99e9db29'
p['output']='out/ver_rin_nana/sprite_style_unification_20261107_v41';p['checkpoint_label']='four_character_style_checkpoint_41_nana_base_fourth_hover'
p['resources']['PL00_U.ARC'].update(path=asset.relative_to(ROOT).as_posix(),after=sha(asset));p['candidate_freeze_bindings']['PL00_U.ARC']={'path':freeze.relative_to(ROOT).as_posix(),'sha256':sha(freeze)}
review=W/'root_review_checkpoint151.json';p['root_visual_review_records'].append({'path':review.relative_to(ROOT).as_posix(),'sha256':sha(review)})
out=W/'staging_rn_v41.json';assert not out.exists();out.write_text(json.dumps(p,ensure_ascii=False,indent=2)+'\n','utf8');print(sha(out))
