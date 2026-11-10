"""Reproducible fixed-size illustration/text overlay on accepted gameplay assets."""
import argparse,json,shutil,struct,sys
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.project import digest,load_project,working_cue,write_json
from scripts.discover_inputs import DiscReader,psx_arc,sha256
from scripts.prepare_riko_ui import entry,replace_entry
from src.psx_disc import write_archive_copies
from src.psx_text import rename_zero

PLAYER_UI_TYPES=(0x10007,0x11,0x15)

def apply_player_ui(arc,recipe_path):
    recipe=json.loads(recipe_path.read_text('utf8'))
    item=next(r for r in recipe['files'] if r['source']['path']=='/ARC/PL01_U.ARC;1')
    target=(recipe_path.parent/item['file']).read_bytes()
    if sha256(target)!=item['sha256']:raise ValueError('Player UI candidate hash mismatch')
    for kind in PLAYER_UI_TYPES:arc=replace_entry(arc,kind,entry(target,kind))
    if recipe.get('death_orbs'):
        from src.psx_death_orbs import recolor_death_orbs
        arc,report=recolor_death_orbs(arc)
        if json.loads(json.dumps(report))!=recipe['death_orbs']:raise ValueError('Death orb recipe differs')
    if recipe.get('hud_mark'):
        from src.psx_hud_mark import replace_hud_mark
        arc,report=replace_hud_mark(arc)
        if json.loads(json.dumps(report))!=recipe['hud_mark']:raise ValueError('HUD mark recipe differs')
    return arc

def checked_recipe(parent,recipe_path):
    recipe=json.loads(recipe_path.read_text('utf8'));pm=json.loads((parent/'manifest.json').read_text('utf8'))
    if Path(recipe['parent_build'])!=parent or recipe['parent_manifest_sha256']!=digest(parent/'manifest.json') or recipe['source_sha256']!=pm['source_sha256']:
        raise ValueError('Illustration parent binding differs')
    source=ROOT/load_project(ROOT,'ver_buki_riko')['source_bin'];items=[];seen=set()
    with source.open('rb') as sf,(parent/pm['bin_file']).open('rb') as pf:
        sd=DiscReader(sf,source.stat().st_size);pd=DiscReader(pf,(parent/pm['bin_file']).stat().st_size)
        actual={r['path']:r for r in sd.inspect()['files']}
        for item in recipe['files']:
            rec=item['source'];name=rec['name'].split(';')[0];candidate=(recipe_path.parent/item['file']).resolve()
            if candidate.parent!=recipe_path.parent or candidate.name!=name or rec['path'] in seen:raise ValueError('Invalid illustration candidate path')
            seen.add(rec['path'])
            if not name.endswith('.ARC') or name=='MOJIPAT.ARC':raise ValueError('Unsupported illustration resource')
            if any(actual[rec['path']][k]!=rec[k] for k in ('lba','size')):raise ValueError('Illustration ISO binding differs')
            old=sd.read(rec['lba'],rec['size']);before=pd.read(rec['lba'],rec['size']);data=candidate.read_bytes()
            if sha256(old)!=rec['sha256'] or sha256(before)!=item['parent_sha256'] or sha256(data)!=item['sha256'] or len(data)!=len(old):raise ValueError('Illustration hash/size mismatch')
            allowed={5} if name.startswith('COL') else set(PLAYER_UI_TYPES) if name=='PL01_U.ARC' else {0,1,0xa,0x10000,0x10102,0x10109,0x1010a}
            if name=='PL01_U.ARC' and (recipe.get('death_orbs') or recipe.get('hud_mark')):allowed|={3,0x10206}
            reconstructed=before
            for e in psx_arc(before):
                a=e['offset'];b=a+e['size']
                if before[a:b]!=data[a:b]:
                    if int(e['type'],16) not in allowed:raise ValueError('Illustration changed protected resource type')
                    reconstructed=reconstructed[:a]+data[a:b]+reconstructed[b:]
            if reconstructed!=data:raise ValueError('Illustration changed archive header/padding')
            if name=='PL01_U.ARC':
                if apply_player_ui(before,recipe_path)!=data:raise ValueError('Unexpected player UI/effect edit')
                text,changes=rename_zero(entry(before,0x15))
                if text!=entry(data,0x15) or changes!=recipe['checks']['text_changes']:raise ValueError('Unexpected dialogue edit')
            if name=='ST0D_0Z.ARC' and recipe['checks'].get('hunter_part_clut'):
                from src.psx_ui_atlas import aliased_composition
                for n in range(14):
                    if any(p['clut'] for p in aliased_composition(entry(data,10),2,n)['parts']):
                        raise ValueError('Original auxiliary palette remains in Riko HQ parts')
            items.append((rec,data))
    return items

