"""Bind the reviewed four-character candidates without altering active pointers."""
from pathlib import Path
import argparse,hashlib,json
ROOT=Path(__file__).resolve().parents[2]
W=Path(__file__).resolve().parent
read=lambda p:json.loads(p.read_text('utf8'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
ap=argparse.ArgumentParser();ap.add_argument('mode',choices=['br','rn']);a=ap.parse_args()
p=read(W/f'{a.mode}_pending_v9a_components.json')
prior=read(W/f'staging_{a.mode}_v8.json')
p['output']=f"out/{p['project']}/sprite_style_unification_20261107_v9"
p['checkpoint_label']='four_character_style_checkpoint_9'
p['review_images']=[];p['candidate_freeze_bindings']={}
for name,r in p['resources'].items():
 f=ROOT/r['path'];assert sha(f)==r['after'],name
 if r['after']!=prior['resources'][name]['after']:
  frozen=f.parent/'FROZEN.json';assert frozen.is_file(),str(frozen)
  p['candidate_freeze_bindings'][name]={'path':str(frozen.relative_to(ROOT)),'sha256':sha(frozen)}
 if 'static_body_patch'in r:
  s=r['static_body_patch'];assert sha(ROOT/s['recipe'])==s['sha256']
pictures=([
 ('riko','리코 부츠 세부','riko/prepared_ground_boots_v13/normal_readback_00.png'),
 ('shibuki','시부키 더블 사이클론','shibuki_audit/double_cyclone_ultimate_pack01/before_readback.png')
]if a.mode=='br'else[
 ('rin','린 공중 베기','zero_audit/rin_extension/prepared_air_saber02/normal_readback_00.png'),
 ('nana','나나 얼티밋 공중','nana_audit/ultimate_air_repaint/packed_air_candidate_v1/readback_1.png')])
for character,label,rel in pictures:
 f=W/rel;assert f.is_file();p['review_images'].append({'character':character,'label':label,'path':str(f.relative_to(ROOT))})
dest=W/f'staging_{a.mode}_v9.json';text=json.dumps(p,ensure_ascii=False,indent=2)+'\n'
if dest.exists():assert dest.read_text('utf8')==text,'Checkpoint already bound to different data'
else:dest.write_text(text,'utf8')
print(dest)
