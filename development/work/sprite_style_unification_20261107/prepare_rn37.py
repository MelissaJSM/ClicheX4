from pathlib import Path
import json,hashlib
W=Path(__file__).resolve().parent;ROOT=W.parents[1];D=W/'root_nana_shot87/packed_settle01';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();read=lambda p:json.loads(p.read_text('utf8'))
p=read(W/'staging_rn_v36.json');fp=D/'FROZEN.json';assert sha(fp)=='9171104f147f3fccfe611f3b26080990089acfbfee8a04ea0c7442ebb682768c';f=read(fp)
for row in f['files']+read(D/'INPUT_FROZEN.json')['files']:assert sha(ROOT/row['path'])==row['sha256'],row['path']
assert p['resources']['PL00_U.ARC']['after']==f['parent_arc_sha256'];assert sha(D/'PL00_U.ARC')==f['candidate_sha256']
p['resources']['PL00_U.ARC'].update(path=(D/'PL00_U.ARC').relative_to(ROOT).as_posix(),after=f['candidate_sha256']);p['candidate_freeze_bindings']['PL00_U.ARC']={'path':fp.relative_to(ROOT).as_posix(),'sha256':sha(fp)}
q=W/'root_review_checkpoint138.json';p['root_visual_review_records'].append({'path':q.relative_to(ROOT).as_posix(),'sha256':sha(q)})
p['output']='out/ver_rin_nana/sprite_style_unification_20261107_v37';p['checkpoint_label']='four_character_style_checkpoint_37_nana_shot_recovery'
dest=W/'staging_rn_v37.json';assert not dest.exists()and not(ROOT/p['output']).exists();dest.write_text(json.dumps(p,ensure_ascii=False,indent=2)+'\n','utf8');print(sha(dest))
