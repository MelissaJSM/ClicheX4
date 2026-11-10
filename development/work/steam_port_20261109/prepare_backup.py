import hashlib
import json
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[2]
WORK = Path(__file__).resolve().parent
STEAM = Path('C:/Program Files (x86)/Steam/steamapps/common/Mega Man X Legacy Collection')
inventory = json.loads((ROOT/'work/steam_port_research_20261109/inventory.json').read_text(encoding='utf-8'))
records = [inventory['executable']] + list(inventory['archives'].values()) + inventory['sound_files']
backup = WORK/'original'
checks = []
for row in records:
    source = Path(row['path'])
    raw = source.read_bytes()
    if hashlib.sha256(raw).hexdigest() != row['sha256']:
        raise ValueError(f'Unexpected source: {source.name}')
    target = backup/source.relative_to(STEAM)
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        if target.read_bytes() != raw:
            raise ValueError('Backup collision')
    else:
        target.write_bytes(raw)
    if hashlib.sha256(target.read_bytes()).hexdigest() != row['sha256']:
        raise ValueError('Backup verification failed')
    checks.append({'relative_path': source.relative_to(STEAM).as_posix(), 'sha256': row['sha256'], 'size': len(raw)})
extra = [STEAM/'config.ini']
for account in (STEAM.parents[2]/'userdata').iterdir():
    folder = account/'743890'
    if folder.is_dir():
        extra.extend(f for f in folder.rglob('*') if f.is_file())
extras = []
for source in extra:
    relative = source.relative_to(STEAM.parents[2])
    target = WORK/'user_state_before'/relative
    target.parent.mkdir(parents=True, exist_ok=True)
    if not target.exists():
        shutil.copy2(source, target)
    extras.append({'source': str(source), 'backup': str(target), 'sha256': hashlib.sha256(target.read_bytes()).hexdigest()})
for mode in ('ver_buki_riko','ver_rin_nana'):
    for name in ('current_build.json','project.json'):
        source = ROOT/'projects'/mode/name
        target = WORK/'ps1_pointers_before'/mode/name
        target.parent.mkdir(parents=True, exist_ok=True)
        if not target.exists():
            shutil.copy2(source,target)
report = {'steam_root': str(STEAM), 'buildid': '21253628', 'originals': checks, 'user_state': extras,
          'permission_source': '사용자가 Steam 이식을 본격적으로 시작하고 가능한 기능을 최대한 구현하도록 요청함.',
          'assignment': {'japanese': 'ver_rin_nana', 'english': 'ver_buki_riko'},
          'scope': '로컬 변환·설치 적용·실행 검증. 원본 백업과 PS1 결과 보존. 외부 공개/배포 제외.'}
(WORK/'backup_manifest.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print({'backed_up': len(checks), 'bytes': sum(r['size'] for r in checks), 'user_state_files':len(extras)})
