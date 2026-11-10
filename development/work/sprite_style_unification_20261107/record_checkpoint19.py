import hashlib,json
from datetime import datetime,timezone
from pathlib import Path
W=Path('work/sprite_style_unification_20261107')
paths=[
 'nana_audit/ultimate_air_repaint/firing_joint_probe_v3/comparison_1.png',
 'nana_audit/ultimate_air_repaint/firing_joint_probe_v3/comparison_3.png',
 'shibuki_audit/double_cyclone_native02/ultimate_before_comparison.png',
 'shibuki_audit/double_cyclone_native02/ultimate_after_comparison.png',
 'zero_audit/rin_extension/air_saber_registered_v1/normal_comparison.png',
 'nana_audit/ultimate_air_repaint/firing_reach_pair_probe_v2/comparison.png',
 'shibuki_audit/double_cyclone_base_pack02/base_readback.png',
 'shibuki_audit/double_cyclone_base_pack02/fourth_readback.png',
 'shibuki_audit/double_cyclone_contact02/initial_effect_overlay.png',
 'shibuki_audit/double_cyclone_ultimate_pack01/before_readback.png',
 'shibuki_audit/double_cyclone_ultimate_pack01/after_readback.png',
 *['zero_audit/rin_extension/prepared_air_saber01/'+name+'_readback_'+n+'.png' for name in ('normal','black') for n in ('00','01')]
]
report={'utc':datetime.now(timezone.utc).isoformat(),'art_review_images':[{'path':(W/p).as_posix(),'sha256':hashlib.sha256((W/p).read_bytes()).hexdigest(),'root_actually_viewed':True}for p in paths],
 'findings':{'nana':'v3 50/52/54 short-arm/chest-dark-bar rejected; new reach pair v2 visually accepted for technical integration.',
 'shibuki':'Base/Fourth and Ultimate before/after packed 98/99 reviewed; garment detail, native soles and hand/effect alignment accepted for offline candidate, not gameplay or user acceptance.',
 'rin':'Packed five references (four new paintings and one exact alias) in normal/red actually viewed; resolves prepared_air_saber01 root art review pending via external evidence without changing frozen files.'},
 'all_characters_complete':False,'user_acceptance':False}
(W/'root_review_checkpoint19.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf8')
p=json.loads((W/'staging_br_v8.json').read_text('utf8'))
for folder in ('prepared_double_cyclone_base01','prepared_double_cyclone_ultimate01'):
 q=json.loads((W/'shibuki_audit'/folder/'proposal.json').read_text('utf8'))
 p['resources'].update(q['files'])
dest=W/'br_pending_v9a_components.json'
dest.write_text(json.dumps(p,ensure_ascii=False,indent=2)+'\n','utf8')
print(json.dumps({'actual_art_images':len(paths),'native_plan':str(dest)}))
