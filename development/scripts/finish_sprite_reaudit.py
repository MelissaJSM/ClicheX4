"""최종 검증 범위와 미완료 실기, 원본/카드 보존 결과를 현재 포인터에 기록한다."""
import json
from datetime import datetime, timezone
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.audit_sprite_reaudit_source import WORK, EXPECTED
from scripts.build_hurt_capsule_fix import require, write_json
from src.psx_disc import file_hash


def main():
    target = WORK / 'final_validation.json'
    require(not target.exists(), 'Final record already exists')
    applied = json.loads((WORK / 'application/applied.json').read_text('utf8'))
    browser = json.loads((WORK / 'album_browser_checks.json').read_text('utf8'))
    playback = json.loads((WORK / 'album_playback_checks.json').read_text('utf8'))
    independent = json.loads((WORK / 'audit/final_independent.json').read_text('utf8'))
    require(browser['passed'] and playback['passed'] and independent['passed'], 'Incomplete verification')
    keyboard = json.loads((WORK / 'keyboard_setting.json').read_text('utf8'))
    require(keyboard['restored'], 'Temporary input setting not restored')
    import winreg
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, keyboard['key']) as key:
        require(winreg.QueryValueEx(key, keyboard['name']) == (keyboard['original'], keyboard['type']), 'Input registry differs')
    process_list = subprocess.check_output(['tasklist', '/FI', 'IMAGENAME eq ePSXe.exe', '/FO', 'CSV', '/NH'], text=True)
    require('epsxe.exe' not in process_list.lower(), 'An emulator is still running')
    protected = {}
    for path, expected in applied['preserved_files'].items():
        require(file_hash(ROOT / path) == expected, 'Protected input changed: ' + path)
        protected[path] = expected
    cards = json.loads((WORK / 'runtime_cards.json').read_text('utf8'))
    card_checks = []
    for mode, rows in cards['projects'].items():
        for item in rows.values():
            actual = file_hash(ROOT / item['path'])
            require(actual == item['sha256'], 'Isolated card changed')
            card_checks.append({'path': item['path'], 'sha256': actual, 'unchanged': True})
    sessions = []
    for name in ('20261105T230053467328Z', '20261105T230541123905Z', '20261105T230624425994Z'):
        folder = ROOT / 'work/ver_rin_nana/emulator_sessions' / name
        rec = json.loads((folder / 'session.local.json').read_text('utf8'))
        require(rec['bin_sha256'] == applied['projects']['ver_rin_nana']['sha256'], 'Unexpected runtime disc')
        sessions.append({'session': folder.relative_to(ROOT).as_posix(), 'pid': rec['pid'], 'sha256': rec['bin_sha256'],
                         'not_running_at_finalization': True, 'save_state_loaded_by_automation': False})
    runtime = {'sessions': sessions, 'boot_title_and_automatic_demo_observed': True,
               'changed_ultimate_poses_verified': False, 'cause_confirmed': False,
               'limitation': '메뉴 입력이 안정적으로 전달되지 않아 검증용 카드 불러오기와 변경 자세 실기에 도달하지 못했다. 임시 PADApiType1 변경은 복원했고 모든 시험 프로세스 종료를 확인했다.',
               'RAM_or_state_written': False, 'F1_F3_sent': False,
               'evidence': ['work/ver_rin_nana/korean_runtime/20261105T230200626565Z/evidence.json',
                            'work/ver_rin_nana/korean_runtime/20261105T230642993940Z/evidence.json']}
    for mode in EXPECTED:
        pointer_path = ROOT / 'projects' / mode / 'current_build.json'
        config_path = ROOT / 'projects' / mode / 'project.json'
        pointer = json.loads(pointer_path.read_text('utf8'))
        config = json.loads(config_path.read_text('utf8'))
        require(pointer['sha256'] == config['latest_integrated_bin_sha256'] == applied['projects'][mode]['sha256'], 'Current pointer changed')
        pointer.update(sprite_reaudit_runtime_verified=False, sprite_reaudit_validation='work/sprite_reaudit_20261106/final_validation.json',
                       sprite_reaudit_animation_verified=True, current_session=None, running_bin_sha256=None,
                       current_runtime_state='시험 창 종료·입력 설정 복원. 변경 모션 실기는 미완료이며 새 CUE와 게임 내 카드로 확인 필요.',
                       runtime_verification_scope='전체 정지 시트 검토, 네이티브 디코더·파츠 조합·120변경 이미지의 원래 순서 재생 통과. 나나 새 CUE 부팅 관찰. 전수 실기 미완료.',
                       next_action='새 모음집/현재 CUE에서 시부키 얼티밋 이동·공중·대시, 나나 부분 포스/프로스트 자세 확인. 남은 소매·둥근 공중발 미술 후보 검토.')
        config.update(sprite_reaudit_validation='work/sprite_reaudit_20261106/final_validation.json')
        write_json(pointer_path, pointer)
        write_json(config_path, config)
    report = {'static_and_simulation_passed': True, 'all_motion_runtime_verified': False,
              'user_accepted': False, 'utc': datetime.now(timezone.utc).isoformat(),
              'projects': applied['projects'], 'independent_audit_sha256': file_hash(WORK / 'audit/final_independent.json'),
              'album_sha256': file_hash(ROOT / 'out/sprite_reaudit_20261106/ALL_SPRITES_CURRENT.html'),
              'browser_checks': 'work/sprite_reaudit_20261106/album_browser_checks.json',
              'playback_checks': 'work/sprite_reaudit_20261106/album_playback_checks.json',
              'protected_files': protected, 'isolated_cards': card_checks, 'runtime': runtime,
              'keyboard_setting_restored': True, 'all_trial_processes_closed': True}
    write_json(target, report)
    print(json.dumps({'static_simulation_passed': True, 'protected': len(protected), 'isolated_cards_unchanged': len(card_checks),
                      'changed_pose_runtime_verified': False, 'all_trial_processes_closed': True}))


if __name__ == '__main__':
    main()
