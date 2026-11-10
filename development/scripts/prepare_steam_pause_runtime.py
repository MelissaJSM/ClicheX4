"""Bind verified cumulative pause archives to existing runtime adapters."""
import json,sys,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];W=ROOT/'work/steam_port_20261109'
def read(name):return json.loads((W/name).read_text('utf8'))
def write(name,v):(W/name).write_text(json.dumps(v,indent=2)+'\n','utf8')
def main():
    builds=read('pause_builds.json');cpu=read('menu_outfits_cpu_verification.json');art=read('menu_outfits_static_verification.json')
    if cpu['native_save_constructor_cases']!=9216 or cpu['pause_selector_cases']!=3744:raise ValueError('CPU proof missing')
    if len(art)!=2 or not all(r['pixels_and_palette_match_ps1'] and r['shared_load_pl00_pl02_textures_cof_ctex_identical'] for r in art):raise ValueError('Shared cache/art proof missing')
    icons=read('save_issue_20261109/icon_verification.json')
    if icons['mismatch_count']!=0 or len(icons['results'])!=2 or not all(r['icons']==20 and r['cof_icon_offsets_zero'] for r in icons['results']):raise ValueError('Shared save icons proof missing')
    requirements={}
    for r in builds:
        if hashlib.sha256((ROOT/r['output']).read_bytes()).hexdigest()!=r['output_sha256']:raise ValueError('Build hash mismatch')
        requirements['nativeDX10/X4/romPC/'+r['target_arc']]=r['output_sha256']
    if len(requirements)!=8:raise ValueError('Complete cumulative assets required')
    for name in ('dialogue_runtime_patch.json','dialogue_display_patch.json','ultimate_runtime.json'):
        backup=W/('before_pause_v3_'+name)
        if not backup.exists():backup.write_bytes((W/name).read_bytes())
        spec=read(name)
        spec['installed_requirements']={key:requirements[key] for key in spec['installed_requirements']}
        if name=='ultimate_runtime.json':spec['build_manifest']='pause_builds.json'
        write(name,spec)
    write('menu_outfits_runtime.json',{'installed_requirements':requirements})
    print({'runtime_asset_requirements':len(requirements),'existing_display_code_preserved':True})
if __name__=='__main__':main()
