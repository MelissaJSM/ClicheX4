import hashlib,json,os,subprocess,sys,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
W=ROOT/'work/steam_port_20261109';D=Path(__file__).parent;BUILD=ROOT/'work/steam_distribution_20261110_v102'
def load(p):return json.loads(p.read_text('utf8'))
def h(p):
    with p.open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
baseline=load(W/'backup_manifest.json');game=Path(baseline['steam_root']);old={r['relative_path']:r['installed_sha256']for r in load(D/'install_state_before.json')['files']};new=load(W/'install_state.json')['files']
assert all(h(game/r['relative_path'])==r['installed_sha256']for r in new)
assert all(h(W/'original'/r['relative_path'])==r['sha256']for r in baseline['originals'])
changed=[r['relative_path']for r in new if r['installed_sha256']!=old[r['relative_path']]]
assert set(changed)=={r['relative_path']for r in load(D/'builds.json')} and len(changed)==3
preserved={'out/ver_rin_nana/hq_armor_20261109_v3/rin_nana.bin':'03bb660be698dd7dd1b1b3fbf6612bcd1ed111cff47b5eda7c186ded3f343f3a','out/ver_buki_riko/capsule_outline_20261109_v1/shibuki_riko.bin':'0d76b1e983275482e4aa5d56ebdaa4a7d6f01a571e8cea218337df9eb84ed46e','out/releases/ClicheX4_Steam_v1.0.0.zip':'a32982a8c6000e6dc0e5d040539596a4ca9da63ff0d23e8ba37b81bac798d58b','out/releases/ClicheX4_Steam_v1.0.1.zip':'a1ee4a0187bd83b33c057e2512c9f1d464bc6899d610de0413a8006418247a92'}
assert all(h(ROOT/p)==v for p,v in preserved.items())
launch=load(D/'live_launch.json');assert launch['ok'] and len(launch['result']['runtime_checks'])==7
assert launch['result']['pid']==53180
names=['live_selector_english.png','live_selector_japanese.png','live_pillars.png'];assert all((D/n).exists()for n in names)
dest=BUILD/'압축 해제 실행 확인';dest.mkdir(exist_ok=True)
with zipfile.ZipFile(ROOT/'out/releases/ClicheX4_Steam_v1.0.2.zip')as z:
    assert all((dest/n).resolve().is_relative_to(dest.resolve())for n in z.namelist())
    for n in z.namelist():
        p=dest/n;raw=z.read(n)
        if p.exists():assert p.read_bytes()==raw
        else:p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw)
env=dict(os.environ);env['PATH']=str(Path(os.environ['SystemRoot'])/'System32');report=BUILD/'validation/extracted_clean_path_verify.json'
r=subprocess.run([str(dest/'ClicheX4_Steam_v1.0.2/ClicheX4.exe'),'--action','verify','--game-dir',str(game),'--report',str(report)],env=env,creationflags=subprocess.CREATE_NO_WINDOW,timeout=60)
proof=load(report);assert r.returncode==0 and proof['ok'] and proof['result']['installed']==237
result={'passed':True,'installed_files_verified':len(new),'original_backups_verified':len(baseline['originals']),'changed_files':changed,'only_3_intended_resources_changed':True,'ps1_and_previous_releases_preserved':True,'original_executable_preserved':True,'runtime_checks':7,'pid':53180,'observed_captures':names,'zip_extracted_verify_without_python_path':True,'user_design_acceptance':False,'all_aspect_ratios_tested':False,'art_sources':{n:h(D/'art'/n)for n in ['ensemble_v5.png','pillar_pair_v4.png']}}
(D/'application.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps(result,ensure_ascii=False))
