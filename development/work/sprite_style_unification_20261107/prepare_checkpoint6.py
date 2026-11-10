"""네 캐릭터의 동결한 누적 후보만 별도 여섯째 검토판에 연결한다."""
from pathlib import Path
import json,hashlib
ROOT=Path(__file__).resolve().parents[2];W=Path(__file__).resolve().parent
read=lambda p:json.loads(p.read_text('utf8'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
for mode in ['br','rn']:
    plan=read(W/f'staging_{mode}_v5.json')
    plan['output']=plan['output'].replace('_v5','_v6')
    plan['checkpoint_label']='four_character_style_checkpoint_6'
    plan['review_images']=[]
    if mode=='br':
        shibuki=read(W/'shibuki_audit/prepared_arrival_victory01/proposal.json')
        for key,q in shibuki['files'].items():
            plan['resources'][key].update(path=q['path'],after=q['after'])
        zero=read(W/'riko/prepared_vehicle_clothes_v1/proposal.json')
        pictures=[('shibuki','Arrival outfit detail','shibuki_audit/arrival_targets01/base_comparison.png'),('riko','Vehicle outfit detail','riko/prepared_vehicle_clothes_v1/normal_readback_04.png')]
    else:
        nana=read(W/'nana_audit/air_repaint/packed_air_candidate_v1/proposal.json')
        for key,q in nana['files'].items():
            plan['resources'][key].update(path=q['path'],after=q['after'])
        zero=read(W/'zero_audit/rin_extension/prepared_rear_continuation2_v1/proposal.json')
        pictures=[('nana','Air outfit detail','nana_audit/air_repaint/packed_air_candidate_v1/readback_1.png'),('rin','Rear outfit detail','zero_audit/rin_extension/prepared_rear_continuation2_v1/normal_readback_00.png')]
    plan['resources']['PL01_U.ARC'].update(path=zero['resource'],after=zero['after_sha256'],static_body_patch=zero['static_body_patch'])
    for character,label,rel in pictures:
        p=W/rel;assert p.is_file(),p
        plan['review_images'].append(dict(character=character,label=label,path=str(p.relative_to(ROOT))))
    for q in plan['resources'].values():assert sha(ROOT/q['path'])==q['after']
    p=W/f'staging_{mode}_v6.json';assert not p.exists();p.write_text(json.dumps(plan,indent=2)+'\n','utf8');print(str(p))
