"""Apply the Rin action illustration to its three shared screen resources."""
import argparse,json,shutil,sys
from pathlib import Path
from datetime import datetime,timezone
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.prepare_rin_weapon_get import ART,PARENT,PARENT_SHA,sources,verify
from scripts.project import digest
from scripts.discover_inputs import DiscReader,sha256
from src.psx_disc import write_archive_copies
from src.psx_sector import validate_checks

def main(art):
    art=art.resolve()
    if not art.is_relative_to(ART):raise ValueError('Unexpected weapon acquisition art path')
    records,raw=sources()
    recipe=json.loads((art/'recipe.json').read_text('utf8'))
    if recipe['parent_sha256']!=PARENT_SHA:raise ValueError('Parent/inventory binding differs')
    for key in ('art','prompt'):
        path=(ROOT/recipe[key]).resolve()
        if not path.is_relative_to(ART) or digest(path)!=recipe[key+'_sha256']:raise ValueError('Weapon acquisition art source changed')
    names=sorted(records)
    if [r['file'] for r in recipe['files']]!=names:raise ValueError('Unexpected weapon acquisition output file set')
    original={n:raw[n] for n in names};modified={};replacements=[]
    for r in recipe['files']:
        name=r['file'];source=records[name];data=(art/name).read_bytes()
        if r['source']!=source or sha256(data)!=r['sha256'] or len(data)!=source['size']:raise ValueError('Candidate/source hash or size changed')
        modified[name]=data;replacements.append((source,data))
    if digest(art/'action.png')!=recipe['action_sha256']:raise ValueError('Action indices changed')
    v=verify(original,modified,np.array(Image.open(art/'action.png')))
    m=json.loads((PARENT/'manifest.json').read_text('utf8'))
    preservation=json.loads((PARENT/'preservation.json').read_text('utf8'))
    def protect():
        for q in preservation['files']:
            if digest(ROOT/q['path'])!=q['expected_sha256']:raise ValueError('Protected input changed: '+q['path'])
    protect()
    out=ROOT/'out/ver_rin_nana'/('rin_weapon_get_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'));out.mkdir()
    result=write_archive_copies(PARENT/'rin_nana.bin',out/'rin_nana.bin',replacements,PARENT_SHA)
    for file in ('rin_nana.cue','modified.arc'):shutil.copyfile(PARENT/file,out/file)
    for folder in ('ui','portrait','hunter','dialogue','pause'):shutil.copytree(PARENT/folder,out/folder)
    shutil.copytree(art,out/'weapon_get')
    changed={q['lba'] for q in result['changed_sectors']};count=0
    with (PARENT/'rin_nana.bin').open('rb') as f,(out/'rin_nana.bin').open('rb') as g:
        while True:
            a,b=f.read(2352),g.read(2352)
            if not a:
                if b:raise ValueError('Output longer than source')
                break
            if len(a)!=len(b) or (a!=b)!=(count in changed):raise ValueError('Unexpected disc change')
            if count in changed:validate_checks(b)
            count+=1
    with (out/'rin_nana.bin').open('rb') as f:
        d=DiscReader(f,result['size'])
        for rec,data in replacements:
            if d.read(rec['lba'],rec['size'])!=data:raise ValueError('Weapon acquisition readback differs')
        player=json.loads((ROOT/'config/ps1_us_slus00561.json').read_text('utf8'))['zero_archive']
        if sha256(d.read(player['lba'],player['size']))!=m['modified_archive_sha256']:raise ValueError('Gameplay changed')
    protect();v.update(all_disc_sectors_compared=count,changed_sectors=len(changed),edc_ecc_checked=True,
        other_parent_sectors_exact=True,readback_equal=True,protected_files=len(preservation['files']),
        embedded_static_bodies=m['verification']['embedded_static_bodies'])
    manifest={**m,'kind':'rin_weapon_get','parent':PARENT.relative_to(ROOT).as_posix(),'parent_sha256':PARENT_SHA,
        'modified_bin':result,'verification':v,'inherited_verification':m['verification'],
        'weapon_get_overlay':{'recipe':(out/'weapon_get/recipe.json').relative_to(ROOT).as_posix(),
                           'recipe_sha256':digest(out/'weapon_get/recipe.json'),'runtime_verified':False},'runtime_verified':False}
    for name,data in [('manifest.json',manifest),('verification.json',v),('preservation.json',preservation)]:
        (out/name).write_text(json.dumps(data,indent=2)+'\n','utf8')
    pointer={'project':'ver_rin_nana','task':'zero_rin','build':out.relative_to(ROOT).as_posix(),
        'cue':(out/'rin_nana.cue').relative_to(ROOT).as_posix(),'sha256':result['sha256'],
        'frames':m['cumulative_frames'],'bank1_frames':m['cumulative_bank1_frames'],'runtime_verified':False}
    (ROOT/'projects/ver_rin_nana/current_build.json').write_text(json.dumps(pointer,indent=2)+'\n','utf8')
    print(json.dumps({'output':str(out),'sha256':result['sha256'],'changed_sectors':len(changed)}))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--art',type=Path,required=True);main(p.parse_args().art)
