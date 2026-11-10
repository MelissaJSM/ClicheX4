from pathlib import Path
import json,hashlib
W=Path(__file__).resolve().parent;ROOT=W.parents[1];sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();read=lambda p:json.loads(p.read_text('utf8'))
p=read(W/'staging_rn_v35.json')
specs=[('PL00_U.ARC','root_nana_shot85/packed_shot01','799516a55a5e83630ae59bd42247213c1d4f2750baf61bed81408506efcf39c6'),('PL02_U.ARC','nana_audit/ultimate_vehicle_repaint/packed_vehicle_candidate_v1','82291058516eecb095ec31d164a066aa8eb1ccc22c242a51a90db2424dba19ba')]
for name,folder,freeze_hash in specs:
 d=W/folder;fp=d/'FROZEN.json';assert sha(fp)==freeze_hash;f=read(fp)
 for row in f['files']+(read(d/'INPUT_FROZEN.json')['files']if(d/'INPUT_FROZEN.json').exists()else[]):assert sha(ROOT/row['path'])==row['sha256'],row['path']
 before=f.get('parent_arc_sha256',f.get('parent_asset_sha256'));after=f.get('candidate_sha256',f.get('asset_sha256'))
 assert before and after and p['resources'][name]['after']==before;assert sha(d/name)==after
 p['resources'][name].update(path=(d/name).relative_to(ROOT).as_posix(),after=after)
 p['candidate_freeze_bindings'][name]={'path':fp.relative_to(ROOT).as_posix(),'sha256':sha(fp)}
for n in (136,137):
 q=W/f'root_review_checkpoint{n}.json';p['root_visual_review_records'].append({'path':q.relative_to(ROOT).as_posix(),'sha256':sha(q)})
p['output']='out/ver_rin_nana/sprite_style_unification_20261107_v36';p['checkpoint_label']='four_character_style_checkpoint_36_nana_basic_shots_ultimate_vehicle'
dest=W/'staging_rn_v36.json';assert not dest.exists()and not(ROOT/p['output']).exists();dest.write_text(json.dumps(p,ensure_ascii=False,indent=2)+'\n','utf8');print(sha(dest))
