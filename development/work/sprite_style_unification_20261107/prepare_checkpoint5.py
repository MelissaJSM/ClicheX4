"""완료한 네 캐릭터 누적 후보를 별도 검토판으로 묶는다. 진행 중 원화는 제외."""
from pathlib import Path
import json,hashlib
ROOT=Path(__file__).resolve().parents[2];W=Path(__file__).resolve().parent
read=lambda p:json.loads(p.read_text('utf8'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
for mode in ['br','rn']:
    plan=read(W/f'staging_{mode}_v4.json')
    plan['output']=plan['output'].replace('_v4','_v5')
    plan['checkpoint_label']='four_character_style_checkpoint_5'
    plan['review_images']=[]
    if mode=='br':
        shibuki=read(W/'shibuki_audit/prepared_victory_ladder01/proposal.json')
        plan['resources'].update(shibuki['files'])
        zero=read(W/'riko/prepared_jump_clothes_v1/proposal.json')
        pictures=[('shibuki','Victory outfit detail','shibuki_audit/victory_native_page02/base_comparison.png'),('riko','Jump outfit detail','riko/prepared_jump_clothes_v1/normal_readback_01.png')]
    else:
        zero=read(W/'zero_audit/rin_extension/prepared_third_saber_v1/proposal.json')
        pictures=[('nana','Wall outfit detail - air set still in progress','nana_audit/wall_repaint/packed_wall_candidate_v4/front_foot_57_review.png'),('rin','Third saber outfit detail','zero_audit/rin_extension/prepared_third_saber_v1/normal_readback_00.png')]
    plan['resources']['PL01_U.ARC'].update(path=zero['resource'],after=zero['after_sha256'],static_body_patch=zero['static_body_patch'])
    for character,label,rel in pictures:
        p=W/rel;assert p.is_file(),p
        plan['review_images'].append(dict(character=character,label=label,path=str(p.relative_to(ROOT))))
    for q in plan['resources'].values():assert sha(ROOT/q['path'])==q['after']
    p=W/f'staging_{mode}_v5.json';assert not p.exists();p.write_text(json.dumps(plan,indent=2)+'\n','utf8');print(str(p))
