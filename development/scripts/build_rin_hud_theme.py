"""검증된 린 심볼/개인 메뉴 색상을 기존 미국판 시험 BIN에 누적한다."""
import argparse,json,shutil,sys
from datetime import datetime,timezone
from pathlib import Path
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.prepare_rin_hud_theme import PARENT,PARENT_SHA,ART,sources,patch,make_overlay,require
from scripts.project import digest
from scripts.discover_inputs import DiscReader,sha256
from src.psx_disc import write_archive_copies
from src.psx_sector import validate_checks

def candidate(art):
    art=art.resolve();require(art.is_relative_to(ART) and art!=ART,'Unexpected candidate directory')
    m,rec,old,pal=sources();r=json.loads((art/'recipe.json').read_text('utf8'))
    require(r['kind']=='rin_hud_theme' and r['parent_sha256']==PARENT_SHA and r['source']==rec,'Candidate parent differs')
    require(r['inputs']=={f:digest(ART/f) for f in ('generated.png','prompt.txt')},'Art or prompt differs')
    require(r['reference_sha256']==digest(ROOT/'character/ver_rin_nana/rin(zero)_mark.webp'),'Reference differs')
    expected,info=make_overlay(old,pal);actual=np.array(Image.open(art/'overlay.png'))
    require(np.array_equal(actual,expected) and info==r['art'] and digest(art/'overlay.png')==r['overlay_sha256'],'Native overlay differs from art')
    require((art/'native_hud_palette.bin').read_bytes()==pal and sha256(pal)==r['palette_sha256'],'HUD palette differs')
    new,v=patch(old,actual);prepared=(art/'PL01_U.ARC').read_bytes()
    require(new==prepared and sha256(new)==r['modified_archive_sha256'] and v==r['verification'],'Candidate does not reproduce')
    return m,rec,old,new,v

def build(art):
    m,rec,old,new,v=candidate(art)
    # The user saved during their test. Preserve that current card and its backup,
    # while retaining every immutable parent input binding.
    protection=json.loads((ROOT/'work/ver_rin_nana/checkpoints/before_hud_theme_20261029/preservation.json').read_text('utf8'))
    parent_protection=json.loads((PARENT/'preservation.json').read_text('utf8'))
    current={q['path']:q['expected_sha256'] for q in protection['files']}
    updates={q['path']:q for q in protection.get('current_session_card_updates',[])}
    for q in parent_protection['files']:
        if current.get(q['path'])!=q['expected_sha256']:
            u=updates.get(q['path']);p=(ROOT/q['path']).resolve()
            require(u is not None and p.parent==ROOT/'work/ver_rin_nana/test_cards/idle_v1' and p.suffix=='.mcr','Immutable input baseline changed')
            require(u['parent_sha256']==q['expected_sha256'] and u['current_sha256']==current[q['path']] and digest(ROOT/u['backup'])==current[q['path']],'Current memory card backup differs')
    def protect():
        for q in protection['files']:require(digest(ROOT/q['path'])==q['expected_sha256'],'Protected input changed: '+q['path'])
    protect();out=ROOT/'out/ver_rin_nana'/('rin_hud_theme_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'));out.mkdir()
    result=write_archive_copies(PARENT/'rin_nana.bin',out/'rin_nana.bin',[(rec,new)],PARENT_SHA)
    (out/'modified.arc').write_bytes(new);shutil.copyfile(PARENT/'rin_nana.cue',out/'rin_nana.cue')
    for folder in ('ui','portrait','hunter','dialogue','pause','weapon_get'):shutil.copytree(PARENT/folder,out/folder)
    shutil.copytree(art,out/'hud_theme');changed={q['lba'] for q in result['changed_sectors']};count=0
    with (PARENT/'rin_nana.bin').open('rb') as f,(out/'rin_nana.bin').open('rb') as g:
        while True:
            a,b=f.read(2352),g.read(2352)
            if not a:
                require(not b,'Output grew');break
            require(len(a)==len(b) and (a!=b)==(count in changed),'Unexpected sector difference')
            if count in changed:validate_checks(b)
            count+=1
    with (out/'rin_nana.bin').open('rb') as f:
        d=DiscReader(f,result['size']);require(d.read(rec['lba'],rec['size'])==new,'Player readback differs')
    protect();v.update(all_disc_sectors_compared=count,changed_sectors=len(changed),edc_ecc_checked=True,
        other_parent_sectors_exact=True,protected_files=len(protection['files']),readback_equal=True,
        embedded_static_bodies=m['verification']['embedded_static_bodies'])
    manifest={**m,'kind':'rin_hud_theme','parent':PARENT.relative_to(ROOT).as_posix(),'parent_sha256':PARENT_SHA,
        'modified_bin':result,'modified_archive_sha256':sha256(new),'verification':v,'inherited_verification':m['verification'],
        'hud_theme_overlay':{'recipe':(out/'hud_theme/recipe.json').relative_to(ROOT).as_posix(),'recipe_sha256':digest(out/'hud_theme/recipe.json'),'runtime_verified':False},'runtime_verified':False}
    for name,data in [('manifest.json',manifest),('verification.json',v),('preservation.json',protection)]:
        (out/name).write_text(json.dumps(data,indent=2)+'\n','utf8')
    pointer={'project':'ver_rin_nana','task':'zero_rin','build':out.relative_to(ROOT).as_posix(),'cue':(out/'rin_nana.cue').relative_to(ROOT).as_posix(),
        'sha256':result['sha256'],'frames':m['cumulative_frames'],'bank1_frames':m['cumulative_bank1_frames'],'runtime_verified':False}
    (ROOT/'projects/ver_rin_nana/current_build.json').write_text(json.dumps(pointer,indent=2)+'\n','utf8')
    print(json.dumps({'output':str(out),'sha256':result['sha256'],'changed_sectors':len(changed)}))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--art',type=Path,required=True);a=p.parse_args();build(a.art)
