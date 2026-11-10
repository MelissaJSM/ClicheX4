"""새 부팅에서 읽은 RAM의 보스 개전 코드/표를 최종 디스크와 대조한다."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.restore_boss_intro_voices import PARENTS, FULL_OUTPUT_NAME, read_exe, require
from src.psx_disc import file_hash


def main(project, capture):
    capture = capture.resolve()
    require(capture.is_relative_to(ROOT / 'work' / project / 'korean_runtime'), 'Unexpected capture folder')
    record = json.loads((capture / 'evidence.json').read_text('utf8'))
    stem = PARENTS[project][0]
    build = ROOT / 'out' / project / FULL_OUTPUT_NAME
    game = build / (stem + '.bin')
    manifest = json.loads((build / 'manifest.json').read_text('utf8'))
    require(record['bin_sha256'] == file_hash(game) == manifest['modified_bin']['sha256'], 'Capture disc differs')
    session = Path(record['session'])
    session_record = json.loads((session / 'session.local.json').read_text('utf8'))
    require(session_record['pid'] == record['pid'] and not session_record['save_state_loaded'], 'Unexpected saved-state session')
    require(not record['process_memory_written'] and not record['keys_sent'], 'Capture was not read-only')
    require(len(record['ram_bases']) == 1, 'Ambiguous RAM snapshot')
    ram_path = capture / ('ram_' + str(record['ram_bases'][0]) + '.bin')
    ram = ram_path.read_bytes()
    exe, _ = read_exe(game)
    require(len(ram) == 0x200000, 'Truncated RAM')
    ranges = ((0x921E8, 240, 'boss intro and completion wait'),
              (0x105FC8, 39, '13 bosses x 3 XA track table'),
              (0x1663C, 128, 'XA request'),
              (0x1540C, 928, 'sound command dispatcher'))
    checked = []
    for at, size, label in ranges:
        payload = exe[at - 0x10000 + 2048:at - 0x10000 + 2048 + size]
        require(ram[at:at + size] == payload, 'Runtime differs from disc: ' + label)
        checked.append({'address': hex(0x80000000 + at), 'size': size, 'label': label,
                        'sha256': hashlib.sha256(payload).hexdigest()})
    require(ram[0x921F8:0x921FC] == bytes(4), 'Boss intro branch still suppressed')
    out = ROOT / 'work/boss_voice_restore_20261105/runtime'
    out.mkdir(exist_ok=True)
    path = out / (project + '_boot.json')
    require(not path.exists(), 'Runtime evidence already recorded')
    report = {'passed': True, 'project': project, 'bin_sha256': record['bin_sha256'],
              'session': session.relative_to(ROOT).as_posix(), 'pid': record['pid'],
              'capture': capture.relative_to(ROOT).as_posix(), 'RAM_sha256': file_hash(ram_path),
              'verified_code_and_tables': checked, 'fresh_boot_code_verified': True,
              'actual_boss_intro_heard': False, 'all_boss_gameplay_verified': False,
              'F1_F3_used': False, 'memory_written': False,
              'limitation': '부팅/메뉴 상태의 실제 코드 상주 증거. 보스 개전·전투 음성 청취 성공으로 확대하지 않음.'}
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', 'utf8')
    print(json.dumps({'passed': True, 'report': path.relative_to(ROOT).as_posix()}))


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--project', choices=PARENTS, required=True)
    p.add_argument('--capture', type=Path, required=True)
    a = p.parse_args()
    main(a.project, a.capture)
