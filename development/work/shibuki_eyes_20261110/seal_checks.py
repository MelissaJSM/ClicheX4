import hashlib,json,os,subprocess,zipfile,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
D=Path(__file__).parent;W=ROOT/'work/steam_port_20261109';B=ROOT/'work/steam_distribution_20261110'
def load(p):return json.loads(p.read_text('utf8'))
def h(p):
    with p.open('rb')as f:return hashlib.file_digest(f,'sha256').hexdigest()
old={r['relative_path']:r['installed_sha256']for r in load(D/'install_state_before.json')['files']}
new=load(W/'install_state.json')['files'];baseline=load(W/'backup_manifest.json');game=Path(baseline['steam_root'])
assert all(h(game/r['relative_path'])==r['installed_sha256']for r in new)
assert all(h(W/'original'/r['relative_path'])==r['sha256']for r in baseline['originals'])
changes=[r['relative_path']for r in new if r['installed_sha256']!=old[r['relative_path']]];assert len(changes)==33
ps1={'out/ver_rin_nana/hq_armor_20261109_v3/rin_nana.bin':'03bb660be698dd7dd1b1b3fbf6612bcd1ed111cff47b5eda7c186ded3f343f3a','out/ver_buki_riko/capsule_outline_20261109_v1/shibuki_riko.bin':'0d76b1e983275482e4aa5d56ebdaa4a7d6f01a571e8cea218337df9eb84ed46e'}
assert all(h(ROOT/p)==v for p,v in ps1.items())
assert h(ROOT/'out/releases/ClicheX4_Steam_v1.0.0.zip')=='a32982a8c6000e6dc0e5d040539596a4ca9da63ff0d23e8ba37b81bac798d58b'
dest=B/'압축 해제 실행 확인';dest.mkdir(exist_ok=True)
with zipfile.ZipFile(ROOT/'out/releases/ClicheX4_Steam_v1.0.1.zip')as z:
    assert all((dest/n).resolve().is_relative_to(dest.resolve())for n in z.namelist())
    for n in z.namelist():
        p=dest/n;raw=z.read(n)
        if p.exists():assert p.read_bytes()==raw
        else:p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw)
env=dict(os.environ);env['PATH']=str(Path(os.environ['SystemRoot'])/'System32')
report=B/'validation/extracted_clean_path_verify.json'
r=subprocess.run([str(dest/'ClicheX4_Steam_v1.0.1/ClicheX4.exe'),'--action','verify','--game-dir',str(game),'--report',str(report)],env=env,creationflags=subprocess.CREATE_NO_WINDOW,timeout=60)
proof=load(report);assert r.returncode==0 and proof['ok'] and proof['result']['installed']==237
result={'passed':True,'installed_readback_files':len(new),'only_33_intended_resources_changed':True,'original_backups_verified':len(baseline['originals']),'both_ps1_final_bins_preserved':True,'previous_release_zip_preserved':True,'zip_extracted_exe_verify_without_python_path':True,'user_report':'이상없이 적용되었어','full_scene_replay_performed':False}
(D/'final_verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n','utf8');print(result)
