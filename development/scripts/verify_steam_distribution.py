"""Exercise the frozen installer against an isolated owned-game fixture."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import zipfile
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from src.steam_distribution import digest,json_bytes

W=ROOT/'work/steam_port_20261109'
from scripts.steam_distribution_release import BUILD,OUT


def main():
    shutil.copytree(BUILD/'frozen/ClicheX4',OUT,dirs_exist_ok=True)
    fixture=BUILD/'검증용 게임 폴더 v2'
    if fixture.exists():raise ValueError('Existing fixture: use its previous evidence; do not overwrite')
    fixture.mkdir()
    with zipfile.ZipFile(OUT/'patches.zip') as z:m=json.loads(z.read('manifest.json'))
    sources={r['source'] for r in m['files']}|{'RXC1.exe'}
    baseline={}
    for rel in sorted(sources):
        p=fixture/rel;p.parent.mkdir(parents=True,exist_ok=True)
        raw=(W/'original'/rel).read_bytes();p.write_bytes(raw);baseline[rel]=digest(raw)
    for rel,raw in {'config.ini':b'user chosen settings','savedata.dat':b'never change user progress'}.items():
        (fixture/rel).write_bytes(raw);baseline[rel]=digest(raw)
    evidence=BUILD/'validation';evidence.mkdir(exist_ok=True)
    reports=[]
    for i,action in enumerate(('verify','install','install','verify','restore','restore','verify')):
        target=evidence/f'{i:02d}_{action}.json'
        result=subprocess.run([str(OUT/'ClicheX4.exe'),'--action',action,'--game-dir',str(fixture),'--report',str(target)],
                              cwd=BUILD,creationflags=subprocess.CREATE_NO_WINDOW,timeout=120)
        report=json.loads(target.read_text('utf8'))
        if result.returncode or not report['ok']:raise AssertionError(report)
        reports.append(report)
    assert reports[0]['result']['original']==237
    assert reports[1]['result']['verified']==237
    assert reports[2]['result']['changed']==0
    assert reports[3]['result']['installed']==237
    assert reports[4]['result']['verified']==237
    assert reports[5]['result']['changed']==0
    assert reports[6]['result']['original']==237
    assert all(digest((fixture/n).read_bytes())==h for n,h in baseline.items())
    assert all(not (fixture/r['target']).exists() for r in m['files'] if r['original_sha256'] is None)
    installed=json.loads((W/'install_state.json').read_text('utf8'))['files']
    backup=json.loads((W/'backup_manifest.json').read_text('utf8'))
    game=Path(backup['steam_root'])
    assert all(digest((game/r['relative_path']).read_bytes())==r['installed_sha256'] for r in installed)
    assert all(digest((W/'original'/r['relative_path']).read_bytes())==r['sha256'] for r in backup['originals'])
    report={'passed':True,'frozen_executable':True,'fixture_has_spaces_and_korean':True,
            'changed_resources':237,'original_resources':193,'private_resources':44,
            'install_repeat_restore_repeat_passed':True,'fixture_exe_settings_saves_preserved':True,
            'live_installed_files_unchanged':len(installed),'original_backups_preserved':len(backup['originals']),
            'patch_sha256':digest((OUT/'patches.zip').read_bytes()),'exe_sha256':digest((OUT/'ClicheX4.exe').read_bytes())}
    (evidence/'summary.json').write_bytes(json_bytes(report));print(json.dumps(report))


if __name__=='__main__':main()
