"""버전별 입력 검증 및 수정하지 않은 기준 실행 사본 준비. 패처는 아니다."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import shutil

ROOT = Path(__file__).resolve().parents[1]
PROJECTS = ('ver_buki_riko', 'ver_rin_nana')


def digest(path):
    with path.open('rb') as stream:
        if hasattr(hashlib, 'file_digest'):
            return hashlib.file_digest(stream, 'sha256').hexdigest()
        result = hashlib.sha256()
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            result.update(chunk)
        return result.hexdigest()


def checked_path(root, relative, allowed):
    path = Path(relative)
    if path.is_absolute() or '..' in path.parts:
        raise ValueError('Relative project path required')
    resolved = (root/path).resolve()
    if not resolved.is_relative_to(allowed.resolve()):
        raise ValueError('Path escaped the allowed project directory')
    return resolved


def load_project(root, project_id):
    if project_id not in PROJECTS:
        raise ValueError('Unknown project')
    path = root/'projects'/project_id/'project.json'
    project = json.loads(path.read_text(encoding='utf-8'))
    if project['project_id'] != project_id or project['schema_version'] != 1:
        raise ValueError('Project identity/schema mismatch')
    references = project['references']
    if len({r['task_id'] for r in references}) != len(references):
        raise ValueError('Duplicate task ID')
    if {r['slot'] for r in references} != {'zero','x_base','x_fourth_armor','x_ultimate_armor'} or len(references) != 4:
        raise ValueError('Expected one reference for each of four slots')
    for ref in references:
        checked_path(root, ref['path'], root/'character'/project_id)
    return project


def inspect_references(root, project):
    from PIL import Image
    results = []
    for ref in project['references']:
        path = checked_path(root, ref['path'], root/'character'/project['project_id'])
        actual = digest(path)
        if actual != ref['sha256']:
            raise ValueError('Reference hash changed: '+ref['path'])
        with Image.open(path) as image:
            image.load()
            results.append({**ref, 'size': path.stat().st_size, 'width': image.width,
                            'height': image.height, 'mode': image.mode, 'format': image.format})
    return results


def validate_bin(source, expected):
    actual = digest(source)
    if actual != expected:
        raise ValueError('Unsupported source BIN hash')
    return actual


def working_cue(text, filename):
    # 이번에 제공된 트랙 선언만 지원한다. BIN 파일명 이외의 트랙 정보를 추측하지 않는다.
    if not re.fullmatch(r'FILE "[^"\r\n]+" BINARY\r?\n\s+TRACK 01 MODE2/2352\r?\n\s+INDEX 01 00:00:00\s*', text):
        raise ValueError('Unsupported CUE layout')
    if not re.fullmatch(r'[A-Za-z0-9_.-]+\.bin', filename):
        raise ValueError('Unsafe output BIN name')
    return re.sub(r'^FILE "[^"\r\n]+"', 'FILE "'+filename+'"', text, count=1)


def new_run(root, project_id, kind):
    parent = root/'work'/project_id/kind
    if not parent.resolve().is_relative_to(root.resolve()):
        raise ValueError('Output directory escaped workspace')
    path = parent/datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    path.mkdir(parents=True, exist_ok=False)
    return path


def write_json(path, content):
    with path.open('x', encoding='utf-8') as stream:
        json.dump(content, stream, indent=2, ensure_ascii=False)


def prepare(root, project):
    references = inspect_references(root, project)
    source = checked_path(root, project['source_bin'], root)
    source_cue = checked_path(root, project['source_cue'], root)
    before = validate_bin(source, project['source_sha256'])
    cue = working_cue(source_cue.read_bytes().decode('utf-8-sig'), 'baseline.bin')
    emulator = root/'ePSXe2018'
    # 복사 원본에 링크가 있으면 다른 입력이 섞이지 않도록 중단한다.
    members = list(emulator.rglob('*'))
    if any(p.is_symlink() or p.is_junction() for p in [emulator]+members):
        raise ValueError('Linked emulator inputs are not supported')
    if not (emulator/'ePSXe.exe').is_file() or not (emulator/'bios/SCPH1001.BIN').is_file():
        raise ValueError('Emulator/BIOS missing')
    if shutil.disk_usage(root).free < source.stat().st_size + 128*1024*1024:
        raise ValueError('Insufficient space for a baseline copy')
    out = new_run(root, project['project_id'], 'baseline')
    target = out/'baseline.bin'
    # x 모드와 새 실행 폴더로 원본·기존 출력과의 동일 파일 충돌을 차단한다.
    with source.open('rb') as src, target.open('xb') as dst:
        shutil.copyfileobj(src, dst, 1024*1024)
    if digest(target) != before or digest(source) != before:
        raise ValueError('Source/copy changed while preparing baseline')
    with (out/'baseline.cue').open('x', encoding='ascii', newline='') as stream:
        stream.write(cue)
    shutil.copytree(emulator, out/'emulator')
    write_json(out/'manifest.json', {
        'project_id': project['project_id'], 'active_task': project['active_task'],
        'source_path': str(source), 'source_sha256': before,
        'baseline_sha256': digest(target), 'source_cue_sha256': digest(source_cue),
        'working_cue_sha256': digest(out/'baseline.cue'), 'game_data_modified': False,
        'boot_id': project['boot_id'], 'references': references,
        'emulator_sha256': digest(out/'emulator/ePSXe.exe'),
        'bios_sha256': digest(out/'emulator/bios/SCPH1001.BIN'),
        'runtime_verified': False})
    return out


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('inspect', 'prepare'))
    parser.add_argument('--project', choices=PROJECTS, required=True)
    args = parser.parse_args()
    project = load_project(ROOT, args.project)
    if args.action == 'inspect':
        refs = inspect_references(ROOT, project)
        out = new_run(ROOT, args.project, 'inspection')
        write_json(out/'references.json', {'project_id': args.project, 'references': refs})
        print(json.dumps({'project_id': args.project, 'references_verified': len(refs), 'report': str(out)},ensure_ascii=False))
    else:
        out = prepare(ROOT, project)
        print(json.dumps({'project_id': args.project, 'baseline': str(out), 'game_data_modified': False},ensure_ascii=False))


if __name__ == '__main__':
    main()
