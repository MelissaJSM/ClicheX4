"""Same-length selection/save UI overlay on the accepted Riko gameplay build."""
import argparse
from datetime import datetime,timezone
import json
from pathlib import Path
import shutil
import struct
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts.project import digest,load_project,working_cue,write_json
from scripts.discover_inputs import DiscReader,sha256
from scripts.prepare_riko_ui import entry,replace_entry,actual_frame,SELECTION_MAPPING
from src.psx_player import composition_frame
from src.psx_static_effect import compose_static,patch_static
from src.psx_ui_atlas import local_composition,place_frame
from src.psx_frame_edit import read_indexed_png
from src.psx_disc import write_archive_copies


def ui_replacements(source,recipe_path,model):
    from scripts.riko_master_sheet import local
    recipe_path=local(recipe_path,ROOT/'work/ver_buki_riko')
    recipe=json.loads(recipe_path.read_text('utf8'))
    config=json.loads((ROOT/'config/riko_ui_us.json').read_text('utf8'))
    if recipe['source_sha256']!=config['source_sha256'] or model['manifest']['source_sha256']!=config['source_sha256']:
        raise ValueError('Unsupported UI source BIN')
    if recipe['mapping']!={str(k):list(v) for k,v in SELECTION_MAPPING.items()}:
        raise ValueError('Unsupported UI pose mapping')
    candidates={r['source']['path']:r for r in recipe['files']}
    if set(candidates)!={r['path'] for r in config['archives']}:raise ValueError('Unexpected UI file set')
    originals={};modified={};replacements=[]
    with source.open('rb') as stream:
        disc=DiscReader(stream,source.stat().st_size);actual={r['path']:r for r in disc.inspect()['files']}
        for rec in config['archives']:
            item=candidates[rec['path']]
            if any(item['source'][k]!=rec[k] for k in rec) or any(actual[rec['path']][k]!=rec[k] for k in ('lba','size')):
                raise ValueError('UI ISO/archive binding changed')
            path=local(recipe_path.parent/item['file'],recipe_path.parent)
            data=path.read_bytes();old=disc.read(rec['lba'],rec['size'])
            if sha256(old)!=rec['sha256'] or sha256(data)!=item['sha256'] or len(data)!=len(old):
                raise ValueError('UI source/target hash or length mismatch')
            name=Path(item['file']).name;originals[name]=old;modified[name]=data;replacements.append((rec,data))
    old=originals['ST0E_U1.ARC'];new=modified['ST0E_U1.ARC'];ot=entry(old,0x10102);nt=entry(new,0x10102);op=entry(old,0xa);np=entry(new,0xa)
    if replace_entry(replace_entry(old,0x10102,nt),0xa,np)!=new or nt[90112:]!=ot[90112:]:raise ValueError('Selection changed X/background resources')
    allowed=set()
    for bank,lo,hi in ((0,0,40960),(1,40960,90112),(2,90112,len(nt))):
        count=composition_frame(op,bank,0)['bank_frame_count']
        for n in range(count):
            a=composition_frame(op,bank,n);b=composition_frame(np,bank,n)
            target=bank==0 and n in SELECTION_MAPPING or bank==1 and n==1
            if len(a['parts'])!=len(b['parts']):raise ValueError('UI part count changed')
            for p,q in zip(a['parts'],b['parts']):
                if any(p[k]!=q[k] for k in ('x','y','flip_x','flip_y','unknown_flags','record_offset')):
                    raise ValueError('UI part geometry/order changed')
                if p['clut']!=q['clut'] and (bank,n,q['clut'])!=(0,38,0):raise ValueError('Unexpected UI CLUT selector change')
                if target:allowed.update((p['record_offset'],p['record_offset']+1))
            rendered=compose_static(nt[lo:hi],local_composition(b))[:2]
            if bank==0 and n in SELECTION_MAPPING:
                expected=place_frame(actual_frame(model,*SELECTION_MAPPING[n]),a,ot[lo:hi])
            elif bank==1 and n==1:
                pal=(recipe_path.parent/'portrait_palette.bin').read_bytes()
                expected=read_indexed_png(recipe_path.parent/'portrait_indexed.png',struct.unpack('<16H',pal))
            else:expected=compose_static(ot[lo:hi],local_composition(a))[:2]
            if rendered!=expected:raise ValueError(f'UI sprite mismatch: {bank}:{n}')
    if any(a!=b and i not in allowed for i,(a,b) in enumerate(zip(op,np))):raise ValueError('UI header/untouched parts changed')
    old=originals['COL0E_U1.ARC'];p=bytearray(entry(old,5));p[:32]=model['palette'];p[160:192]=(recipe_path.parent/'portrait_palette.bin').read_bytes()
    if replace_entry(old,5,bytes(p))!=modified['COL0E_U1.ARC']:raise ValueError('Unexpected selection palette change')
    old=originals['MOJIPAT.ARC'];start=config['save_palette_offset']
    if old[:start]+model['palette']+old[start+32:]!=modified['MOJIPAT.ARC']:raise ValueError('Unexpected menu data change')
    old=originals['LOAD_U.ARC'];g=entry(old,0x10008);c=local_composition(composition_frame(originals['MOJIPAT.ARC'],2,43))
    desired=place_frame(actual_frame(model,0,147),c,g);edited=patch_static(g,{43:c},{43:desired})
    if replace_entry(old,0x10008,edited)!=modified['LOAD_U.ARC']:raise ValueError('Unexpected loading atlas change')
    for n in range(c['bank_frame_count']):
        if n==43:continue
        co=local_composition(composition_frame(originals['MOJIPAT.ARC'],2,n))
        if compose_static(g,co)[:2]!=compose_static(edited,co)[:2]:raise ValueError('Save icon corrupts another menu frame')
    return replacements


