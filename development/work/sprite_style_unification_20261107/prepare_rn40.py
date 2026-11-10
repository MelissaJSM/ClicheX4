from pathlib import Path
import json,hashlib
W=Path(__file__).resolve().parent;ROOT=W.parents[1];D=W/'nana_audit/ultimate_nova_repaint/packed_nova_candidate_v1'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();read=lambda p:json.loads(p.read_text('utf8'))
p=read(W/'staging_rn_v39.json');f=read(D/'FROZEN.json');candidate='1ec00de5164827c5dd5322b93b7060e11a1afbddd26bacb23f5b585e63715195'
assert sha(D/'FROZEN.json')=='74fe8ce48ea98f804ebf62b832b7924b8de13bcbb48eff9c55926f50911a726d'
assert f['frozen']and f['asset_sha256']==candidate and f['parent_asset_sha256']==p['resources']['PL02_U.ARC']['after']
for row in f['files']:assert sha(ROOT/row['path'])==row['sha256'],row['path']
lock=read(D/'INPUT_FROZEN.json')['files']
if isinstance(lock,dict):
 for name,digest in lock.items():assert sha(ROOT/name)==digest,name
else:
 for row in lock:assert sha(ROOT/row['path'])==row['sha256'],row['path']
p['resources']['PL02_U.ARC'].update(path=(D/'PL02_U.ARC').relative_to(ROOT).as_posix(),after=candidate)
p['candidate_freeze_bindings']['PL02_U.ARC']={'path':(D/'FROZEN.json').relative_to(ROOT).as_posix(),'sha256':sha(D/'FROZEN.json')}
q=W/'root_review_checkpoint146.json';assert sha(q)=='94d776881e3dffd87ce4114800e9dc0dbc1d64d20869dc1283f5b7e5c766f5fc';p['root_visual_review_records'].append({'path':q.relative_to(ROOT).as_posix(),'sha256':sha(q)})
p['output']='out/ver_rin_nana/sprite_style_unification_20261107_v40';p['checkpoint_label']='four_character_style_checkpoint_40_nana_ultimate_nova'
dest=W/'staging_rn_v40.json';assert not dest.exists()and not(ROOT/p['output']).exists();dest.write_text(json.dumps(p,ensure_ascii=False,indent=2)+'\n','utf8');print(sha(dest))
