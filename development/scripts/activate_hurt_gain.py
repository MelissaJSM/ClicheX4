"""감사된 두 모드 피격음 증폭본 적용. 미재현 캡슐 제보는 열린 상태로 유지한다."""
import json
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.build_hurt_capsule_fix import PARENTS, BUILD_NAME, WORK, require, write_json
from scripts.project import working_cue
from src.psx_disc import file_hash


def main():
    audit = json.loads((WORK / 'audit/final_independent.json').read_text('utf8'))
    require(audit['passed'], 'Independent final audit required')
    baseline = json.loads((WORK / 'audit/protection_before.json').read_text('utf8'))
    runtime = json.loads((WORK / 'runtime/boot_results.json').read_text('utf8'))
    dest = WORK / 'application'
    require(not dest.exists(), 'Already activated')
    for rel, info in baseline['files'].items():
        require(file_hash(ROOT / rel) == info['sha256'], 'Preparation baseline changed: ' + rel)
    mutable = {f'projects/{mode}/{name}' for mode in PARENTS
               for name in ('current_build.json', 'project.json')}
    pending, result = {}, {}
    for mode, (stem, parent_sha) in PARENTS.items():
        folder = ROOT / 'projects' / mode
        current = json.loads((folder / 'current_build.json').read_text('utf8'))
        config = json.loads((folder / 'project.json').read_text('utf8'))
        require(current['sha256'] == config['latest_integrated_bin_sha256'] == parent_sha,
                'Current parent changed')
        build = ROOT / 'out' / mode / BUILD_NAME
        manifest = json.loads((build / 'manifest.json').read_text('utf8'))
        check = audit['projects'][mode]
        actual = file_hash(build / (stem + '.bin'))
        boot = runtime['projects'][mode]
        require(boot['bin_sha256'] == actual and boot['session_closed_normally'], 'Wrong runtime image/session')
        require(check['passed'] and actual == manifest['modified_bin']['sha256'] == check['bin_sha256']
                and manifest['parent_sha256'] == parent_sha, 'Final image differs from audit')
        require(check['capsule_graphics_and_timing_unchanged'] and manifest['capsule_proposal'] is None
                and check['changed_sector_count'] == 3, 'Expected audio-only correction')
        require(all(c['before'] == 90 and c['after'] == 104 for c in check['resource_changes'].values()),
                'Wrong hurt volume')
        cue = build / (stem + '.cue')
        parent_cue = ROOT / 'out' / mode / 'boss_voice_restored_20261105_v2' / (stem + '.cue')
        require(cue.read_text('ascii') == working_cue(parent_cue.read_text('ascii'), stem + '.bin'),
                'CUE structure changed')
        current.update(task='hurt_capsule_fix', stage='HURT_GAIN_APPLIED_CAPSULE_UNREPRODUCED',
                       build=build.relative_to(ROOT).as_posix(), cue=cue.relative_to(ROOT).as_posix(),
                       sha256=actual, status_report='docs/HURT_CAPSULE_FIX.md',
                       hurt_gain_db=5.02353, hurt_gain_user_accepted=False,
                       capsule_issue_status='post_grant_mismatch_not_reproduced' if mode == 'ver_buki_riko' else 'not_in_scope',
                       capsule_changed=False, user_accepted=False,
                       previous_pointer=(dest / mode / 'current_build.json').relative_to(ROOT).as_posix(),
                       current_session=None, running_bin_sha256=None,
                       last_test_session=boot['session'],
                       fresh_boot_hurt_tone_verified=boot['hurt_tone_volume_104_verified'],
                       hurt_boot_report='work/hurt_capsule_fix_20261106/runtime/boot_results.json',
                       current_runtime_state='피격음 수정 CUE 활성화. 확인용 새 부팅 세션 종료, 기존 F1/카드 보존.',
                       runtime_verification_scope='전체 디스크/실제 SDK 검사. 실제 혼합음 청취와 캡슐 제보 장면 재현은 미검증.',
                       next_action='새 CUE로 부팅하여 피격음 확인. 시부키 캡슐 불일치 장면 추가 확인 필요; 과거 F3 캐시와 구별.')
        config.update(active_task='hurt_capsule_fix', active_substage='HURT_GAIN_APPLIED_CAPSULE_UNREPRODUCED',
                      latest_integrated_build=build.relative_to(ROOT).as_posix(),
                      latest_integrated_bin_sha256=actual, hurt_capsule_report='docs/HURT_CAPSULE_FIX.md')
        pending[mode] = (current, config)
        result[mode] = {'cue': current['cue'], 'sha256': actual}
    dest.mkdir()
    for mode in PARENTS:
        (dest / mode).mkdir()
        for name in ('current_build.json', 'project.json'):
            shutil.copyfile(ROOT / 'projects' / mode / name, dest / mode / name)
    for mode, (current, config) in pending.items():
        write_json(ROOT / 'projects' / mode / 'current_build.json', current)
        write_json(ROOT / 'projects' / mode / 'project.json', config)
    preserved = {}
    for rel, info in baseline['files'].items():
        if rel not in mutable:
            require(file_hash(ROOT / rel) == info['sha256'], 'Protected file changed: ' + rel)
            preserved[rel] = info['sha256']
    write_json(dest / 'applied.json', {
        'passed': True, 'projects': result, 'preserved_files': preserved,
        'updated_metadata': sorted(mutable), 'originals_modified': False,
        'F1_written': False, 'cards_written': False, 'user_accepted': False,
        'capsule_modified': False, 'capsule_issue_resolved': False,
        'independent_audit_sha256': file_hash(WORK / 'audit/final_independent.json')})
    print(json.dumps({'applied': result, 'protected_files': len(preserved)}))


if __name__ == '__main__':
    main()
