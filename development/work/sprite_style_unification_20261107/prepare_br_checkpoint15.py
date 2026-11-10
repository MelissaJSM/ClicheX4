"""Bind Shibuki run32 after frozen native directory and preservation proofs."""
from pathlib import Path
import json,hashlib
W=Path(__file__).resolve().parent;ROOT=W.parents[1]
read=lambda p:json.loads(p.read_text('utf8'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
D=W/'shibuki_audit/prepared_base_run01';arc=D/'PL00_U.ARC';f=read(D/'FROZEN.json')
assert sha(arc)=='381d83fa2623d58a3302914196ffdd73bd8c972e27aa584380af05d819e688ce'
lock=read(D/'PREPARED_LOCK.json')
for name,digest in lock['files'].items():assert sha(D/name)==digest,name
proposal=read(D/'proposal.json');plan=read(W/'staging_br_v14.json')
assert plan['resources']['PL00_U.ARC']['after']==proposal['sequential_parent']['sha256']
proofs={
 'zero_audit/shibuki_run32_directory_native01/report.json':'11dd4c9bf5de510e9124d5b7e67e9ac42d04a256598100d4b018844152982331',
 'zero_audit/shibuki_run32_independent01/report.json':'bd446a6955df3ee80d859f82a286c859dafa6a06bbc0950f10e2b3f1ba37f3a6'}
for rel,digest in proofs.items():assert sha(W/rel)==digest and read(W/rel)['passed'],rel
if isinstance(f.get('files'),list):
 for rec in f['files']:assert sha(ROOT/rec['path'])==rec['sha256'],rec['path']
elif 'files' in f:
 for rel,digest in f['files'].items():assert sha(D/rel)==digest,rel
else:assert f['candidate_sha256']==sha(arc)
for rec in f.get('proofs',{}).values():assert sha(ROOT/rec['path'])==rec['sha256']
plan['resources']['PL00_U.ARC'].update(path=arc.relative_to(ROOT).as_posix(),after=sha(arc))
plan['candidate_freeze_bindings']['PL00_U.ARC']={'path':(D/'FROZEN.json').relative_to(ROOT).as_posix(),'sha256':sha(D/'FROZEN.json')}
for row in plan['resources'].values():assert sha(ROOT/row['path'])==row['after']
for row in plan['candidate_freeze_bindings'].values():assert sha(ROOT/row['path'])==row['sha256']
plan['output']='out/ver_buki_riko/sprite_style_unification_20261107_v15'
plan['checkpoint_label']='four_character_style_checkpoint_15_shibuki_base_run'
plan['entry2_internal_layout_proofs']=[{'path':(W/rel).relative_to(ROOT).as_posix(),'sha256':digest} for rel,digest in proofs.items()]
for i in (63,65,75):
 p=W/f'root_review_checkpoint{i}.json';plan['root_visual_review_records'].append({'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)})
p=W/'staging_br_v15.json';assert not p.exists();p.write_text(json.dumps(plan,ensure_ascii=False,indent=2)+'\n','utf8');print(p)
