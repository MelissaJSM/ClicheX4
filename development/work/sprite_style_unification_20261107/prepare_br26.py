from pathlib import Path
import json,hashlib
W=Path(__file__).resolve().parent;ROOT=W.parents[1];D=W/'shibuki_audit/prepared_chaser_base01'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();read=lambda p:json.loads(p.read_text('utf8'))
p=read(W/'staging_br_v25.json');f=read(D/'FROZEN.json');candidate='3e11b7e6f6c58e6e175ba8a53278a8329440c160096bf89abdb9df334c3ef52d'
assert sha(D/'FROZEN.json')=='65440801f58ad0bc5c129db18f561688e399ee78a3cf263aaa6e0a2bb2ad3cb5'
assert f['frozen']and f['candidate_sha256']==candidate and f['parent_arc_sha256']==p['resources']['PL00_U.ARC']['after']
for name,digest in f['files'].items():assert sha(D/name)==digest,name
for name,digest in read(D/'INPUT_LOCK.json')['files'].items():assert sha(ROOT/name)==digest,name
p['resources']['PL00_U.ARC'].update(path=(D/'PL00_U.ARC').relative_to(ROOT).as_posix(),after=candidate)
p['candidate_freeze_bindings']['PL00_U.ARC']={'path':(D/'FROZEN.json').relative_to(ROOT).as_posix(),'sha256':sha(D/'FROZEN.json')}
q=W/'root_review_checkpoint144.json';assert sha(q)=='6cb7f35111068ff48113e21187c9f6b92cb88caa11368ccd80fc06307c5fce17';p['root_visual_review_records'].append({'path':q.relative_to(ROOT).as_posix(),'sha256':sha(q)})
p['output']='out/ver_buki_riko/sprite_style_unification_20261107_v26';p['checkpoint_label']='four_character_style_checkpoint_26_shibuki_basic_fourth_chaser'
dest=W/'staging_br_v26.json';assert not dest.exists()and not(ROOT/p['output']).exists();dest.write_text(json.dumps(p,ensure_ascii=False,indent=2)+'\n','utf8');print(sha(dest))
