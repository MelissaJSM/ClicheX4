"""Riko 수용본 위에 같은 길이 X 대기 ARC만 적용하고 전체 디스크 차이를 검사한다."""
import argparse
from datetime import datetime,timezone
import json
from pathlib import Path
import shutil
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts.project import write_json,working_cue,validate_bin,inspect_references,load_project
from scripts.discover_inputs import sha256
from src.psx_disc import write_archive_copy,file_hash
from src.psx_sector import validate_checks


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--recipe',type=Path,required=True)
    args=parser.parse_args()
    recipe_path=args.recipe.resolve()
    if not recipe_path.is_relative_to((ROOT/'work/ver_buki_riko/shibuki_idle').resolve()):
        raise ValueError('Expected a Shibuki idle recipe')
    recipe=json.loads(recipe_path.read_text(encoding='utf-8'))
    if recipe['task']!='x_shibuki' or recipe['scope']!='six_frame_idle':raise ValueError('Unsupported scope')
    arc=(recipe_path.parent/'modified.arc').read_bytes()
    if sha256(arc)!=recipe['modified_arc_sha256']:raise ValueError('Changed idle ARC')
    cfg=json.loads((ROOT/'config/shibuki_x_us.json').read_text(encoding='utf-8'))
    if recipe['original_arc_sha256']!=cfg['archive']['sha256']:raise ValueError('Unsupported X ARC')
    project=load_project(ROOT,'ver_buki_riko');inspect_references(ROOT,project)
    validate_bin(ROOT/project['source_bin'],cfg['source_sha256'])
    accepted=json.loads((ROOT/'projects/ver_buki_riko/riko_accepted_build.json').read_text(encoding='utf-8'))
    parent=(ROOT/accepted['cue']).with_suffix('.bin')
    validate_bin(parent,accepted['bin_sha256'])
    out=ROOT/'out/ver_buki_riko'/('shibuki_idle_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'))
    out.mkdir(parents=True,exist_ok=False)
    target=out/'shibuki_riko.bin'
    result=write_archive_copy(parent,target,cfg['archive'],arc,accepted['bin_sha256'])
    cue=working_cue((ROOT/accepted['cue']).read_text(encoding='ascii'),'shibuki_riko.bin')
    (out/'shibuki_riko.cue').write_text(cue,encoding='ascii')
    (out/'modified.arc').write_bytes(arc)
    shutil.copyfile(recipe_path,out/'recipe.json')
    expected={r['lba'] for r in result['changed_sectors']}
    actual=[]
    with parent.open('rb') as a,target.open('rb') as b:
        for sector in range(result['size']//2352):
            before,after=a.read(2352),b.read(2352)
            if before==after:continue
            if sector not in expected or before[:24]!=after[:24]:raise ValueError('Unexpected raw sector difference')
            validate_checks(after);actual.append(sector)
            start=(sector-cfg['archive']['lba'])*2048
            if after[24:2072]!=arc[start:start+2048]:raise ValueError('Patched sector differs from ARC')
    if set(actual)!=expected:raise ValueError('Sector accounting mismatch')
    validate_bin(parent,accepted['bin_sha256'])
    validate_bin(ROOT/project['source_bin'],cfg['source_sha256'])
    inspect_references(ROOT,project)
    manifest=dict(project='ver_buki_riko',task='x_shibuki',stage='EXPANSION',kind='shibuki_base_idle_candidate',
                  parent_build=accepted['build'],parent_bin_sha256=accepted['bin_sha256'],
                  source_sha256=cfg['source_sha256'],modified_bin=result,
                  modified_archive_sha256=sha256(arc),archive=cfg['archive'],recipe=str(recipe_path.relative_to(ROOT)),
                  riko_preserved_byte_for_byte=True,only_X_archive_and_checks_changed=True,
                  full_disc_sectors_compared=result['size']//2352,runtime_verified=False,
                  user_accepted_design_basis=recipe.get('user_accepted_design_basis',False),
                  revised_design_user_review_pending=recipe.get('revised_design_user_review_pending',False),
                  new_animation_user_review_pending=True,
                  unedited_X_actions_recolored=True,armor_not_implemented=True,text_not_changed=True)
    write_json(out/'manifest.json',manifest)
    print(json.dumps({'output':str(out),'sha256':result['sha256'],'changed_sectors':actual,'full_disc_verified':True}))


if __name__=='__main__':main()
