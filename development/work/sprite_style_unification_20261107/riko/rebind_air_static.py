"""새 공중 구성표에 보존된 낙봉파 효과의 파일 바인딩을 갱신한다."""
from pathlib import Path
import json, sys, hashlib
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT))
from scripts.prepare_riko_ui import entry
SHA=lambda b:hashlib.sha256(b).hexdigest()
BASE=Path(__file__).resolve().parent

def bind_static(source_name='prepared_burst_final_v1', target_name='prepared_air_special_v1', source_sha='e871006eed3473bfe6716fc676fb0e4d638c62846de545186dd0de0f6a17e7fc', target_sha='4e751c0e13d6f68bbb02f285493fee75c263c7cc995a96615332935c358e7615'):
    source=(BASE/source_name).resolve()
    target=(BASE/target_name).resolve()
    assert source.parent==BASE and target.parent==BASE and source!=target
    old=(source/'PL01_U.ARC').read_bytes()
    new=(target/'PL01_U.ARC').read_bytes()
    assert SHA(old)==source_sha
    assert SHA(new)==target_sha
    assert entry(old,0x10206)==entry(new,0x10206)
    recipe=json.loads((source/'static_effects.json').read_text('utf8'))
    recipe['parts_sha256']=SHA(entry(new,3))
    for spec in [dict(file=recipe['palette_file'],sha256=recipe['palette_sha256']),*recipe['frames'].values()]:
        data=(source/spec['file']).read_bytes()
        assert SHA(data)==spec['sha256']
        dst=target/spec['file']
        assert not dst.exists() or dst.read_bytes()==data
        dst.write_bytes(data)
    recipe_path=target/'static_effects.json'
    recipe_path.write_text(json.dumps(recipe,indent=2)+'\n','utf8')
    proposal_path=target/'proposal.json'
    proposal=json.loads(proposal_path.read_text('utf8'))
    proposal['verification'].pop('heads_preserved_pixels_per_reference',None)
    proposal['static_recipe_parts_hash_requires_rebind']=False
    proposal['static_body_patch']={'recipe':str(recipe_path.relative_to(ROOT)),'sha256':SHA(recipe_path.read_bytes())}
    proposal_path.write_text(json.dumps(proposal,indent=2)+'\n','utf8')
    print(json.dumps(proposal['static_body_patch']))

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--followup',action='store_true');a=p.parse_args()
    if a.followup:bind_static('prepared_air_special_v1','prepared_followup_cloth_v1','4e751c0e13d6f68bbb02f285493fee75c263c7cc995a96615332935c358e7615','105a7ba315a8dc0ef09d229770c4238fd8364adba43b483a5364c83f0ba79141')
    else:bind_static()
