"""네 캐릭터의 동결 후보를 새 검토 계획에 해시로 묶는다."""
from pathlib import Path
import json,hashlib
ROOT=Path(__file__).resolve().parents[2];W=Path(__file__).resolve().parent
def read(p):return json.loads(p.read_text('utf8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
for mode in ['br','rn']:
    plan=read(W/f'staging_{mode}_v3.json')
    plan['resources']={name:{k:q[k] for k in ['path','before','after']}for name,q in plan['resources'].items()}
    plan['output']=plan['output'].replace('_v3','_v4')
    plan['checkpoint_label']='four_character_style_checkpoint_4'
    plan['review_images']=[]
    if mode=='br':
        wall=read(W/'shibuki_audit/prepared_wall_front01/proposal.json')
        for name,q in wall['files'].items():plan['resources'][name]=q
        riko=read(W/'riko/prepared_air_special_v1/proposal.json')
        plan['resources']['PL01_U.ARC'].update(path=riko['resource'],after=riko['after_sha256'],static_body_patch=riko['static_body_patch'])
        pictures=[('shibuki','Wall detail','shibuki_audit/prepared_wall_front01/base_comparison00.png'),
                  ('riko','Air and ice attack detail','riko/prepared_air_special_v1/normal_readback_00.png')]
    else:
        wall=read(W/'nana_audit/wall_repaint/packed_wall_candidate_v4/proposal.json')['files']['PL00_U.ARC']
        plan['resources']['PL00_U.ARC'].update(path=wall['path'],after=wall['after'])
        path=W/'zero_audit/rin_extension/prepared_air_continuation2_v2/PL01_U.ARC'
        assert sha(path)=='ffca3087c17c883e6383b0ff38417b003138d1614c8add8edb1b99199bf322df'
        plan['resources']['PL01_U.ARC'].update(path=str(path.relative_to(ROOT)),after=sha(path))
        pictures=[('nana','Wall foot detail','nana_audit/wall_repaint/packed_wall_candidate_v4/front_foot_57_review.png'),
                  ('rin','Air continuation detail','zero_audit/rin_extension/prepared_air_continuation2_v2/normal_readback_00.png')]
    for character,label,rel in pictures:
        p=W/rel;assert p.is_file(),p
        plan['review_images'].append(dict(character=character,label=label,path=str(p.relative_to(ROOT))))
    for q in plan['resources'].values():assert sha(ROOT/q['path'])==q['after']
    dest=W/f'staging_{mode}_v4.json';assert not dest.exists()
    dest.write_text(json.dumps(plan,indent=2)+'\n','utf8')
    print(str(dest))
