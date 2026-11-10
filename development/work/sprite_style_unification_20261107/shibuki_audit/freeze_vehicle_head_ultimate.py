"""Ultimate 작은 차량머리19의 고정 자원·출처·독립·루트 검토를 결속한다."""
from pathlib import Path
import argparse
import json
import sys

H = Path(__file__).resolve().parent
ROOT = H.parents[2]
sys.path.insert(0, str(ROOT))
from native_pose_pack import need, sha, write

FINAL = 'a0629d169d6b5a0d88f31faa5dc4866c7fef99245b278caedc92f523acb3f024'
REFS = [n for n in range(184, 204) if n != 198]


def read(p):
    return json.loads(p.read_text('utf8'))


def images(rows):
    for row in rows:
        need(sha((ROOT / row['path']).read_bytes()) == row['sha256'], '근거 파일 변경: ' + row['path'])


def check(files, base=ROOT):
    if isinstance(files, list):
        images(files)
    else:
        for name, digest in files.items():
            need(sha((base / name).read_bytes()) == digest, '잠금 파일 변경: ' + name)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--root-review', required=True)
    ap.add_argument('--root-review-sha256', required=True)
    args = ap.parse_args()
    d = H / 'prepared_vehicle_head_ultimate01'
    need(not (d / 'FROZEN.json').exists(), '기존 동결 보호')
    need(sha((d / 'PL02_U.ARC').read_bytes()) == FINAL, '후보 변경')
    il = read(d / 'INPUT_LOCK.json')
    pl = read(d / 'PREPARED_LOCK.json')
    check(il['files'])
    check(pl['files'], d)
    check(pl['source_scripts'], H)
    need(len(il['files']) == 188, '입력 수')

    audit = H.parent / 'zero_audit/shibuki_vehicle_head_ultimate19_independent01'
    peer = H.parent / 'nana_audit/shibuki_vehicle_head_source_independent01'
    need(sha((audit / 'report.json').read_bytes()) == '5b4cd8d554b07d0f33e1f798669a3f35d5b71145292656923e13e7da5f4380d8', '독립 보고 변경')
    need(sha((audit / 'conclusions.json').read_bytes()) == '0dc31aafecc35fc2fbe20e64eeadbaedb8d8a954c58b22071d6e8ca2adb2b5f1', '독립 결론 변경')
    check(read(audit / 'READER_LOCK.json')['files'])
    peer_lock = read(peer / 'READER_LOCK.json')
    check(peer_lock['inputs'])
    check(peer_lock['outputs'])
    ind, con, source = [read(p) for p in (audit / 'report.json', audit / 'conclusions.json', peer / 'report.json')]
    need(all(q['passed'] and q['candidate_sha256'] == FINAL and q['parent_sha256'] == il['parent_sha256'] for q in (ind, con, source)), '독립 후보 또는 부모 불일치')
    expected = {'raw_checked': 512, 'non_target_raw_exact': 493, 'non_target_layers_exact': 1045, 'target_layers_exact': 95, 'non_target_compositions_exact': 1753, 'new_owner_layers': 38, 'GPU_parts': 95, 'selected_blank_records_exact': 57, 'partial_RGBA_exact': 608}
    need(ind['counts'] == con['checks'] == expected, '독립 수치')
    need(ind['ref198_raw_layers_compositions_all32blank_preserved'] and ind['other_composition_banks_entire_bytes_exact'] and ind['entry_boundaries_palette_audio_other_entries_exact'], '보존 조건')
    need(source['exact_owned_layers'] == 38 and source['empty678_target_checks'] == 57 and len(source['gold_samples']) == 10 and source['changed_from_nearest'] == 5, '원화 직접 재구성')
    for name in ('direct_source_peer', 'original_ownership', 'caller_peer'):
        images(con[name].values())
    vis = read(audit / 'visual_review.json')
    need(vis['actually_viewed'] and vis['board_count'] == len(vis['boards']) == 6, '독립 실제 6판')
    images(vis['boards'])
    images([vis['source_peer_actual_views']])

    rp = (ROOT / args.root_review).resolve()
    need(rp.is_relative_to(H.parent.resolve()) and sha(rp.read_bytes()) == args.root_review_sha256, '루트 검토 경로/해시')
    review = read(rp)
    need(review['candidate_sha256'] == FINAL, '루트 검토 후보')
    images(review['actually_viewed_files'])
    packed_names = {'before_readback_00.png', 'before_readback_01.png', 'after_readback_00.png', 'after_readback_01.png', 'ownership_184.png', 'ownership_196.png'}
    viewed_hashes = {v['sha256'] for v in review['actually_viewed_files']}
    need(all(sha((d / name).read_bytes()) in viewed_hashes for name in packed_names), '루트 최종 재추출4/부분2 열람')

    vr = read(d / 'verification.json')
    need(vr['passed'] and vr['candidate_sha256'] == FINAL and vr['total_identical_builds'] == 3 and vr['rejected_count'] == 11 and not vr['pixel_reduction'], '재현/거부')
    np = H / 'vehicle_head_ultimate_components_native_checks.json'
    native = read(np)
    nr = native['resources']['PL02_U.ARC']
    checks = [v for bank in nr['banks'] for v in bank['native_decoder_checks']]
    need(native['passed'] and nr['candidate_sha256'] == FINAL and len(checks) == 19 and all(v['buffer_outside_and_unused_tail_preserved'] for v in checks), '원MIPS19')
    seq = read(d / 'original_sequence_read.json')
    need(seq['candidate_sha256'] == FINAL and seq['all_pointer_step_bytes_exact'] and seq['table_count'] == 26 and seq['step_count'] == 92 and not seq['changes_to_EXE'], '원표 읽기')
    check(read(d / 'post_lock_evidence.json')['evidence'])
    author = read(d / 'author_visual_review.json')
    need(author['actually_viewed'] and author['actual_images'] == 8 and not author['new_confirmed_defect'], '제작자 실제 열람')
    images(author['images'])

    evidence = [d / n for n in ('INPUT_LOCK.json', 'PREPARED_LOCK.json', 'verification.json', 'author_visual_review.json', 'original_sequence_read.json', 'post_lock_evidence.json')]
    evidence += [audit / n for n in ('report.json', 'conclusions.json', 'visual_review.json', 'READER_LOCK.json')]
    evidence += [peer / n for n in ('report.json', 'visual_review.json', 'READER_LOCK.json')]
    evidence += [ROOT / row['path'] for group in ('original_ownership', 'caller_peer') for row in con[group].values()]
    evidence += [np, rp, Path(__file__)]
    write(d / 'final_verification.json', {
        'passed': True, 'candidate_sha256': FINAL, 'parent_arc_sha256': il['parent_sha256'], 'selected_refs': REFS,
        'source_files_checked': 188, 'counts': expected, 'total_identical_builds': 3, 'rejected_inputs': 11,
        'root_actual_images': len(review['actually_viewed_files']), 'root_final_readback_and_partial_images': 6,
        'independent_final_boards': 6, 'author_actual_images': 8, 'original_MIPS_changed_refs': 19,
        'original_table_count': 26, 'original_step_count': 92,
        'evidence': {p.relative_to(ROOT).as_posix(): sha(p.read_bytes()) for p in evidence},
        'all_bank_entry_boundaries_palette_audio_preserved': True, 'ref198_and_empty678_preserved': True,
        'supersedes_initial_pending_flags': True, 'gameplay_verified': False, 'user_accepted': False,
        'full_project_complete': False,
        'limits': [
            '현재 수용된 시부키의 같은 머리19개 위치 정책을 유지한다. 원US의5개 또는 포스6개 고유 크롭 복원은 아니다.',
            '새 머리는13×15/144픽셀과 홍채 원점이 같지만 귀 사이1셀 추가/1셀 제거가 있어 외곽 전체exact를 주장하지 않는다.',
            '독립 출처 재구성은Audio, ARC/부분/최종6판은HUD, 최종 미술은Root의 별도 수행 결과다.',
            '원MIPS19는 graphics 포인터를 공급한 디코더/업로드 검사다. 전체 로더·실제GPU 래스터화·조종석 실기는 별도다.',
            '원표26개92스텝 바이트 보존은 읽기 검사이며 실제26개 차량 동작 재생이 아니다. 빈198도 표50/51의 사용을 보존한다.',
            '실제 Ultimate 획득 전은mask15, 획득 후는mask0이다. 217..230 강제15 규칙을 이 머리에 적용하지 않는다.',
            '기본/포스 작은 머리 보완과 기본/포스 호버는 별도 후보이며 이번PL02 동결에 포함하지 않는다.',
            '기술보고 actually_viewed=false 및 초기 pending 상태는 당시 기록으로 보존하고 최종visual/conclusions의 완료 범위만 결속한다.'
        ]
    })
    write(d / 'FROZEN.json', {
        'frozen': True, 'files': {p.name: sha(p.read_bytes()) for p in sorted(d.iterdir()) if p.is_file() and p.name != 'FROZEN.json'},
        'candidate_sha256': FINAL, 'parent_arc_sha256': il['parent_sha256'], 'selected_refs': REFS,
        'native_and_independent_passed': True, 'root_final_readback_and_partial_reviewed': True,
        'root_valid_actual_plates': len(review['actually_viewed_files']), 'all_bank_boundaries_preserved': True,
        'supersedes_initial_pending_flags': True, 'gameplay_verified': False, 'user_accepted': False,
        'full_style_unification_complete': False
    })
    print(json.dumps({'candidate': FINAL, 'frozen': sha((d / 'FROZEN.json').read_bytes()), 'final': sha((d / 'final_verification.json').read_bytes())}))


if __name__ == '__main__':
    main()
