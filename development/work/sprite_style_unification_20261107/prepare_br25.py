from pathlib import Path
import json,hashlib
W=Path(__file__).resolve().parent;ROOT=W.parents[1];D=W/'shibuki_audit/prepared_standing_fire_ultimate01'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();read=lambda p:json.loads(p.read_text('utf8'))
p=read(W/'staging_br_v24.json');f=read(D/'FROZEN.json');candidate='1f271aeaee7c65a938a6a09116bc8b2317f7f138465f563d4c6cc1f3704ee1ad'
assert sha(D/'FROZEN.json')=='02f9f858ed6b4f17169edbc37749aa3c19553f629f1052dc9a89fab8fd809f4d'
assert f['frozen']and f['candidate_sha256']==candidate and f['parent_arc_sha256']==p['resources']['PL02_U.ARC']['after']
for name,digest in f['files'].items():assert sha(D/name)==digest,name
for name,digest in read(D/'INPUT_LOCK.json')['files'].items():assert sha(ROOT/name)==digest,name
p['resources']['PL02_U.ARC'].update(path=(D/'PL02_U.ARC').relative_to(ROOT).as_posix(),after=candidate)
p['candidate_freeze_bindings']['PL02_U.ARC']={'path':(D/'FROZEN.json').relative_to(ROOT).as_posix(),'sha256':sha(D/'FROZEN.json')}
q=W/'root_review_checkpoint140.json';assert sha(q)=='cf6424be4f688506b83469395053e8283944cda25e94b1f55c9e567f6aaf250f';p['root_visual_review_records'].append({'path':q.relative_to(ROOT).as_posix(),'sha256':sha(q)})
p['output']='out/ver_buki_riko/sprite_style_unification_20261107_v25';p['checkpoint_label']='four_character_style_checkpoint_25_shibuki_ultimate_standing'
dest=W/'staging_br_v25.json';assert not dest.exists()and not(ROOT/p['output']).exists();dest.write_text(json.dumps(p,ensure_ascii=False,indent=2)+'\n','utf8');print(sha(dest))
