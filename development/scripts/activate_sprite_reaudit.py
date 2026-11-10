"""독립 감사와 최신 검토판 대조가 끝난 스프라이트 재검토본만 활성화한다."""
import json
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.audit_sprite_reaudit_source import WORK, EXPECTED
from scripts.build_hurt_capsule_fix import require, write_json
from src.psx_disc import file_hash


def main():
    dest = WORK / 'application'
    require(not dest.exists(), 'Application already exists')
    protected = json.loads((WORK / 'protection_before.json').read_text('utf8'))['files']
    for name, info in protected.items():
        require(file_hash(ROOT / name) == info['sha256'], 'Protected input changed: ' + name)
    audit = json.loads((WORK / 'audit/final_independent.json').read_text('utf8'))
    require(audit['passed'], 'Final independent audit required')
    gallery = json.loads((ROOT / 'out/sprite_reaudit_20261106/manifest.json').read_text('utf8'))
    browser = json.loads((WORK / 'album_browser_checks.json').read_text('utf8'))
    require(browser['passed'] and browser['html_sha256'] == gallery['sha256'] == file_hash(ROOT / gallery['HTML']),
            'Verified current gallery required')
    pending, applied = {}, {}
    for mode, (stem, expected, _) in EXPECTED.items():
        plan = json.loads((WORK / (mode + '_plan.json')).read_text('utf8'))
        native = json.loads((WORK / (mode + '_plan_native_checks.json')).read_text('utf8'))
        require(plan['source_sha256'] == expected and native['passed'], 'Wrong source/native evidence')
        build = ROOT / plan['output']
        manifest = json.loads((build / 'manifest.json').read_text('utf8'))
        actual = file_hash(build / (stem + '.bin'))
        require(actual == manifest['modified_bin']['sha256'] == audit['projects'][mode]['bin_sha256'] == gallery['sources'][mode]['sha256'],
                'Build/audit/gallery mismatch')
        for name, resource in plan['resources'].items():
            require(native['resources'][name]['candidate_sha256'] == resource['after'] == manifest['resources'][name]['after'],
                    'Wrong prepared resource/native check')
        folder = ROOT / 'projects' / mode
        pointer = json.loads((folder / 'current_build.json').read_text('utf8'))
        config = json.loads((folder / 'project.json').read_text('utf8'))
        require(pointer['sha256'] == config['latest_integrated_bin_sha256'] == expected, 'Concurrent active build change')
        pointer.update(task='sprite_reaudit', stage='SPRITE_REAUDIT_APPLIED_REVIEW',
                       build=plan['output'], cue=f"{plan['output']}/{stem}.cue", sha256=actual,
                       status_report='docs/SPRITE_REAUDIT_20261106.md',
                       sprite_collection=gallery['HTML'], sprite_reaudit_report='docs/SPRITE_REAUDIT_20261106.md',
                       sprite_reaudit_user_accepted=False, sprite_reaudit_runtime_verified=False,
                       user_accepted=False, current_session=None, running_bin_sha256=None,
                       current_runtime_state='새 스프라이트 재검토본 활성화. 실제 실행 범위는 후속 검사 기록 참조.',
                       runtime_verification_scope='전체 자원·실제 디코더·부분 파츠·연속 미리보기 검사. 새 동작 실기는 별도.',
                       previous_pointer=(dest / mode / 'current_build.json').relative_to(ROOT).as_posix(),
                       next_action='새 CUE와 게임 내 카드로 변경 모션 확인. 과거 F3의 그래픽 캐시와 구별.')
        config.update(active_task='sprite_reaudit', active_substage='SPRITE_REAUDIT_APPLIED_REVIEW',
                      latest_integrated_build=plan['output'], latest_integrated_bin_sha256=actual,
                      latest_sprite_collection='out/sprite_reaudit_20261106', latest_sprite_album=gallery['HTML'],
                      sprite_reaudit_report='docs/SPRITE_REAUDIT_20261106.md')
        pending[mode] = (pointer, config)
        applied[mode] = {'cue': pointer['cue'], 'sha256': actual}
    dest.mkdir()
    for mode in EXPECTED:
        (dest / mode).mkdir()
        for name in ('current_build.json', 'project.json'):
            shutil.copyfile(ROOT / 'projects' / mode / name, dest / mode / name)
    for mode, (pointer, config) in pending.items():
        write_json(ROOT / 'projects' / mode / 'current_build.json', pointer)
        write_json(ROOT / 'projects' / mode / 'project.json', config)
    mutable = {f'projects/{mode}/{name}' for mode in EXPECTED for name in ('current_build.json', 'project.json')}
    kept = {}
    for name, info in protected.items():
        if name in mutable:
            continue
        require(file_hash(ROOT / name) == info['sha256'], 'Protected file changed after application: ' + name)
        kept[name] = info['sha256']
    write_json(dest / 'applied.json', {'passed': True, 'projects': applied, 'preserved_files': kept,
                                      'updated_metadata': sorted(mutable), 'user_accepted': False,
                                      'originals_or_saves_written': False, 'current_album': gallery['HTML']})
    print(json.dumps({'applied': applied, 'protected_files': len(kept)}))


if __name__ == '__main__':
    main()
