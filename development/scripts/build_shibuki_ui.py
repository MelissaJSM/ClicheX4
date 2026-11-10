"""Build an isolated UI candidate and verify every raw sector against its parent."""
import argparse,json,shutil,sys
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.inventory_shibuki_ui import load,D,PARENT
from scripts.project import digest,working_cue,inspect_references,load_project
from scripts.discover_inputs import sha256,DiscReader
from src.psx_disc import write_archive_copies
from src.psx_sector import validate_checks

def build(recipe_path):
    recipe_path=recipe_path.resolve();recipe=json.loads(recipe_path.read_text('utf8'))
    if not recipe_path.is_relative_to(D) or recipe['kind']!='shibuki_ui_illustrations':raise ValueError('Unsupported UI recipe')
    if recipe['parent_build']!=str(PARENT.relative_to(ROOT)):raise ValueError('Unexpected UI parent')
    if recipe.get('text_pending') is not True:raise ValueError('This graphics-only builder requires separate reviewed text integration')
    if digest(PARENT/'manifest.json')!=recipe['parent_manifest_sha256']:raise ValueError('Parent manifest changed')
    records,original,current=load();parent=PARENT/'shibuki_riko.bin'
    if digest(parent)!=recipe['parent_bin_sha256']:raise ValueError('Parent BIN changed')
    project=load_project(ROOT,'ver_buki_riko');inspect_references(ROOT,project)
    replacements=[];payloads={};names=set()
    for item in recipe['files']:
        name=item['file']
        if name in names or name not in records or Path(name).name!=name:raise ValueError('Invalid or duplicate resource')
        names.add(name);source=records[name];data=(recipe_path.parent/name).read_bytes()
        if source!=item['source'] or sha256(current[name])!=item['parent_sha256'] or sha256(data)!=item['sha256']:raise ValueError('Resource hash/binding changed')
        if len(data)!=source['size'] or data==current[name]:raise ValueError('Invalid replacement length/content')
        if name in ('PL01_U.ARC','ST0D_0Z.ARC'):raise ValueError('Riko-only resource modification refused')
        replacements.append(({**source,'sha256':item['parent_sha256']},data))
        for i in range((len(data)+2047)//2048):payloads[source['lba']+i]=data[i*2048:(i+1)*2048]
    if not names or not {'PL00_U.ARC','ST0E_U1.ARC','ST0F_UX.ARC'}<=names:raise ValueError('Incomplete UI recipe')
    out=ROOT/'out/ver_buki_riko'/('shibuki_ui_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'));out.mkdir(exist_ok=False)
    target=out/'shibuki_riko.bin';result=write_archive_copies(parent,target,replacements,recipe['parent_bin_sha256'])
    expected={r['lba'] for r in result['changed_sectors']};actual=[]
    with parent.open('rb') as a,target.open('rb') as b:
        for sector in range(result['size']//2352):
            before,after=a.read(2352),b.read(2352)
            if before==after:continue
            if sector not in expected or before[:24]!=after[:24]:raise ValueError('Unexpected raw-sector difference')
            validate_checks(after);actual.append(sector);chunk=payloads[sector]
            if after[24:24+len(chunk)]!=chunk or after[24+len(chunk):2072]!=before[24+len(chunk):2072]:raise ValueError('Sector payload differs')
    if set(actual)!=expected:raise ValueError('Sector accounting differs')
    with target.open('rb') as f:
        reader=DiscReader(f,target.stat().st_size)
        for record,data in replacements:
            if reader.read(record['lba'],record['size'])!=data:raise ValueError('Archive readback differs')
    if digest(parent)!=recipe['parent_bin_sha256'] or digest(ROOT/project['source_bin'])!=recipe['source_sha256']:raise ValueError('Input changed')
    inspect_references(ROOT,project)
    (out/'shibuki_riko.cue').write_text(working_cue((PARENT/'shibuki_riko.cue').read_text('ascii'),'shibuki_riko.bin'),encoding='ascii')
    shutil.copyfile(recipe_path,out/'recipe.json');shutil.copyfile(recipe_path.parent/'PL00_U.ARC',out/'modified.arc')
    for name in ('review.png','details.png','verification.json'):
        if (recipe_path.parent/name).exists():shutil.copyfile(recipe_path.parent/name,out/name)
    # Store full sector proof separately to keep the build manifest reviewable.
    (out/'sector_changes.json').write_text(json.dumps(result,indent=2),encoding='utf8')
    manifest={'project':'ver_buki_riko','task':'x_shibuki_ui','stage':'EXPANSION','kind':'shibuki_ui_graphics_candidate',
        'source_sha256':recipe['source_sha256'],'parent_build':recipe['parent_build'],'parent_bin_sha256':recipe['parent_bin_sha256'],
        'modified_bin':{k:v for k,v in result.items() if k!='changed_sectors'},'changed_sectors':len(actual),'modified_archive_sha256':sha256((out/'modified.arc').read_bytes()),
        'recipe':str(recipe_path.relative_to(ROOT)),'resource_count':len(names),'full_disc_sectors_compared':result['size']//2352,
        'riko_player_preserved':True,'gameplay_preserved':True,'archive_sizes_lbas_preserved':True,'exe_changed':False,
        'runtime_verified':False,'user_review_pending':True,'dialogue_text_applied':False,'dialogue_relocation_approval_pending':True}
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf8')
    print(json.dumps({'output':str(out),'sha256':result['sha256'],'changed_sectors':len(actual),'full_disc_verified':True}))
    return out

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--recipe',type=Path,required=True);a=p.parse_args();build(a.recipe)
