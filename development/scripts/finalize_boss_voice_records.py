"""활성 복구본의 부팅 범위와 미검증 항목을 메타데이터에 연결한다."""
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.restore_boss_intro_voices import PARENTS, FULL_OUTPUT_NAME, require
from src.psx_disc import file_hash


def main():
    work = ROOT / 'work/boss_voice_restore_20261105'
    app = json.loads((work / 'application/applied.json').read_text('utf8'))
    require(app['passed'], 'Activation missing')
    result = {}
    for mode, (stem, _) in PARENTS.items():
        boot_path = work / 'runtime' / (mode + '_boot.json')
        boot = json.loads(boot_path.read_text('utf8'))
        current_path = ROOT / 'projects' / mode / 'current_build.json'
        current = json.loads(current_path.read_text('utf8'))
        build = ROOT / 'out' / mode / FULL_OUTPUT_NAME
        require(boot['passed'] and boot['bin_sha256'] == current['sha256'] == app['projects'][mode]['sha256']
                == file_hash(build / (stem + '.bin')), 'Runtime/active disc mismatch')
        close = json.loads((ROOT / boot['session'] / 'close.local.json').read_text('utf8'))
        require(close['exited'], 'Test emulator still running')
        current.update(fresh_boot_boss_code_verified=True, boss_full_gameplay_verified=False,
                       boss_voice_listening_verified=False,
                       boss_boot_report=boot_path.relative_to(ROOT).as_posix(),
                       last_test_session=boot['session'], current_session=None, running_bin_sha256=None,
                       current_runtime_state='새 CUE 부팅과 RAM 코드 상주 확인 후 정상 종료. 기존 F1/사용자 카드 보존.')
        current_path.write_text(json.dumps(current, ensure_ascii=False, indent=2) + '\n', 'utf8')
        manifest_path = build / 'manifest.json'
        manifest = json.loads(manifest_path.read_text('utf8'))
        manifest.update(fresh_boot_code_verified=True, boss_voice_listening_verified=False,
                        boss_boot_report=boot_path.relative_to(ROOT).as_posix(),
                        independent_audit='work/boss_voice_restore_20261105/audit/final_independent.json',
                        native_combat_sdk='work/boss_voice_restore_20261105/calls/native_combat_sdk.json')
        manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', 'utf8')
        result[mode] = {'sha256': current['sha256'], 'pointer': current_path.relative_to(ROOT).as_posix(),
                        'fresh_boot_code_verified': True, 'all_bosses_heard': False, 'test_session_closed': True}
    for rel, expected in app['preserved_files'].items():
        require(file_hash(ROOT / rel) == expected, 'Protected file changed: ' + rel)
    cards = json.loads((work / 'runtime/test_cards_before.json').read_text('utf8'))
    require(all(file_hash(ROOT / r['path']) == r['sha256'] for r in cards), 'Isolated test card changed')
    final = {'passed': True, 'projects': result, 'protected_files': len(app['preserved_files']),
              'isolated_test_cards_preserved': len(cards), 'all_test_emulators_normally_closed': True}
    (work / 'application/final_verification.json').write_text(json.dumps(final, ensure_ascii=False, indent=2) + '\n', 'utf8')
    print(json.dumps(final))


if __name__ == '__main__':
    main()
