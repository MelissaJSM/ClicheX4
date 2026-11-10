from pathlib import Path
import json,hashlib
W=Path(__file__).resolve().parent;ROOT=W.parents[1];D=W/'nana_audit/ultimate_hover_repaint/packed_hover_candidate_v1'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();read=lambda p:json.loads(p.read_text('utf8'))
p=read(W/'staging_rn_v38.json');f=read(D/'FROZEN.json');candidate='e630d04286c1dbcbb65a5a301dd984f23cdecf13a1759dbaaf52ad8ae103efff'
assert sha(D/'FROZEN.json')=='5be06e7d16213df54b5ca4a2117f07085f5503ed410b48a171ebc854d6ac0dd3'
assert f['frozen']and f['asset_sha256']==candidate and f['parent_asset_sha256']==p['resources']['PL02_U.ARC']['after']
for row in f['files']:assert sha(ROOT/row['path'])==row['sha256'],row['path']
lock=read(D/'INPUT_FROZEN.json')['files']
if isinstance(lock,dict):
 for name,digest in lock.items():assert sha(ROOT/name)==digest,name
else:
 for row in lock:assert sha(ROOT/row['path'])==row['sha256'],row['path']
p['resources']['PL02_U.ARC'].update(path=(D/'PL02_U.ARC').relative_to(ROOT).as_posix(),after=candidate)
p['candidate_freeze_bindings']['PL02_U.ARC']={'path':(D/'FROZEN.json').relative_to(ROOT).as_posix(),'sha256':sha(D/'FROZEN.json')}
for n,digest in [(142,'fd126b2be30f208586c607b97532f31884da0cd086eb568cbef95baa8ae5895e'),(143,'a4d15e747e93211355053deb4b3d608f1a6578a262736d8614c4ee405f46caab')]:
 q=W/f'root_review_checkpoint{n}.json';assert sha(q)==digest;p['root_visual_review_records'].append({'path':q.relative_to(ROOT).as_posix(),'sha256':sha(q)})
p['output']='out/ver_rin_nana/sprite_style_unification_20261107_v39';p['checkpoint_label']='four_character_style_checkpoint_39_nana_ultimate_hover'
dest=W/'staging_rn_v39.json';assert not dest.exists()and not(ROOT/p['output']).exists();dest.write_text(json.dumps(p,ensure_ascii=False,indent=2)+'\n','utf8');print(sha(dest))
