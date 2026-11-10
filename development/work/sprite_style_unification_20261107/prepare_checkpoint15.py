"""Bind Rin's reviewed burst revision to the inherited v14 test plan."""
from pathlib import Path
import json, hashlib
W=Path(__file__).resolve().parent; ROOT=W.parents[1]
read=lambda p:json.loads(p.read_text('utf8'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
d=W/'zero_audit/rin_extension/prepared_burst_remaining02'
f=read(d/'FROZEN.json'); arc=d/'PL01_U.ARC'
assert sha(arc)==f['candidate_sha256']=='1dde3e8793628d5f38b4318543e8d9f3a22b37ad350622a96f4f4f63e92610b9'
for name,key in [('proposal.json','proposal_sha256'),('static_effects.json','static_recipe_sha256')]: assert sha(d/name)==f[key]
for pathkey, hashkey in [('root_review','root_review_sha256'),('independent_report','independent_report_sha256')]: assert sha(ROOT/f[pathkey])==f[hashkey]
plan=read(W/'staging_rn_v14.json')
row=plan['resources']['PL01_U.ARC']; row['path']=arc.relative_to(ROOT).as_posix(); row['after']=sha(arc)
recipe=d/'static_effects.json'; row['static_body_patch']={'recipe':recipe.relative_to(ROOT).as_posix(),'sha256':sha(recipe)}
plan['candidate_freeze_bindings']['PL01_U.ARC']={'path':(d/'FROZEN.json').relative_to(ROOT).as_posix(),'sha256':sha(d/'FROZEN.json')}
for item in plan['candidate_freeze_bindings'].values(): assert sha(ROOT/item['path'])==item['sha256']
for item in plan['resources'].values(): assert sha(ROOT/item['path'])==item['after']
plan['output']='out/ver_rin_nana/sprite_style_unification_20261107_v15'
plan['checkpoint_label']='four_character_style_checkpoint_15_rin_burst'
for i in (51,52):
    p=W/f'root_review_checkpoint{i}.json'
    plan['root_visual_review_records'].append({'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)})
dest=W/'staging_rn_v15.json'; body=json.dumps(plan,ensure_ascii=False,indent=2)+'\n'
if dest.exists(): assert dest.read_text('utf8')==body
else: dest.write_text(body,'utf8')
print(dest)