def validate_layer(build,manifest,model):
    from scripts.riko_master_sheet import local
    layer=manifest['illustrations'];parent=local(Path(layer['parent_build']),ROOT/'out/ver_buki_riko')
    recipe=local(Path(layer['recipe']),ROOT/'work/ver_buki_riko')
    if digest(parent/'manifest.json')!=layer['parent_manifest_sha256'] or digest(recipe)!=layer['recipe_sha256']:raise ValueError('Illustration layer binding changed')
    expected=apply_player_ui(model['built_arc'],recipe)
    if (build/'modified.arc').read_bytes()!=expected or sha256(expected)!=manifest['modified_archive_sha256']:raise ValueError('Illustrations changed player gameplay assets')
    for p in parent.glob('*.png'):
        if digest(p)!=digest(build/p.name):raise ValueError('Accepted sprite art changed')
    files=checked_recipe(parent,recipe);game=build/manifest['bin_file']
    with game.open('rb') as f:
        disc=DiscReader(f,game.stat().st_size)
        for rec,data in files:
            if disc.read(rec['lba'],rec['size'])!=data:raise ValueError('Illustration BIN readback differs')
    model.update(build=build,manifest=manifest,built_arc=expected)
    return model

def build(parent,extracted,recipe):
    from scripts.riko_master_sheet import load_model,local
    parent=local(parent,ROOT/'out/ver_buki_riko');recipe=local(recipe,ROOT/'work/ver_buki_riko')
    model=load_model(parent,extracted);manifest=model['manifest']
    if not manifest.get('ui_overlay') or manifest.get('illustrations'):raise ValueError('Expected accepted UI parent')
    overlays=checked_recipe(parent,recipe);project=load_project(ROOT,'ver_buki_riko');source=ROOT/project['source_bin']
    replacements={}
    with source.open('rb') as sf,(parent/manifest['bin_file']).open('rb') as pf:
        sd=DiscReader(sf,source.stat().st_size);pd=DiscReader(pf,(parent/manifest['bin_file']).stat().st_size)
        for rec in sd.inspect()['files']:
            if rec.get('directory') or rec['size']==0 or rec['size']>16*1024*1024:continue
            if not (rec['path'].startswith('/ARC/') or rec['path']=='/SLUS_005.61;1'):continue
            old=sd.read(rec['lba'],rec['size']);new=pd.read(rec['lba'],rec['size'])
            if old!=new:replacements[rec['path']]=({**rec,'sha256':sha256(old)},new)
    for rec,data in overlays:replacements[rec['path']]=(rec,data)
    arc=apply_player_ui(model['built_arc'],recipe)
    out=ROOT/'out/ver_buki_riko'/('riko_illustrations_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'));out.mkdir()
    result=write_archive_copies(source,out/'riko_motion.bin',list(replacements.values()),manifest['source_sha256'])
    (out/'modified.arc').write_bytes(arc)
    for p in parent.glob('*.png'):shutil.copyfile(p,out/p.name)
    (out/'riko_motion.cue').write_text(working_cue((ROOT/project['source_cue']).read_text('utf-8-sig'),'riko_motion.bin'),'ascii')
    m=dict(manifest);m.update(kind='riko_illustrations_text_v1',modified_bin=result,modified_archive_sha256=sha256(arc),
        illustrations={'parent_build':str(parent),'parent_manifest_sha256':digest(parent/'manifest.json'),
          'recipe':str(recipe),'recipe_sha256':digest(recipe),'changed_files':[rec['path'] for rec,data in overlays],
          'runtime_verified':False,'player_animation_and_gameplay_preserved':True})
    write_json(out/'manifest.json',m);validate_layer(out,m,model)
    print(json.dumps({'output':str(out),'sha256':result['sha256'],'changed_sectors':len(result['changed_sectors'])}))
    return out

if __name__=='__main__':
    p=argparse.ArgumentParser()
    for n in ('parent','extract','recipe'):p.add_argument('--'+n,type=Path,required=True)
    a=p.parse_args();build(a.parent,a.extract,a.recipe)
