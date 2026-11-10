"""Fix residual original Zero CLUT references in the accepted HQ artwork."""
import argparse
import json
import shutil
import struct
from pathlib import Path
from scripts.prepare_riko_ui import entry, replace_entry
from scripts.project import digest
from src.psx_ui_atlas import aliased_composition
from src.psx_ui_render import render_static_rgba


def prepare(source, output):
    if output.exists():raise ValueError('Output exists')
    recipe=json.loads((source/'recipe.json').read_text('utf8'))
    for r in recipe['files']:
        if digest(source/r['file'])!=r['sha256']:raise ValueError('Source candidate changed')
    arc=(source/'ST0D_0Z.ARC').read_bytes();parts=entry(arc,10);changed=bytearray(parts)
    compositions=[aliased_composition(parts,2,n) for n in range(14)]
    if compositions[0]['bank_frame_count']!=14:raise ValueError('Unsupported HQ frame bank')
    offsets=set();counts={}
    for n,c in enumerate(compositions):
        counts[n]=sum(p['clut']!=0 for p in c['parts'])
        for p in c['parts']:
            if p['clut']:
                changed[p['record_offset']] &= ~12
                offsets.add(p['record_offset'])
    if not offsets:raise ValueError('Source already uses the Riko palette')
    banks=struct.unpack_from('<I',parts)[0]//4
    for b in range(banks):
        if b==2:continue
        for n in range(aliased_composition(parts,b,0)['bank_frame_count']):
            if aliased_composition(parts,b,n)!=aliased_composition(bytes(changed),b,n):
                raise ValueError('Another HQ character or UI shares changed flags')
    for i,(a,b) in enumerate(zip(parts,changed)):
        if a!=b and (i not in offsets or (a^b)&~12):raise ValueError('Non-CLUT parts data changed')
    outarc=replace_entry(arc,10,bytes(changed))
    shutil.copytree(source,output);(output/'ST0D_0Z.ARC').write_bytes(outarc)
    g=entry(arc,0x10102)[63488:81920];pal=entry((source/'COL0D_0Z.ARC').read_bytes(),5)
    palettes={i:struct.unpack('<16H',pal[(35+i)*32:(36+i)*32]) for i in range(4)}
    frame_changes=[]
    for n,c in enumerate(compositions):
        before,_=render_static_rgba(g,c,palettes)
        after,_=render_static_rgba(g,aliased_composition(bytes(changed),2,n),palettes)
        before.save(output/f'hq_actual_before_{n:02d}.png');after.save(output/f'hq_actual_after_{n:02d}.png')
        frame_changes.append({'frame':n,'corrected_part_flags':counts[n],
            'rgba_pixels_changed':sum(a!=b for a,b in zip(list(before.get_flattened_data()),list(after.get_flattened_data())))})
    report={'bank':2,'clut':'0x7883','palette_row':35,'changed_flag_offsets':sorted(offsets),
        'frames':frame_changes,'texture_palette_geometry_and_timing_bytes_unchanged':True,
        'other_hq_banks_preserved':True,'cause':'Original auxiliary CLUT offsets survived UI regridding'}
    recipe['checks']['hunter_part_clut']=report
    for r in recipe['files']:r['sha256']=digest(output/r['file'])
    (output/'recipe.json').write_text(json.dumps(recipe,indent=2)+'\n',encoding='utf8')
    (output/'clut_fix.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
    print(json.dumps({'output':str(output),'flags_corrected':len(offsets),'frames':frame_changes}))


if __name__=='__main__':
    p=argparse.ArgumentParser()
    for n in ('source','output'):p.add_argument('--'+n,type=Path,required=True)
    a=p.parse_args();prepare(a.source,a.output)
