"""Validated Hunter HQ overlay on the accepted Rin selection build."""
import argparse,json,shutil,sys
import numpy as np
from PIL import Image
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.prepare_rin_hunter import PARENT,PARENT_SHA,ART,sources,verify
from scripts.project import digest
from scripts.build_rin_idle import sha
from scripts.discover_inputs import DiscReader
from src.psx_disc import write_archive_copies
from src.psx_sector import validate_checks

def main(art):
    art=art.resolve()
    if not art.is_relative_to(ART):raise ValueError('Unexpected Hunter art folder')
    m,records,original=sources();r=json.loads((art/'recipe.json').read_text('utf8'))
    source=(ROOT/r['generated_source']).resolve()
    if not source.is_relative_to(ART) or r['parent_sha256']!=PARENT_SHA or digest(source)!=r['generated_sha256']:raise ValueError('Source art/parent changed')
    departure=r.get('forward_departure')
    if departure:
        dep=(ROOT/departure['source']).resolve()
        if not dep.is_relative_to(ART) or digest(dep)!=departure['sha256']:raise ValueError('Departure source changed')
    if len(r['files'])!=len(records):raise ValueError('Unexpected source set')
    modified={};replacements=[]
    for source,item in zip(records,r['files']):
        name=source['path'].split('/')[-1].split(';')[0]
        if source!=item['source'] or name!=item['file']:raise ValueError('Source binding changed')
        raw=(art/name).read_bytes()
        if sha(raw)!=item['sha256'] or len(raw)!=source['size']:raise ValueError('Candidate hash/length changed')
        modified[name]=raw;replacements.append((source,raw))
    world={n:np.array(Image.open(art/f'world_{n:02d}.png')) for n in range(14)}
    targets={n:(Image.open(art/f'frame_{n:02d}.png').tobytes(),Image.open(art/f'frame_{n:02d}.png').size) for n in range(14)}
    v=verify(original,modified,targets,world)
    preservation=json.loads((PARENT/'preservation.json').read_text('utf8'))
    def protect():
        for q in preservation['files']:
            if digest(ROOT/q['path'])!=q['expected_sha256']:raise ValueError('Protected input changed: '+q['path'])
    protect()
    out=ROOT/'out/ver_rin_nana'/('rin_hunter_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'));out.mkdir()
    result=write_archive_copies(PARENT/'rin_nana.bin',out/'rin_nana.bin',replacements,PARENT_SHA)
    shutil.copyfile(PARENT/'rin_nana.cue',out/'rin_nana.cue');shutil.copyfile(PARENT/'modified.arc',out/'modified.arc')
    shutil.copytree(art,out/'hunter');shutil.copytree(PARENT/'ui',out/'ui');shutil.copytree(PARENT/'portrait',out/'portrait')
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
            if d.read(rec['lba'],rec['size'])!=data:raise ValueError('Hunter readback differs')
        player=json.loads((ROOT/'config/ps1_us_slus00561.json').read_text('utf8'))['zero_archive']
        if sha(d.read(player['lba'],player['size']))!=m['modified_archive_sha256']:raise ValueError('Gameplay changed')
    protect();v.update(all_disc_sectors_compared=count,changed_sectors=len(changed),edc_ecc_checked=True,
                       other_parent_sectors_exact=True,readback_equal=True,protected_files=len(preservation['files']),
                       embedded_static_bodies=m['verification']['embedded_static_bodies'])
    manifest={**m,'kind':'rin_hunter','parent':PARENT.relative_to(ROOT).as_posix(),'parent_sha256':PARENT_SHA,
              'modified_bin':result,'verification':v,'inherited_verification':m['verification'],
              'hunter_overlay':{'recipe':(out/'hunter/recipe.json').relative_to(ROOT).as_posix(),
                                  'recipe_sha256':digest(out/'hunter/recipe.json'),'runtime_verified':False},'runtime_verified':False}
    for name,data in [('manifest.json',manifest),('verification.json',v),('preservation.json',preservation)]:
        (out/name).write_text(json.dumps(data,indent=2)+'\n','utf8')
    pointer={'project':'ver_rin_nana','task':'zero_rin','build':out.relative_to(ROOT).as_posix(),
             'cue':(out/'rin_nana.cue').relative_to(ROOT).as_posix(),'sha256':result['sha256'],
             'frames':m['cumulative_frames'],'bank1_frames':m['cumulative_bank1_frames'],'runtime_verified':False}
    (ROOT/'projects/ver_rin_nana/current_build.json').write_text(json.dumps(pointer,indent=2)+'\n','utf8')
    print(json.dumps({'output':str(out),'sha256':result['sha256'],'changed_sectors':len(changed)}))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--art',type=Path,required=True);main(p.parse_args().art)
