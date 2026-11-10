"""오래된 출력 BIN을 검증 가능한 원시 섹터 차이 ZIP으로 보관한다. 원본/아트는 보존."""
import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
SOURCE = 'MegaMan X4.bin'
SOURCE_HASH = '3ceab06ac99add4035f912188bcbf5b16c02056f46a33d38ff0c8dbce6cb613b'
SECTOR = 2352
CHUNK = SECTOR * 1024


def digest(path):
    with path.open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()


def safe_path(root, relative, output=False):
    parts = PurePosixPath(relative)
    if '\\' in relative or ':' in relative or parts.is_absolute() or '..' in parts.parts:
        raise ValueError('Unsafe relative path')
    if output and parts.parts[:2] not in (('out', 'ver_buki_riko'), ('out', 'ver_rin_nana')):
        raise ValueError('Only project output files are allowed')
    p = root
    for component in parts.parts:
        p = p / component
        if p.exists() or p.is_symlink():
            s = p.lstat()
            if p.is_symlink() or getattr(s, 'st_file_attributes', 0) & 0x400:
                raise ValueError('Links/junctions are forbidden')
            if p.is_file() and s.st_nlink != 1:
                raise ValueError('Hard links are forbidden')
    if not p.resolve().is_relative_to(root.resolve()):
        raise ValueError('Path escapes workspace')
    return p


def stamp(path):
    s = path.stat()
    return s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns, s.st_nlink


