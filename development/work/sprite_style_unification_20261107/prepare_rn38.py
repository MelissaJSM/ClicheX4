from pathlib import Path
import json,hashlib
W=Path(__file__).resolve().parent;ROOT=W.parents[1];D=W/'root_nana_selection8/prepared01'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();read=lambda p:json.loads(p.read_text('utf8'))
p=read(W/'staging_rn_v37.json');f=read(D/'FROZEN.json');candidate='55b5d04d9a3452f2f12fe5ab21024de58c61f43eaa8b078f873ce4c7d2182f52'
assert sha(D/'FROZEN.json')=='27689ca5661327d4de5f3883be0547b733096fa2c1f013168f0de9c6ac2ae5d4'
assert f['frozen']and f['candidate_sha256']==candidate and f['parent_selection_sha256']==p['resources']['ST0E_U1.ARC']['after']
for name,digest in f['files'].items():assert sha(D/name)==digest,name
for row in read(D/'INPUT_LOCK.json')['files']:assert sha(ROOT/row['path'])==row['sha256'],row['path']
reader=read(W/'zero_audit/nana_selection8_spares_independent01/READER_LOCK.json')
for key in('reader','finalizer'):
 row=reader[key];assert sha(ROOT/row['path'])==row['sha256'],row['path']
for name,digest in reader['input_hashes'].items():assert sha(ROOT/name)==digest,name
p['resources']['ST0E_U1.ARC'].update(path=(D/'ST0E_U1.ARC').relative_to(ROOT).as_posix(),after=candidate)
p['candidate_freeze_bindings']['ST0E_U1.ARC']={'path':(D/'FROZEN.json').relative_to(ROOT).as_posix(),'sha256':sha(D/'FROZEN.json')}
q=W/'root_review_checkpoint141.json';assert sha(q)=='f108472291114de909b214ef10a8a54098cdb40fbb83bf4358aa3c7cd30edca9';p['root_visual_review_records'].append({'path':q.relative_to(ROOT).as_posix(),'sha256':sha(q)})
q=W/'selection_standing_v5_checks.json';p['selection_standing_scope_checks']={'path':q.relative_to(ROOT).as_posix(),'sha256':sha(q)}
p['sync_x_selection_standing']=True;p['preserve_x_selection']=False;p['build_entrypoint']='scripts/build_sprite_style_selection_v5.py';p['output']='out/ver_rin_nana/sprite_style_unification_20261107_v38';p['checkpoint_label']='four_character_style_checkpoint_38_nana_selection_standing'
dest=W/'staging_rn_v38.json';assert not dest.exists()and not(ROOT/p['output']).exists();dest.write_text(json.dumps(p,ensure_ascii=False,indent=2)+'\n','utf8');print(sha(dest))