def validate_layer(build,manifest,model):
    from scripts.riko_master_sheet import local
    layer=manifest['ui_overlay'];parent=local(Path(layer['parent_build']),ROOT/'out/ver_buki_riko')
    recipe=local(Path(layer['recipe']),ROOT/'work/ver_buki_riko')
    if digest(parent/'manifest.json')!=layer['parent_manifest_sha256'] or digest(recipe)!=layer['recipe_sha256'] or digest(ROOT/'config/riko_ui_us.json')!=layer['config_sha256']:
        raise ValueError('UI overlay recipe/parent/config changed')
    if (build/'modified.arc').read_bytes()!=model['built_arc'] or manifest['modified_archive_sha256']!=sha256(model['built_arc']):
        raise ValueError('UI overlay changed the gameplay archive')
    for path in parent.glob('*.png'):
        if digest(path)!=digest(build/path.name):raise ValueError('UI overlay changed accepted art')
    source=ROOT/load_project(ROOT,'ver_buki_riko')['source_bin'];replacements=ui_replacements(source,recipe,model)
    game=build/manifest['bin_file']
    with game.open('rb') as stream:
        disc=DiscReader(stream,game.stat().st_size)
        for rec,data in replacements:
            if disc.read(rec['lba'],rec['size'])!=data:raise ValueError('UI BIN differs from recipe')
    model.update(build=build,manifest=manifest)
    return model


def build(parent,extracted,recipe):
    from scripts.riko_master_sheet import load_model,local
    from scripts.build_riko_personal_effects import stage_replacements
    parent=local(parent,ROOT/'out/ver_buki_riko');recipe=local(recipe,ROOT/'work/ver_buki_riko')
    m=load_model(parent,extracted);r=json.loads(recipe.read_text('utf8'))
    if m['manifest'].get('ui_overlay') or not m['manifest'].get('jump_alignment'):raise ValueError('Expected the accepted pre-UI build')
    if Path(r['parent_build'])!=parent or r['parent_manifest_sha256']!=digest(parent/'manifest.json'):raise ValueError('UI art parent differs')
    project=load_project(ROOT,'ver_buki_riko');source=ROOT/project['source_bin'];ui=ui_replacements(source,recipe,m)
    profile=json.loads((ROOT/'config/ps1_us_slus00561.json').read_text('utf8'))
    ec=json.loads((ROOT/'config/riko_personal_effects_us.json').read_text('utf8'));stages=stage_replacements(source,ec,m['palette'])
    out=ROOT/'out/ver_buki_riko'/('riko_ui_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'));out.mkdir()
    result=write_archive_copies(source,out/'riko_motion.bin',[(profile['zero_archive'],m['built_arc']),*stages,*ui],m['manifest']['source_sha256'])
    shutil.copyfile(parent/'modified.arc',out/'modified.arc')
    for p in parent.glob('*.png'):shutil.copyfile(p,out/p.name)
    (out/'riko_motion.cue').write_text(working_cue((ROOT/project['source_cue']).read_text('utf-8-sig'),'riko_motion.bin'),'ascii')
    manifest=dict(m['manifest']);manifest.update(kind='riko_selection_save_ui_v1',modified_bin=result,
        ui_overlay={'parent_build':str(parent),'parent_manifest_sha256':digest(parent/'manifest.json'),
        'recipe':str(recipe),'recipe_sha256':digest(recipe),'config_sha256':digest(ROOT/'config/riko_ui_us.json'),
        'changed_ui_files':[r['path'] for r,d in ui],'runtime_verified':False})
    write_json(out/'manifest.json',manifest);validate_layer(out,manifest,m)
    print(json.dumps({'output':str(out),'sha256':result['sha256'],'changed_sectors':len(result['changed_sectors'])}))
    return out


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('parent','extract','recipe'):p.add_argument('--'+n,type=Path,required=True)
    a=p.parse_args();build(a.parent,a.extract,a.recipe)
