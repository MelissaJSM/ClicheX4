from pathlib import Path
import json,hashlib
W=Path(__file__).resolve().parent;ROOT=W.parents[1];D=W/'shibuki_audit/prepared_selection_standing01'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();read=lambda p:json.loads(p.read_text('utf8'))
p=read(W/'staging_br_v23.json');f=read(D/'FROZEN.json');candidate='47e5bd6463219b77380ae39104f89ab1073c10a1313fb9828b61229e4cb73cc5'
assert f['frozen']and f.get('candidate_sha256',f.get('asset_sha256'))==candidate
assert f.get('parent_arc_sha256',f.get('parent_asset_sha256',f.get('parent_selection_sha256')))==p['resources']['ST0E_U1.ARC']['after']
rows=f['files']
if isinstance(rows,dict):
 for name,digest in rows.items():assert sha(D/name)==digest,name
else:
 for r in rows:assert sha(ROOT/r['path'])==r['sha256'],r['path']
assert sha(D/'ST0E_U1.ARC')==candidate
p['resources']['ST0E_U1.ARC'].update(path=(D/'ST0E_U1.ARC').relative_to(ROOT).as_posix(),after=candidate)
p['candidate_freeze_bindings']['ST0E_U1.ARC']={'path':(D/'FROZEN.json').relative_to(ROOT).as_posix(),'sha256':sha(D/'FROZEN.json')}
q=W/'root_review_checkpoint139.json';assert sha(q)=='33d7c93a4a2b6bb7acfbd6c3d511c918fe3a39ae5252a5468de668ab7ac1c128';p['root_visual_review_records'].append({'path':q.relative_to(ROOT).as_posix(),'sha256':sha(q)})
check=W/'selection_standing_v4_checks.json';r=read(check);assert r['passed']and r['builder_sha256']==sha(ROOT/'scripts/build_sprite_style_selection_v4.py')
p['selection_standing_scope_checks']={'path':check.relative_to(ROOT).as_posix(),'sha256':sha(check)}
p['sync_x_selection_standing']=True;p['preserve_x_selection']=False;p['build_entrypoint']='scripts/build_sprite_style_selection_v4.py';p['output']='out/ver_buki_riko/sprite_style_unification_20261107_v24';p['checkpoint_label']='four_character_style_checkpoint_24_shibuki_selection_standing'
dest=W/'staging_br_v24.json';assert not dest.exists()and not(ROOT/p['output']).exists();dest.write_text(json.dumps(p,ensure_ascii=False,indent=2)+'\n','utf8');print(sha(dest))
