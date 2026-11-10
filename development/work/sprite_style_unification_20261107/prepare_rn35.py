from pathlib import Path
import json,hashlib
W=Path(__file__).resolve().parent;ROOT=W.parents[1];sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();read=lambda p:json.loads(p.read_text('utf8'))
p=read(W/'staging_rn_v34.json')
specs=[('PL00_U.ARC','root_nana_vehicle/packed_vehicle03','948b0d88aa61aded2300e282604806ad2c222b8075de83fa3b10d5e5bccb54de'),('PL02_U.ARC','nana_audit/ultimate_special_finish_repaint/packed_special_candidate_v1','e27563d71033f55b72b6a87ee1ea79faaab6c90f725429b9cc35920a25b1190d'),('ST0E_U1.ARC','nana_selection_sync34_03','9712a521ed43fcd789853476a1032dcc4c598d1221354bf0fb7d9e225fb23fd0')]
for name,folder,freeze_hash in specs:
 d=W/folder;fp=d/'FROZEN.json';assert sha(fp)==freeze_hash;f=read(fp)
 rows=f['files']+(read(d/'INPUT_FROZEN.json')['files']if(d/'INPUT_FROZEN.json').exists()else[])
 for row in rows:assert sha(ROOT/row['path'])==row['sha256'],row['path']
 before=f.get('parent_arc_sha256',f.get('parent_asset_sha256'));after=f.get('candidate_sha256',f.get('asset_sha256'));assert p['resources'][name]['after']==before
 assert sha(d/name)==after;p['resources'][name].update(path=(d/name).relative_to(ROOT).as_posix(),after=after)
 p['candidate_freeze_bindings'][name]={'path':fp.relative_to(ROOT).as_posix(),'sha256':sha(fp)}
for n in (132,133,134):
 q=W/f'root_review_checkpoint{n}.json';p['root_visual_review_records'].append({'path':q.relative_to(ROOT).as_posix(),'sha256':sha(q)})
p['preserve_x_selection']=False;p['output']='out/ver_rin_nana/sprite_style_unification_20261107_v35';p['checkpoint_label']='four_character_style_checkpoint_35_nana_vehicle_special_selection';p['build_entrypoint']='scripts/build_sprite_style_selection_v3.py'
dest=W/'staging_rn_v35.json';assert not dest.exists()and not(ROOT/p['output']).exists();dest.write_text(json.dumps(p,ensure_ascii=False,indent=2)+'\n','utf8');print(sha(dest))