def reconstruct(root, archive, sink=None, required_source_hash=SOURCE_HASH):
    """항상 원본/페이로드/복원 해시를 검증한다. sink가 없으면 쓰지 않고 검증만 한다."""
    with zipfile.ZipFile(archive) as z:
        if sorted(z.namelist()) != ['metadata.json', 'sectors.bin']:
            raise ValueError('Unexpected archive entries')
        if z.getinfo('metadata.json').file_size > 16 * 1024 * 1024:
            raise ValueError('Oversized metadata')
        m = json.loads(z.read('metadata.json'))
        if m['format'] != 'x4-raw-sector-delta-v1' or m['sector_size'] != SECTOR:
            raise ValueError('Unsupported archive format')
        if m['source_sha256'] != required_source_hash or m['source'] != SOURCE:
            raise ValueError('Unsupported original')
        source = safe_path(root, m['source'])
        safe_path(root, m['target'], output=True)
        if source.stat().st_size != m['size'] or m['size'] % SECTOR:
            raise ValueError('Invalid image size')
        lbas = m['lbas']
        if (not isinstance(lbas, list) or any(type(x) is not int for x in lbas)
                or lbas != sorted(set(lbas))
                or any(x < 0 or x >= m['size'] // SECTOR for x in lbas)
                or z.getinfo('sectors.bin').file_size != len(lbas) * SECTOR):
            raise ValueError('Invalid sector list/payload size')
        source_hash = hashlib.sha256()
        target_hash = hashlib.sha256()
        cursor = 0
        with source.open('rb') as f, z.open('sectors.bin') as payload:
            for base in range(0, m['size'] // SECTOR, 1024):
                block = f.read(CHUNK)
                source_hash.update(block)
                patched = bytearray(block)
                while cursor < len(lbas) and lbas[cursor] < base + len(block) // SECTOR:
                    off = (lbas[cursor] - base) * SECTOR
                    sector = payload.read(SECTOR)
                    if len(sector) != SECTOR:
                        raise ValueError('Truncated sector')
                    patched[off:off + SECTOR] = sector
                    cursor += 1
                target_hash.update(patched)
                if sink is not None:
                    sink.write(patched)
        if source_hash.hexdigest() != required_source_hash:
            raise ValueError('Original hash mismatch')
        if target_hash.hexdigest() != m['target_sha256']:
            raise ValueError('Restored image hash mismatch')
        return m


def compact(root, relative, expected_hash, required_source_hash=SOURCE_HASH, *, remove_full=True):
    target = safe_path(root, relative, output=True)
    source = safe_path(root, SOURCE)
    if target.suffix.lower() != '.bin' or target == source:
        raise ValueError('Only separate BIN outputs may be compacted')
    if target.stat().st_size != source.stat().st_size or target.stat().st_size % SECTOR:
        raise ValueError('Different image size')
    before = stamp(target)
    source_before = stamp(source)
    archive = target.with_suffix(target.suffix + '.delta.zip')
    safe_path(root, archive.relative_to(root).as_posix(), output=True)
    if archive.exists():
        raise FileExistsError(archive)
    lbas = []
    payload = bytearray()
    sh = hashlib.sha256()
    th = hashlib.sha256()
    with source.open('rb') as a, target.open('rb') as b:
        base = 0
        while original := a.read(CHUNK):
            modified = b.read(len(original))
            if len(modified) != len(original):
                raise ValueError('Target changed during read')
            sh.update(original)
            th.update(modified)
            if original != modified:
                for off in range(0, len(original), SECTOR):
                    if original[off:off + SECTOR] != modified[off:off + SECTOR]:
                        lbas.append(base + off // SECTOR)
                        payload.extend(modified[off:off + SECTOR])
            base += len(original) // SECTOR
    if sh.hexdigest() != required_source_hash or th.hexdigest() != expected_hash:
        raise ValueError('Source/target hash mismatch; nothing removed')
    m = dict(format='x4-raw-sector-delta-v1', source=SOURCE,
             source_sha256=required_source_hash, target=relative,
             target_sha256=expected_hash, size=before[2], sector_size=SECTOR, lbas=lbas)
    with zipfile.ZipFile(archive, 'x', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        z.writestr('metadata.json', json.dumps(m, indent=2))
        z.writestr('sectors.bin', payload)
    verified = reconstruct(root, archive, required_source_hash=required_source_hash)
    if stamp(target) != before or stamp(source) != source_before:
        raise ValueError('Input changed during archival; nothing removed')
    # 검증된 정확한 단일 파일만 삭제한다. 디렉터리 삭제나 쉘 삭제는 사용하지 않는다.
    if remove_full:
        safe_path(root, relative, output=True).unlink()
    return dict(target=relative, target_sha256=verified['target_sha256'],
                archive=archive.relative_to(root).as_posix(), archive_sha256=digest(archive),
                original_bytes=before[2], archive_bytes=archive.stat().st_size,
                changed_sectors=len(lbas), restored_hash_verified=True, full_bin_removed=remove_full)


def restore(root, archive, required_source_hash=SOURCE_HASH):
    with zipfile.ZipFile(archive) as z:
        m = json.loads(z.read('metadata.json'))
    target = safe_path(root, m['target'], output=True)
    if target.exists():
        raise FileExistsError(target)
    temp = target.with_suffix(target.suffix + '.restoring')
    safe_path(root, temp.relative_to(root).as_posix(), output=True)
    # 실패한 후보는 남긴다. 기존 파일에 덧붙이거나 덮어쓰지 않는다.
    with temp.open('xb') as f:
        reconstruct(root, archive, f, required_source_hash)
        f.flush()
        os.fsync(f.fileno())
    if target.exists():
        raise FileExistsError(target)
    # Windows rename refuses an existing destination; CLI is Windows-only.
    temp.rename(target)
    return target


def protected_directories(root):
    p = json.loads((root / 'projects/ver_buki_riko/current_build.json').read_text(encoding='utf-8'))
    keep = {p[k].replace('\\','/') for k in ('build','previous_build') if p.get(k)}
    # Legacy feature pointers can lag behind the current integrated release.
    project = root / 'projects/ver_buki_riko/project.json'
    if project.exists():
        latest = json.loads(project.read_text(encoding='utf-8')).get('latest_integrated_build')
        if latest: keep.add(latest.replace('\\','/'))
    release = root / 'projects/ver_buki_riko/final_release.json'
    if release.exists():
        r = json.loads(release.read_text(encoding='utf-8'))
        keep.update(x.replace('\\','/') for x in r['protected_build_directories'])
    return keep


def plan(root):
    keep = protected_directories(root)
    entries = []
    for target in sorted((root / 'out/ver_buki_riko').rglob('*.bin')):
        if target.stat().st_size < 500_000_000:
            continue
        relative = target.relative_to(root).as_posix()
        safe_path(root, relative, output=True)
        if target.parent.relative_to(root).as_posix() in keep:
            continue
        m = json.loads((target.parent / 'manifest.json').read_text(encoding='utf-8'))
        if m['source_sha256'] != SOURCE_HASH:
            raise ValueError(f'Unsupported manifest source: {relative}')
        info = m['roundtrip'] if target.name == 'roundtrip.bin' else m['modified_bin']
        entries.append(dict(path=relative, sha256=info['sha256'], size=target.stat().st_size))
    return dict(keep=sorted(keep), targets=entries, removable_bytes=sum(x['size'] for x in entries))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['plan', 'compact', 'restore', 'verify'])
    parser.add_argument('--archive', type=Path)
    parser.add_argument('--report', type=Path)
    args = parser.parse_args()
    if args.action in ('restore', 'verify'):
        if not args.archive:
            parser.error('--archive required')
        a = safe_path(ROOT, args.archive.resolve().relative_to(ROOT).as_posix(), output=True)
        result = restore(ROOT, a) if args.action == 'restore' else reconstruct(ROOT, a)
        print(result if args.action == 'restore' else json.dumps({k: v for k, v in result.items() if k != 'lbas'}))
        return
    planned = plan(ROOT)
    if not args.report:
        parser.error('--report required')
    args.report.parent.mkdir(parents=True, exist_ok=True)
    with args.report.open('x', encoding='utf-8') as f:
        if args.action == 'plan':
            json.dump(planned, f, indent=2)
        else:
            sys.path.insert(0, str(ROOT))
            from scripts.emulator_session import working_instances
            if working_instances(include_original=True):
                raise RuntimeError('Close emulators before compacting game outputs')
            for i, entry in enumerate(planned['targets'], 1):
                result = compact(ROOT, entry['path'], entry['sha256'])
                f.write(json.dumps(result) + '\n')
                f.flush()
                os.fsync(f.fileno())
                print(f"{i}/{len(planned['targets'])} archived {entry['path']}", flush=True)
    print(json.dumps({'count': len(planned['targets']), 'bytes': planned['removable_bytes'], 'keep': planned['keep']}))


if __name__ == '__main__':
    main()
