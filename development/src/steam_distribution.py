"""Portable patch installer core. Standard library only; never modifies saves/EXE."""
from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import tempfile
import time
import uuid
import zipfile
import zlib

SCHEMA = 'clichex4-steam-xor-v1'
STATE_DIR = '.clichex4'
LIMIT = 128 * 1024 * 1024


def digest(data):
    return hashlib.sha256(data).hexdigest()


def json_bytes(value):
    return (json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode('utf8')


def safe_path(root, relative):
    if not isinstance(relative, str) or '\\' in relative or ':' in relative:
        raise ValueError('잘못된 패키지 경로입니다.')
    rel = PurePosixPath(relative)
    if rel.is_absolute() or any(p in ('', '.', '..') for p in relative.split('/')):
        raise ValueError('패키지 경로가 지정 폴더를 벗어납니다.')
    root = Path(root).resolve()
    target = root.joinpath(*rel.parts)
    if not target.resolve().is_relative_to(root):
        raise ValueError('폴더 밖으로 연결된 경로는 변경하지 않습니다.')
    cursor = target
    while cursor != root:
        if cursor.is_symlink() or (cursor.exists() and cursor.is_junction()):
            raise ValueError('링크/정션으로 연결된 파일은 변경하지 않습니다.')
        cursor = cursor.parent
    return target


def encode_delta(before, after):
    size = max(len(before), len(after))
    if size > LIMIT:
        raise ValueError('Patch input exceeds bound')
    delta = (int.from_bytes(before, 'little') ^ int.from_bytes(after, 'little')).to_bytes(size, 'little')
    return zlib.compress(delta, 9)


def decode_delta(before, compressed, row):
    if digest(before) != row['source_sha256'] or len(before) != row['source_size']:
        raise ValueError('원본 파일이 지원 버전과 다릅니다: ' + row['source'])
    size = max(row['source_size'], row['size'])
    if not 0 < size <= LIMIT or digest(compressed) != row['patch_sha256']:
        raise ValueError('패치 데이터가 손상되었습니다: ' + row['target'])
    dec = zlib.decompressobj()
    delta = dec.decompress(compressed, size + 1)
    if len(delta) != size or not dec.eof or dec.unused_data or dec.unconsumed_tail:
        raise ValueError('패치 압축 범위가 잘못되었습니다.')
    result = (int.from_bytes(before, 'little') ^ int.from_bytes(delta, 'little')).to_bytes(size, 'little')[:row['size']]
    if digest(result) != row['sha256']:
        raise ValueError('패치 결과 검증에 실패했습니다: ' + row['target'])
    return result


def atomic_write(path, raw):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp = tempfile.mkstemp(prefix='.cliche-', suffix='.tmp', dir=path.parent)
    try:
        with os.fdopen(fd, 'wb') as f:
            f.write(raw)
            f.flush()
            os.fsync(f.fileno())
        os.replace(temp, path)
    finally:
        if os.path.exists(temp):
            os.unlink(temp)


class Package:
    def __init__(self, archive, expected_archive_sha256=None):
        self.archive = Path(archive)
        if expected_archive_sha256 and digest(self.archive.read_bytes()) != expected_archive_sha256:
            raise ValueError('배포 패키지 검사에 실패했습니다. ZIP을 다시 풀어 주세요.')
        with zipfile.ZipFile(self.archive) as z:
            infos = z.infolist()
            if len({i.filename.casefold() for i in infos}) != len(infos):
                raise ValueError('중복 패키지 경로입니다.')
            if any(i.file_size > LIMIT for i in infos):
                raise ValueError('Package member exceeds bound')
            self.manifest = json.loads(z.read('manifest.json'))
            m = self.manifest
            if m['schema'] != SCHEMA or m['appid'] != 743890:
                raise ValueError('지원하지 않는 패키지입니다.')
            self.rows = m['files']
            if not 1 <= len(self.rows) <= 512:
                raise ValueError('Unexpected file count')
            targets = set()
            for row in self.rows:
                for key in ('source', 'target', 'patch'):
                    safe_path(Path.cwd(), row[key])
                rel = row['target']
                if not rel.startswith(('nativeDX10/X4/', 'nativeDX10/RXC1/romPC/')):
                    raise ValueError('게임 자원 밖의 변경 요청입니다.')
                if not rel.endswith(('.arc', '.xsew', '.sbkr', '.srqr', '.stqr', '.sngw')):
                    raise ValueError('지원하지 않는 게임 자원 형식입니다.')
                if not row['source'].startswith('nativeDX10/') or row['source'] == 'RXC1.exe':
                    raise ValueError('잘못된 원본 자원입니다.')
                if rel.casefold() in targets:
                    raise ValueError('중복 설치 대상입니다.')
                targets.add(rel.casefold())
                if not 0 < row['size'] <= LIMIT or not 0 < row['source_size'] <= LIMIT:
                    raise ValueError('잘못된 파일 크기입니다.')
                if row['original_sha256'] is not None and (row['source'] != rel or row['original_sha256'] != row['source_sha256']):
                    raise ValueError('원본 복원 정보가 일치하지 않습니다.')
                z.getinfo(row['patch'])
            expected = {'manifest.json'} | {r['patch'] for r in self.rows}
            if set(z.namelist()) != expected:
                raise ValueError('예상하지 않은 파일이 패키지에 있습니다.')

    def validate_root(self, root):
        root = Path(root).resolve()
        exe = safe_path(root, 'RXC1.exe')
        if not exe.is_file() or digest(exe.read_bytes()) != self.manifest['exe_sha256']:
            raise ValueError('지원하는 원본 RXC1.exe가 없습니다. Steam 레거시 컬렉션 1의 게임 폴더를 선택해 주세요.')
        return root

    def _state(self, root):
        p = safe_path(root, STATE_DIR + '/state.json')
        if not p.exists():
            return None
        state = json.loads(p.read_text('utf8'))
        if state.get('schema') != SCHEMA or state.get('release') not in [self.manifest['release'], *self.manifest.get('upgrade_from', [])]:
            raise ValueError('다른 패치 버전의 백업입니다. 해당 버전의 복원 도구를 먼저 사용해 주세요.')
        return state

    def inspect(self, root, progress=lambda *_: None):
        root = self.validate_root(root)
        state = self._state(root)
        previous_release = state.get('release') if state else None
        if state and state.get('phase') == 'installing' and state.get('upgrade_source_release') in self.manifest.get('upgrade_from', []):
            previous_release = state['upgrade_source_release']
        report = []
        for i, row in enumerate(self.rows):
            path = safe_path(root, row['target'])
            value = digest(path.read_bytes()) if path.exists() else None
            if value == row['sha256'] == row['original_sha256']:
                status = 'unchanged'
            elif value == row['sha256']:
                status = 'installed'
            elif value == row['original_sha256']:
                status = 'original'
            elif state and value is not None and value == row.get('previous_sha256', {}).get(previous_release):
                status = 'previous'
            else:
                status = 'conflict'
            report.append({'target': row['target'], 'status': status, 'sha256': value})
            progress(i + 1, len(self.rows), '파일 확인')
        return {'installed': sum(r['status'] in ('installed','unchanged') for r in report),
                'original': sum(r['status'] in ('original','unchanged') for r in report),
                'unchanged': sum(r['status'] == 'unchanged' for r in report),
                'upgradable': sum(r['status'] == 'previous' for r in report),
                'conflicts': [r['target'] for r in report if r['status'] == 'conflict'],
                'total': len(report), 'files': report}

    def source_bytes(self, root, row):
        # Backups are always considered before a potentially patched live file.
        for rel in (STATE_DIR + '/original/' + row['source'], row['source']):
            p = safe_path(root, rel)
            if p.is_file():
                raw = p.read_bytes()
                if len(raw) == row['source_size'] and digest(raw) == row['source_sha256']:
                    return raw
        raise ValueError('지원 원본/백업을 찾을 수 없습니다: ' + row['source'])

    @contextmanager
    def lock(self, root):
        path = safe_path(root, STATE_DIR + '/installer.lock')
        path.parent.mkdir(exist_ok=True)
        # Windows byte-range locking is released by the OS even after a crash.
        with path.open('a+b') as f:
            f.seek(0)
            if os.name == 'nt':
                import msvcrt
                if not path.stat().st_size:
                    f.write(b'0'); f.flush(); f.seek(0)
                try:msvcrt.locking(f.fileno(), msvcrt.LK_NBLCK, 1)
                except OSError:raise ValueError('다른 설치/복원 작업이 실행 중입니다.')
            try:yield
            finally:
                if os.name == 'nt':
                    f.seek(0); msvcrt.locking(f.fileno(), msvcrt.LK_UNLCK, 1)

    def apply(self, root, restore=False, progress=lambda *_: None,
              running=lambda: False, before_commit=None):
        root = self.validate_root(root)
        if running():
            raise ValueError('게임을 종료한 뒤 설치/복원해 주세요.')
        with self.lock(root):
            previous = self._state(root)
            check = self.inspect(root)
            if check['conflicts']:
                raise ValueError('다른 수정본이나 손상된 파일을 덮어쓰지 않습니다:\n' + '\n'.join(check['conflicts'][:8]))
            if restore and not previous:
                if check['original'] == check['total']:
                    return {'action': 'restore', 'changed': 0, 'already_original': True}
                raise ValueError('이 설치 도구의 원본 백업이 없습니다. 기존 개발용 복원 도구를 사용해 주세요.')
            if not restore and check['installed'] == check['total']:
                return {'action': 'install', 'changed': 0, 'already_installed': True}
            required = sum(r['size'] + r['source_size'] for r in self.rows) * 2
            if shutil.disk_usage(root).free < required:
                raise ValueError('설치/복원을 위한 여유 공간이 부족합니다.')
            txn_rel = STATE_DIR + '/transactions/' + uuid.uuid4().hex
            txn = safe_path(root, txn_rel)
            txn.mkdir(parents=True)
            planned = []
            with zipfile.ZipFile(self.archive) as z:
                for i, row in enumerate(self.rows):
                    dest = safe_path(root, row['target'])
                    old = dest.read_bytes() if dest.exists() else None
                    source = self.source_bytes(root, row)
                    if not restore:
                        backup = safe_path(root, STATE_DIR + '/original/' + row['source'])
                        if backup.exists():
                            if digest(backup.read_bytes()) != row['source_sha256']:
                                raise ValueError('원본 백업이 손상되었습니다: ' + row['source'])
                        else:
                            atomic_write(backup, source)
                        new = decode_delta(source, z.read(row['patch']), row)
                    else:
                        new = source if row['original_sha256'] is not None else None
                    if old != new:
                        staged = safe_path(txn, f'new/{i:04d}.dat')
                        if new is not None:atomic_write(staged, new)
                        planned.append((dest, old, new, staged, row['target']))
                    progress(i + 1, len(self.rows), '복원 준비' if restore else '패치 검증·백업')
            state_path = safe_path(root, STATE_DIR + '/state.json')
            state = {'schema': SCHEMA, 'release': self.manifest['release'],
                     'phase': 'restoring' if restore else 'installing', 'transaction': txn_rel,
                     'created': time.strftime('%Y-%m-%dT%H:%M:%S')}
            if previous:
                previous_release = previous.get('upgrade_source_release', previous['release'])
                if previous_release in self.manifest.get('upgrade_from', []):
                    state['upgrade_source_release'] = previous_release
            atomic_write(state_path, json_bytes(state))
            committed = []
            try:
                if running():raise ValueError('게임이 실행되어 변경을 중단했습니다.')
                for i, (dest, old, new, staged, rel) in enumerate(planned):
                    if (dest.read_bytes() if dest.exists() else None) != old:
                        raise ValueError('설치 중 다른 프로그램이 파일을 변경했습니다: ' + rel)
                    if before_commit:before_commit(i, dest)
                    if new is None:
                        dest.unlink()
                    else:
                        dest.parent.mkdir(parents=True, exist_ok=True)
                        os.replace(staged, dest)
                    committed.append((dest, old, new))
                    if (dest.read_bytes() if dest.exists() else None) != new:
                        raise ValueError('설치 후 읽기 검증 실패: ' + rel)
                    progress(i + 1, len(planned), '원본 복원' if restore else '패치 적용')
                state['phase'] = 'restored' if restore else 'installed'
                atomic_write(state_path, json_bytes(state))
            except Exception:
                for dest, old, new in reversed(committed):
                    if (dest.read_bytes() if dest.exists() else None) != new:
                        raise ValueError('동시에 파일이 변경되어 자동 되돌리기를 멈췄습니다: ' + str(dest))
                    if old is None:
                        dest.unlink()
                    else:
                        atomic_write(dest, old)
                if previous:
                    atomic_write(state_path, json_bytes(previous))
                else:
                    state['phase'] = 'restored'
                    atomic_write(state_path, json_bytes(state))
                raise
            finally:
                # Remove only this transaction's known staged files. Never a
                # recursive removal derived from a package-provided path.
                for _, _, _, staged, _ in planned:
                    if staged.exists():staged.unlink()
            result = self.inspect(root)
            field = 'original' if restore else 'installed'
            if result[field] != result['total']:
                raise ValueError('최종 파일 검증 실패')
            return {'action': 'restore' if restore else 'install', 'changed': len(planned),
                    'verified': result['total'], 'save_files_written': False, 'exe_written': False}
