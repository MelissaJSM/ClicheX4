from pathlib import Path
import json,hashlib
W=Path(__file__).resolve().parent;ROOT=W.parents[1];sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();read=lambda p:json.loads(p.read_text('utf8'))
p=read(W/'staging_br_v21.json')
for arc,folder,h in [('PL00_U.ARC','prepared_standing_special_base01','62853e4abbbec91cc6b5b46be598994cc8ae4fb9cb770a5983396941dc93efb5'),('PL02_U.ARC','prepared_standing_special_ultimate01','6703feb6ff5f8ce1295110e1dafda7e7e41e9461ddb7a69a18efc18e64463a0e')]:
 D=W/'shibuki_audit'/folder;assert sha(D/'FROZEN.json')==h;f=read(D/'FROZEN.json')
 for name,digest in f['files'].items():assert sha(D/name)==digest,name
 assert p['resources'][arc]['after']==f['parent_arc_sha256']
 p['resources'][arc].update(path=(D/arc).relative_to(ROOT).as_posix(),after=f['candidate_sha256'])
 p['candidate_freeze_bindings'][arc]={'path':(D/'FROZEN.json').relative_to(ROOT).as_posix(),'sha256':h}
review=W/'root_review_checkpoint127.json';p['root_visual_review_records'].append({'path':review.relative_to(ROOT).as_posix(),'sha256':sha(review)})
p['output']='out/ver_buki_riko/sprite_style_unification_20261107_v22';p['checkpoint_label']='four_character_style_checkpoint_22_shibuki_standing_special'
out=W/'staging_br_v22.json';assert not out.exists()and not(ROOT/p['output']).exists();out.write_text(json.dumps(p,ensure_ascii=False,indent=2)+'\n','utf8');print(sha(out))
