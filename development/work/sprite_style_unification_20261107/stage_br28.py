from pathlib import Path
import json,hashlib
W=Path(__file__).resolve().parent;ROOT=W.parents[1];H=W/'shibuki_audit'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text('utf8'))
p=read(W/'staging_br_v27.json');p['output']='out/ver_buki_riko/sprite_style_unification_20261107_v28';p['checkpoint_label']='four_character_style_checkpoint_28_shibuki_nova_preparation'
for name,folder,want,freeze in [('PL00_U.ARC','prepared_nova_base01','619032d0b81ffc50e5f5664ff1e3d0c077f226a7d5a8ccfac081be6a2126c6c5','046ea0722f5469cb8317cb096eaad18d0e40b43f6dde0c6d77a678ad26d2d24f'),('PL02_U.ARC','prepared_nova_ultimate01','687fb27b10b9a7c13dd6d0c9fd6976dbb04f88f9b3b775f3d33482ebb7efb86f','bfc4e2c280e56ed25d9f25b4b5f3549ef623dfbd6d41ca5244f8c66d6c480135')]:
 d=H/folder;f=d/name;lock=d/'FROZEN.json';assert sha(f)==want and sha(lock)==freeze
 p['resources'][name].update(path=f.relative_to(ROOT).as_posix(),after=want);p['candidate_freeze_bindings'][name]={'path':lock.relative_to(ROOT).as_posix(),'sha256':freeze}
for n in(147,149,150):
 f=W/f'root_review_checkpoint{n}.json';p['root_visual_review_records'].append({'path':f.relative_to(ROOT).as_posix(),'sha256':sha(f)})
out=W/'staging_br_v28.json';assert not out.exists();out.write_text(json.dumps(p,ensure_ascii=False,indent=2)+'\n','utf8');print(sha(out))
