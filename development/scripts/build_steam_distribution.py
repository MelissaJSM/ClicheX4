"""Build a local source-verified delta release and a clean freezer source tree."""
import ast
import hashlib
import json
from pathlib import Path
import shutil
import sys
import zipfile

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from src.steam_distribution import SCHEMA, encode_delta, decode_delta, digest, json_bytes, Package

W=ROOT/'work/steam_port_20261109'
from scripts.steam_distribution_release import BUILD,STAGE,OUT,RELEASE
MODULES=['steam_title_position','steam_portrait_routes','steam_dialogue_outfits','steam_ultimate_player','steam_menu_outfits','steam_audio_runtime','steam_effect_colors']


def load(p):return json.loads(p.read_text('utf8'))
def put(p,raw):
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_bytes(raw.encode('utf8') if isinstance(raw,str) else raw)
def function(path,name):
    text=path.read_text('utf8');node=next(n for n in ast.parse(text).body if isinstance(n,ast.FunctionDef) and n.name==name)
    return '\n'.join(text.splitlines()[node.lineno-1:node.end_lineno])+'\n'
def replace_once(text,old,new):
    if text.count(old)!=1:raise ValueError('Packaging adapter source changed: '+old[:80])
    return text.replace(old,new)


def main():
    OUT.mkdir(parents=True,exist_ok=True);STAGE.mkdir(parents=True,exist_ok=True)
    baseline=load(W/'backup_manifest.json');game=Path(baseline['steam_root'])
    originals={r['relative_path']:r for r in baseline['originals']}
    tracked=load(W/'install_state.json')['files']
    current=[r for r in tracked if r['relative_path']!='RXC1.exe']
    mapping={r['target_arc']:r['original_target_arc'] for name in ('portrait_builds','hq_variant_builds') for r in load(W/(name+'.json'))}
    manifest={'schema':SCHEMA,'release':RELEASE,'appid':743890,'steam_buildid':baseline['buildid'],
              'exe_sha256':originals['RXC1.exe']['sha256'],
              'modes':{'Japanese':'하나코 나나 / 아오쿠모 린','English (US)':'텐코 시부키 / 유즈하 리코'},'files':[]}
    previous_versions={}
    for version,expected in [('1.0.0','aafd95a29af885dfd2ee752d15ccd4ddeb584a93bb80cc54a46ab64296502fd8'),('1.0.1','30b9ae1e2b4c4908ca5511fcc1c851199e797e42e99a218e7420d03af9014ac1'),('1.0.2','36101e3b0a3ad5df7b5f2ecf657edf76f8f1935525f934de20906b6364b384de')]:
        previous_path=ROOT/f'out/releases/ClicheX4_Steam_v{version}/patches.zip'
        assert digest(previous_path.read_bytes())==expected
        with zipfile.ZipFile(previous_path) as z:previous=json.loads(z.read('manifest.json'))
        assert previous['release']==version
        previous_versions[version]={r['target']:r for r in previous['files']}
    manifest['upgrade_from']=list(previous_versions)
    if digest((game/'RXC1.exe').read_bytes())!=manifest['exe_sha256']:raise ValueError('Original EXE required')
    patch=OUT/'patches.zip'
    with zipfile.ZipFile(patch,'w',compression=zipfile.ZIP_STORED) as z:
        for i,r in enumerate(sorted(current,key=lambda r:r['relative_path'])):
            rel=r['relative_path'];source=rel if rel in originals else 'nativeDX10/X4/romPC/'+mapping[Path(rel).name]
            b=(W/'original'/source).read_bytes();a=(game/rel).read_bytes()
            if digest(b)!=originals[source]['sha256'] or digest(a)!=r['installed_sha256']:raise ValueError('Release input hash differs: '+rel)
            delta=encode_delta(b,a)
            row={'target':rel,'source':source,'source_sha256':digest(b),'source_size':len(b),
                 'original_sha256':originals[rel]['sha256'] if rel in originals else None,
                 'sha256':digest(a),'size':len(a),'patch':f'delta/{i:04d}.xor.z','patch_sha256':digest(delta)}
            row['previous_sha256']={}
            for version,previous_rows in previous_versions.items():
                prior=previous_rows[rel]
                assert all(prior[k]==row[k]for k in ('source','source_sha256','source_size','original_sha256'))
                row['previous_sha256'][version]=prior['sha256']
            if decode_delta(b,delta,row)!=a:raise AssertionError(rel)
            z.writestr(row['patch'],delta);manifest['files'].append(row)
        z.writestr('manifest.json',json_bytes(manifest))
    pkg=Package(patch);check=pkg.inspect(game)
    assert check['installed']==len(current)==237 and len(tracked)==238,check
    put(STAGE/'release_config.py',f'RELEASE={RELEASE!r}\nPATCH_SHA256={digest(patch.read_bytes())!r}\nRUNTIME_MODULES={MODULES!r}\n')
    put(STAGE/'release_paths.py',"from pathlib import Path\nROOT=Path('.')\nEXE=Path('RXC1.exe')\n")
    put(STAGE/'main.py',(ROOT/'scripts/distribution_app.py').read_bytes())
    for folder in ('src','scripts'):put(STAGE/folder/'__init__.py','')
    for name in ('steam_distribution','steam_executable','steam_region_routes','steam_dialogue_variants','steam_ultimate','steam_menu_outfits','steam_effect_colors'):
        put(STAGE/'src'/(name+'.py'),(ROOT/'src'/(name+'.py')).read_bytes())
    put(STAGE/'src/steam_dialogue.py','import struct\n\n'+function(ROOT/'src/steam_dialogue.py','runtime_patches'))
    # Minimal window reader; no development control/capture/emulator dependencies.
    rt='import ctypes\nfrom ctypes import wintypes\nfrom pathlib import Path\nfrom release_paths import EXE\nfrom src.steam_executable import validate_executable\n\n'
    rt+=function(ROOT/'scripts/emulator_session.py','windows')+'\n'+function(ROOT/'scripts/steam_runtime.py','game_window')
    put(STAGE/'scripts/steam_runtime.py',rt)
    native=(W/'runtime/code/text.bin').read_bytes()
    if digest(native)!='38ff6b3ca58e7f4119b8ff5082bd0ad68429134eb90ffd3074da77341148e6cc':raise ValueError('Native comparison source changed')
    signatures={}
    for name in MODULES:
        text=(ROOT/'scripts'/(name+'.py')).read_text('utf8')
        if 'ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))' in text:
            text=replace_once(text,'ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))','from release_paths import ROOT')
        else:text=replace_once(text,'ROOT=Path(__file__).resolve().parents[1]\nsys.path.insert(0,str(ROOT))','from release_paths import ROOT')
        if name=='steam_audio_runtime':
            start,n,a=0x987e60,0xf6,0x987ec9
            b=native[start-0x401000:start-0x401000+n];p=bytearray(b);p[a-start:a-start+2]=b'\x90\x90'
            signatures[name]={'before':digest(b),'after':digest(p)}
            old="  text=(W/'runtime/code/text.bin').read_bytes();start=0x987e60;n=0xf6;expected_code=text[start-0x401000:start-0x401000+n]\n  live=read(start,n);patched=bytearray(expected_code);patched[a-start:a-start+2]=after\n  if live not in (expected_code,bytes(patched)):raise ValueError('Native intro function changed unexpectedly')\n  if live==expected_code:changed=True;write(after)"
            new=f"  start=0x987e60;n=0xf6;before_hash={digest(b)!r};after_hash={digest(p)!r}\n  live_hash=sha(read(start,n))\n  if live_hash not in (before_hash,after_hash):raise ValueError('Native intro function changed unexpectedly')\n  if live_hash==before_hash:changed=True;write(after)\n  if sha(read(start,n))!=after_hash:raise ValueError('Native intro readback differs')"
            text=replace_once(text,old,new)
        if name=='steam_effect_colors':
            from src.steam_effect_colors import signatures as effects
            b,p=effects(native);signatures[name]={'before':digest(b),'after':digest(p)}
            text=replace_once(text,',AFTER,signatures',',AFTER')
            text=replace_once(text," original,patched=signatures((W/'runtime/code/text.bin').read_bytes())",f' before_hash={digest(b)!r};after_hash={digest(p)!r}')
            text=replace_once(text,'if live not in (original,patched):','if sha(live) not in (before_hash,after_hash):')
            text=replace_once(text,'if live==original:','if sha(live)==before_hash:')
            text=replace_once(text,'if read(START,SIZE)!=patched:','if sha(read(START,SIZE))!=after_hash:')
        compile(text,str(Path('scripts')/(name+'.py')),'exec')
        put(STAGE/'scripts'/(name+'.py'),text)
    selections={
      'dialogue_display_patch':['installed_requirements','patches','menu_layout_patches'],
      'dialogue_runtime_patch':['installed_requirements','patches'],
      'portrait_routes':['routes','requirements'],
      'dialogue_variant_runtime':['installed_requirements','zero_palettes'],
      'ultimate_runtime':['installed_requirements','build_manifest'],
      'menu_outfits_runtime':['installed_requirements'],
      'audio_runtime':['installed_requirements'],
      'effect_colors_runtime':['address','before_hex','after_hex','proof_sha256','installed_requirements']}
    for name,keys in selections.items():
        data=load(W/(name+'.json'));put(STAGE/'runtime_specs'/(name+'.json'),json_bytes({k:data[k] for k in keys}))
    for name,keys in {'portrait_builds':['target_arc','output_sha256'],'hq_variant_builds':['target_arc','output_sha256'],
                      'audio_builds':['relative_path','output_sha256'],'pause_builds':['target_arc','relative_path','output_sha256']}.items():
        put(STAGE/'runtime_specs'/(name+'.json'),json_bytes([{k:r[k] for k in keys} for r in load(W/(name+'.json'))]))
    for name in ('audio/independent_verification.json','get_boss_completion/death_cpu_verification.json'):
        put(STAGE/'runtime_specs'/name,(W/name).read_bytes())
    # Reject accidental private paths, native dumps or user-state dependencies.
    for p in STAGE.rglob('*'):
        if p.is_file() and p.suffix in ('.py','.json'):
            t=p.read_text('utf8').lower()
            for banned in ('rpio_dev','rpio_d~','c:/users/','c:\\users\\','savedata.dat','runtime/code/text.bin'):
                if banned in t:raise ValueError('Private/development dependency: '+str(p)+' '+banned)
    report={'release':RELEASE,'files':len(current),'private_files':sum(r['original_sha256'] is None for r in manifest['files']),
            'patch_bytes':patch.stat().st_size,'patch_sha256':digest(patch.read_bytes()),'all_deltas_roundtrip':True,
            'installed_matches':check['installed'],'native_runtime_comparison_hashes':signatures,
            'original_game_files_bundled':False,'native_code_dump_bundled':False,'user_state_bundled':False}
    put(BUILD/'build_report.json',json_bytes(report));print(json.dumps(report))


if __name__=='__main__':main()
