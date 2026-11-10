"""기본/포스 피격13의 고정 자원과 별도 검사 근거를 연결한다."""
from pathlib import Path
import json, sys
H = Path(__file__).resolve().parent
ROOT = H.parents[2]
sys.path.insert(0, str(ROOT))
from native_pose_pack import need, sha, write
from pack_shibuki_hurt import PARENT, REFS, LOCK_SHA, validate_inputs

FINAL = '87e7d1db40c2380815ca2986bc27382db73f718d9c338d2eaad776372a2e257b'

def main():
    d = H / 'prepared_hurt_base01'
    need(not (d / 'FROZEN.json').exists(), 'Already frozen')
    lk = json.loads((d / 'PREPARED_LOCK.json').read_text('utf8'))
    for n, h in lk['files'].items():
        need(sha((d / n).read_bytes()) == h, 'Prepared changed: ' + n)
    for n, h in lk['source_scripts'].items():
        need(sha((H / n).read_bytes()) == h, 'Producer changed: ' + n)
    validate_inputs((H / 'prepared_base_run01/PL00_U.ARC').read_bytes())
    need(sha((d / 'PL00_U.ARC').read_bytes()) == FINAL, 'Candidate changed')
    names = [
        H / 'hurt_base_components_native_checks.json',
        H.parent / 'zero_audit/shibuki_hurt13_independent01/report.json',
        H.parent / 'zero_audit/shibuki_hurt13_independent01/visual_review.json',
        H.parent / 'root_review_checkpoint103.json',
        H / 'hurt_base_sequence01/report.json',
        H / 'hurt_base_sequence01/browser_verification.json',
    ]
    native, independent, visual, root, sequence, browser = [
        json.loads(p.read_text('utf8')) for p in names]
    need(native['passed'] and independent['passed'] and browser['passed'], 'Checks not passed')
    need(native['resources']['PL00_U.ARC']['candidate_sha256'] == FINAL, 'Native resource')
    need(independent['candidate_sha256'] == FINAL and independent['target_lock_sha256'] == LOCK_SHA,
         'Independent resource/lock')
    need(root['arc_sha256'] == FINAL and len(root['root_actually_viewed']) == 8, 'Root review')
    for row in root['root_actually_viewed']:
        need(sha((ROOT / row['path']).read_bytes()) == row['sha256'], 'Root image changed')
    need(sequence['candidate_sha256'] == FINAL and sequence['native_table_bytes_verified'], 'Sequence source')
    need(browser['native_table_report_sha256'] == sha(names[4].read_bytes()), 'Browser report binding')
    need(browser['html_sha256'] == sha((H / 'hurt_base_sequence01/REVIEW.html').read_bytes()), 'HTML changed')
    checks = sum(x['canvas_forms_checked'] for x in browser['cases'])
    need(checks == 710 and len(sequence['native_step_checks']) == 5, 'Sequence coverage')
    plates = [H / f'hurt_base_sequence01/{form}_id{aid}_ordered.png'
              for form in ('base', 'fourth') for aid in (33, 34, 35)]
    verification = json.loads((d / 'verification.json').read_text('utf8'))
    proof = {
        'passed': True, 'candidate_sha256': FINAL, 'parent_arc_sha256': PARENT,
        'target_lock_sha256': LOCK_SHA, 'selected_visual_refs': list(REFS),
        'evidence': {p.relative_to(ROOT).as_posix(): sha(p.read_bytes()) for p in names},
        'counts': independent['counts'], 'native_MIPS_GPU': True,
        'independent_reader_no_producer_called': True,
        'root_actual_packed_plates': 8, 'author_actual_packed_plates': 8,
        'author_actually_viewed_ordered_plates': [
            {'path': p.relative_to(ROOT).as_posix(), 'sha256': sha(p.read_bytes())} for p in plates],
        'root_ordered_plate_review_pending': True,
        'native_sequence_ids': [33, 34, 35, 36, 37],
        'native_sequence_pointer_and_step_bytes_exact': True,
        'browser_actual_canvas_checks': checks,
        'browser_loop_terminal_hold_play_pause_verified': True,
        'continuous_video_actually_watched_by_model': False,
        'reproduction_runs': verification['reproduction_runs'],
        'invalid_input_rejections': verification['rejection_count'],
        'bank_and_entry_boundaries_preserved': True,
        'new_gameplay_verified': False, 'user_accepted': False, 'full_project_complete': False,
        'replaces_pending_status_in_initial_prepared_reports': True,
        'limitations': verification['limitations'] + [
            '오라 색상/옛 의상 조각 제거 방향은 root103의 최종 재추출 열람에서 수용했다.',
            '원표33..37의 순서/유지 호출수를 재생하지만 60호출/초는 검토 가정이며 실제 피격 물리·외부 상태·무적 깜빡임·소리는 재현하지 않았다.',
            '정지 순서판6장의 직접 열람과 브라우저 실제 canvas 검사는 연속 게임 영상을 직접 본 것과 구분한다.',
        ],
        'next_scope': 'Ultimate 피격4몸체의 새 전후 의상 공통부/손발 정합, 원본 별 효과 파생과13참조 패킹.'
    }
    write(d / 'final_verification.json', proof)
    write(d / 'FROZEN.json', {
        'frozen': True,
        'files': {p.name: sha(p.read_bytes()) for p in sorted(d.iterdir())
                  if p.is_file() and p.name != 'FROZEN.json'},
        'candidate_sha256': FINAL, 'parent_arc_sha256': PARENT,
        'source_lock_sha256': LOCK_SHA, 'selected_visual_refs': list(REFS),
        'native_and_independent_passed': True, 'root_packed_art_reviewed': True,
        'supersedes_initial_pending_flags': True, 'gameplay_verified': False,
        'user_accepted': False, 'full_style_unification_complete': False,
    })
    print(json.dumps({'frozen': sha((d / 'FROZEN.json').read_bytes()),
                      'verification': sha((d / 'final_verification.json').read_bytes())}))

if __name__ == '__main__':
    main()
