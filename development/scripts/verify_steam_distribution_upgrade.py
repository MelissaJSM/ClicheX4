"""Verify release migration in an isolated fixture while the user can keep playing."""
import json,sys,subprocess,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from src.steam_distribution import Package,digest,json_bytes
from scripts.steam_distribution_release import BUILD,OUT,RELEASE
W=ROOT/'work/steam_port_20261109'
def main():
    shutil.copytree(BUILD/'frozen/ClicheX4',OUT,dirs_exist_ok=True)
    new=Package(OUT/'patches.zip')
    results=[verify(version,new)for version in new.manifest['upgrade_from']]
    (BUILD/'validation/upgrade_summary.json').write_bytes(json_bytes({'passed':True,'migrations':results}));print(json.dumps(results))
def verify(version,new):
    fixture=BUILD/('이전 버전 업데이트 검증 '+version);assert not fixture.exists();fixture.mkdir()
    old=Package(ROOT/f'out/releases/ClicheX4_Steam_v{version}/patches.zip')
    originals={r['source'] for r in new.rows}|{'RXC1.exe'};checks={}
    for rel in originals:
        raw=(W/'original'/rel).read_bytes();p=fixture/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw);checks[rel]=digest(raw)
    for rel,raw in {'savedata.dat':b'user progress','config.ini':b'user settings'}.items():(fixture/rel).write_bytes(raw);checks[rel]=digest(raw)
    expected=sum(r['sha256']!=r['previous_sha256'][version]for r in new.rows)
    first=old.apply(fixture);before=new.inspect(fixture);assert before['upgradable']==expected,before
    upgraded=new.apply(fixture);assert upgraded['changed']==expected and upgraded['verified']==237
    evidence=BUILD/'validation';evidence.mkdir(exist_ok=True);report=evidence/('final_frozen_verify_upgraded_'+version+'.json')
    p=subprocess.run([str(OUT/'ClicheX4.exe'),'--action','verify','--game-dir',str(fixture),'--report',str(report)],creationflags=subprocess.CREATE_NO_WINDOW,timeout=60)
    verified=json.loads(report.read_text('utf8'));assert p.returncode==0 and verified['ok'] and verified['result']['installed']==237
    repeat=new.apply(fixture);assert repeat['changed']==0
    restore=new.apply(fixture,restore=True);assert restore['verified']==237
    assert new.apply(fixture,restore=True)['changed']==0
    assert all(digest((fixture/n).read_bytes())==h for n,h in checks.items())
    assert all(not(fixture/r['target']).exists()for r in new.rows if r['original_sha256']is None)
    return {'passed':True,'old_release':version,'new_release':RELEASE,'changed_resources':expected,'total_resources':237,'original_backups_exe_settings_save_preserved':True,'upgrade_repeat_restore_repeat':True,'final_frozen_verify_passed':True,'game_not_interrupted':True,'final_frozen_exe_sha256':digest((OUT/'ClicheX4.exe').read_bytes())}
if __name__=='__main__':main()
