"""독립 감사된 두 모드 보스 음성 복구본을 활성 포인터에 적용한다."""
import json
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.restore_boss_intro_voices import PARENTS, FULL_OUTPUT_NAME, require
from scripts.project import working_cue
from src.psx_disc import file_hash

WORK = ROOT / 'work/boss_voice_restore_20261105'


def write(path, obj):
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + '\n', 'utf8')


def main():
    audit = json.loads((WORK / 'audit/final_independent.json').read_text('utf8'))
    require(audit['passed'], 'Independent final audit required')
    sdk = json.loads((WORK / 'calls/native_combat_sdk.json').read_text('utf8'))
    require(sdk['passed'] and not sdk['native_sdk_mocked']
            and sdk['all_bank2_regression_commands'] == 558 and sdk['all_wave_addresses_checked'] == 114,
            'Full native SDK regression required')
    baseline = json.loads((WORK / 'audit/protection_before.json').read_text('utf8'))
    dest = WORK / 'application'
    require(not dest.exists(), 'Already activated')
    mutable = {f'projects/{mode}/{name}' for mode in PARENTS
               for name in ('current_build.json', 'project.json')}
    for rel, info in baseline['files'].items():
        require(file_hash(ROOT / rel) == info['sha256'], 'File changed during preparation: ' + rel)
    pending, result = {}, {}
    for mode, (stem, expected) in PARENTS.items():
        folder = ROOT / 'projects' / mode
        old = json.loads((folder / 'current_build.json').read_text('utf8'))
        config = json.loads((folder / 'project.json').read_text('utf8'))
        require(old['sha256'] == config['latest_integrated_bin_sha256'] == expected,
                'Active parent changed')
        build = ROOT / 'out' / mode / FULL_OUTPUT_NAME
        m = json.loads((build / 'manifest.json').read_text('utf8'))
        actual = file_hash(build / (stem + '.bin'))
        require(actual == m['modified_bin']['sha256'] == audit['projects'][mode]['bin_sha256']
                and m['parent_sha256'] == expected, 'Final image differs from audited image')
        require({name: check['after'] for name, check in m['combat_checks'].items()} == sdk['resource_sha256'][mode],
                'Native SDK evidence targets different combat resources')
        parent_cue = ROOT / 'out' / mode / 'sprite_consistency_20261105_v1' / (stem + '.cue')
        cue = build / (stem + '.cue')
        require(cue.read_text('ascii') == working_cue(parent_cue.read_text('ascii'), stem + '.bin'),
                'CUE track structure differs')
        old.update(task='boss_voice_restoration', stage='BOSS_VOICES_APPLIED_REVIEW',
                   build=build.relative_to(ROOT).as_posix(), cue=cue.relative_to(ROOT).as_posix(),
                   sha256=actual, status_report='docs/BOSS_VOICE_RESTORATION.md',
                   boss_voice_report='docs/BOSS_VOICE_RESTORATION.md',
                   boss_voice_user_accepted=False, user_accepted=False,
                   current_session=None, running_bin_sha256=None,
                   current_runtime_state='새 보스 음성 CUE 활성화. 기존 F1과 메모리카드 보존.',
                   runtime_verification_scope='전체 자원/섹터·native 개전 및 전투 호출 검사. 전 보스 실제 청취 미검증.',
                   previous_pointer=(dest / mode / 'current_build.json').relative_to(ROOT).as_posix(),
                   next_action='새 CUE로 부팅하고 게임 내 메모리카드로 진행. 과거 F3 음향/코드 캐시는 사용하지 않음.')
        config.update(active_task='boss_voice_restoration', active_substage='BOSS_VOICES_APPLIED_REVIEW',
                      latest_integrated_build=build.relative_to(ROOT).as_posix(),
                      latest_integrated_bin_sha256=actual,
                      boss_voice_report='docs/BOSS_VOICE_RESTORATION.md')
        pending[mode] = (old, config)
        result[mode] = {'cue': old['cue'], 'sha256': actual}
    dest.mkdir()
    for mode in PARENTS:
        (dest / mode).mkdir()
        for name in ('current_build.json', 'project.json'):
            shutil.copyfile(ROOT / 'projects' / mode / name, dest / mode / name)
    for mode, (current, config) in pending.items():
        write(ROOT / 'projects' / mode / 'current_build.json', current)
        write(ROOT / 'projects' / mode / 'project.json', config)
    preserved = {}
    for rel, info in baseline['files'].items():
        if rel not in mutable:
            require(file_hash(ROOT / rel) == info['sha256'], 'Protected file changed: ' + rel)
            preserved[rel] = info['sha256']
    write(dest / 'applied.json', {'passed': True, 'projects': result,
          'preserved_files': preserved, 'updated_metadata': sorted(mutable),
          'originals_modified': False, 'F1_written': False, 'cards_written': False,
          'emulator_input_sent': False, 'user_accepted': False})
    print(json.dumps({'applied': result, 'protected_files': len(preserved)}))


if __name__ == '__main__':
    main()
