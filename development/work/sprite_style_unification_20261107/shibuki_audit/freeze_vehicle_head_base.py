"""기본/포스 작은머리19의 최종 독립·미술·원코드 근거를 결속한다."""
from pathlib import Path
import argparse
import json
import sys

H = Path(__file__).resolve().parent
ROOT = H.parents[2]
sys.path.insert(0, str(ROOT))
from native_pose_pack import need, sha, write
from freeze_vehicle_head_ultimate import read, check, images

FINAL = '4ceab054c4fa9170a0e785fb00baa01f05afaceb4d2dfc2dcc4e80eab30ee36f'
REFS = [n for n in range(184, 204) if n != 198]


def check_lock(p):
    lock = read(p)
    groups = [lock[k] for k in ('files', 'inputs', 'outputs') if k in lock]
    need(bool(groups), '독립 잠금 목록 없음')
    for group in groups:
        check(group)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--root-review', required=True)
    ap.add_argument('--root-review-sha256', required=True)
    ap.add_argument('--independent-report-sha256', required=True)
    args = ap.parse_args()
    d = H / 'prepared_vehicle_head_base01'
    need(not (d / 'FROZEN.json').exists(), '기존 동결 보호')
    need(sha((d / 'PL00_U.ARC').read_bytes()) == FINAL, '후보 변경')
    il, pl = read(d / 'INPUT_LOCK.json'), read(d / 'PREPARED_LOCK.json')
    check(il['files'])
    check(pl['files'], d)
    check(pl['source_scripts'], H)
    need(len(il['files']) == 192, '192입력 잠금')
    audit = H.parent / 'nana_audit/shibuki_vehicle_head_base19_independent01'
    peer = H.parent / 'nana_audit/shibuki_vehicle_head_base_semantic_read01'
    need(sha((audit / 'report.json').read_bytes()) == args.independent_report_sha256, '독립 최종 보고 변경')
    check_lock(audit / 'READER_LOCK.json')
    check_lock(peer / 'READER_LOCK.json')
    ind, source = read(audit / 'report.json'), read(peer / 'report.json')
    need(ind['passed'] and ind['candidate_sha256'] == FINAL and ind['parent_sha256'] == il['parent_sha256'], '독립 후보/부모')
    expected = {'raw': 508, 'non_target_raw': 489, 'non_target_layers': 1045, 'target_layers': 95, 'non_target_compositions': 1749, 'owner_layers': 38, 'GPU_parts': 95, 'empty678_offset_exact': 57, 'partial_RGBA': 608}
    need(ind['counts'] == expected, '독립 수치')
    need(ind['source_reconstruction']['sha256'] == sha((peer / 'report.json').read_bytes()) == 'abc7753ce406a8509cc7a31f44d339125591a07b6127916d8c86e601c0845449', '직접 출처 결속')
    need(ind['source_reconstruction']['source_inputs_unchanged'] and ind['source_reconstruction']['new_master0_and5_reused'], '출처 재사용')
    need(source['passed'] and source['new_head5_owner'] == 39 and source['source_missing_inside_old_alpha'] == [0, 0] and source['old_alpha_pixels'] == 144 and source['gold_changes_from_nearest'] == 0, '원화2셀/소유')
    need(source['common_eye_index'] == 7 and source['head5_at_eye'] == 0 and source['final_base_and_fourth_RGBA_exact_to_registration'], '공통 홍채/의상')
    for key in ('other_entries_palette_sound_exact', 'bank_boundaries_exact', 'other_composition_banks_except0and5_entire_bytes_exact', 'non_target_raw_alias_groups_excluding_targets_exact'):
        need(ind[key], key)
    need(ind['ref198']['raw_and_layers_exact'] and ind['ref198']['all32_blank'] and len(ind['selected_empty678_offset_proofs']) == 57, '198/빈678')
    storage = ind['record_storage']
    need(storage['all_non_target_ordered_4byte_sequences_exact'] and storage['head5_tail_slack_bytes'] == 12 and not storage['target_records_shared_with_external'], '무손실 기록 공유')
    visual = read(audit / 'visual_review.json')
    need(visual['actually_viewed'], '독립 실제 열람')
    boards = visual.get('images', visual.get('boards', visual.get('actually_viewed_files', visual.get('viewed_files'))))
    need(isinstance(boards, list) and len(boards) == 6, '독립 최종6판')
    images(boards)
    root_path = (ROOT / args.root_review).resolve()
    need(root_path.is_relative_to(H.parent.resolve()) and sha(root_path.read_bytes()) == args.root_review_sha256, '루트 검토 경로/해시')
    review = read(root_path)
    need(review['candidate_sha256'] == FINAL, '루트 검토 후보')
    images(review['actually_viewed_files'])
    names = ('base_readback_00.png', 'base_readback_01.png', 'fourth_readback_00.png', 'fourth_readback_01.png', 'ownership_184.png', 'ownership_196.png')
    viewed = {r['sha256'] for r in review['actually_viewed_files']}
    need(all(sha((d / name).read_bytes()) in viewed for name in names), '루트 최종6판 열람')
    vr = read(d / 'verification.json')
    need(vr['passed'] and vr['candidate_sha256'] == FINAL and vr['total_identical_builds'] == 3 and vr['rejected_count'] == 13 and not vr['pixel_reduction'], '3재현/13거부')
    need(vr['graphics_saved'] == 118 and vr['graphics_remaining_before'] == 32 and vr['graphics']['remaining_slack'] == 150 and vr['final_head5_slack'] == 12, '공간 확보 근거')
    need(len(vr['hover10_50layers_exact']) == 50 and vr['palette_exact'], '후속 호버 부모 보존')
    native_path = H / 'vehicle_head_base_components_native_checks.json'
    native = read(native_path)
    native_resource = native['resources']['PL00_U.ARC']
    native_rows = [r for bank in native_resource['banks'] for r in bank['native_decoder_checks']]
    need(native['passed'] and native_resource['candidate_sha256'] == FINAL and len(native_rows) == 19 and all(r['buffer_outside_and_unused_tail_preserved'] for r in native_rows), '원MIPS19')
    seq = read(d / 'original_sequence_read.json')
    need(seq['candidate_sha256'] == FINAL and seq['all_pointer_step_bytes_exact'] and seq['table_count'] == 26 and seq['step_count'] == 92, '원표 읽기')
    check(read(d / 'post_lock_evidence.json')['evidence'])
    author = read(d / 'author_visual_review.json')
    need(author['actually_viewed'] and author['actual_images'] == 7 and not author['new_confirmed_defect'], '제작자 실제7판')
    images(author['images'])
    evidence = [d / name for name in ('INPUT_LOCK.json', 'PREPARED_LOCK.json', 'verification.json', 'post_lock_evidence.json', 'author_visual_review.json', 'original_sequence_read.json')]
    evidence += [audit / name for name in ('report.json', 'visual_review.json', 'READER_LOCK.json')]
    evidence += [peer / name for name in ('report.json', 'READER_LOCK.json')]
    evidence += [native_path, root_path, H / 'freeze_vehicle_head_ultimate.py', Path(__file__)]
    write(d / 'final_verification.json', {
        'passed': True, 'candidate_sha256': FINAL, 'parent_arc_sha256': il['parent_sha256'], 'selected_refs': REFS,
        'source_files_checked': 192, 'counts': expected, 'total_identical_builds': 3, 'rejected_inputs': 13,
        'root_actual_images': len(review['actually_viewed_files']), 'independent_actual_images': 6, 'author_actual_images': 7,
        'original_MIPS_changed_refs': 19, 'original_table_count': 26, 'original_step_count': 92,
        'all_bank_entry_boundaries_palette_audio_preserved': True, 'ref198_and_empty678_preserved': True,
        'graphics_saved_bytes': 118, 'graphics_slack_bytes': 150, 'head5_slack_bytes': 12, 'future_hover50layers_and_palette_exact': True,
        'evidence': {p.relative_to(ROOT).as_posix(): sha(p.read_bytes()) for p in evidence},
        'supersedes_initial_pending_flags': True, 'gameplay_verified': False, 'user_accepted': False, 'full_project_complete': False,
        'limits': ['현재 시부키19동형 정책을 유지하며 원US5/6고유 크롭 복원은 아니다.', '기존13×15/144alpha·홍채 원점을 보존한다. 원화 외곽추가3/5셀은 내부 편집 범위 밖으로 제외했으며 기존alpha 안 옛RGB 복사는 없다.', '새 포스 장식39셀은 head5에만 속하고 기본 새머리/홍채는 공통이다. 새 전체팔레트 교체가 아니다.', 'head5 부족12B는 동일4바이트 기록의 접두/접미 공유로 해결했다. 각ref 기록 순서/내용과 고정 은행을 보존하며 압축용 아트 단순화는 하지 않았다.', '원MIPS19는 graphics 포인터를 공급한 디코더/업로드 검사이며 전체 로더·실제GPU 래스터화·조종석 실기는 별도다.', '원표26개92스텝 보존은 읽기 검사다. 실제26개 동작·반전·가림 검증으로 세지 않는다.', '이 후보의 호버10/50층은 기존36d4와 같다. Root가 후속 새 호버를 이 부모에 별도 적용한다.', '초기 목표의 packing_parent_pending 및 기술 actually_viewed=false는 당시 기록으로 보존하고 최종 후속 근거의 범위만 결속한다.'],
    })
    write(d / 'FROZEN.json', {'frozen': True, 'files': {p.name: sha(p.read_bytes()) for p in sorted(d.iterdir()) if p.is_file() and p.name != 'FROZEN.json'}, 'candidate_sha256': FINAL, 'parent_arc_sha256': il['parent_sha256'], 'selected_refs': REFS, 'native_and_independent_passed': True, 'root_final_readback_and_partial_reviewed': True, 'root_valid_actual_plates': len(review['actually_viewed_files']), 'all_bank_boundaries_preserved': True, 'supersedes_initial_pending_flags': True, 'gameplay_verified': False, 'user_accepted': False, 'full_style_unification_complete': False})
    print(json.dumps({'candidate': FINAL, 'frozen': sha((d / 'FROZEN.json').read_bytes()), 'final': sha((d / 'final_verification.json').read_bytes())}))


if __name__ == '__main__':
    main()
