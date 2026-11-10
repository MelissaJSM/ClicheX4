"""Ultimate 작은머리 동결, 기본/포스 등록 및 BR30 제한 실기를 구분한 새 장부."""
from pathlib import Path
from collections import Counter, defaultdict
import json
import struct
import sys
import numpy as np

H = Path(__file__).resolve().parent
ROOT = H.parents[2]
sys.path.insert(0, str(ROOT))
from native_pose_pack import need, sha, write
from scripts.export_x_consistency import Archive


def ev(p):
    return {'path': p.relative_to(ROOT).as_posix(), 'sha256': sha(p.read_bytes())}


def main():
    need(not (H / 'fullform_ledger42.json').exists(), '새 장부 보호')
    q = json.loads((H / 'fullform_ledger41.json').read_text('utf8'))
    d = H / 'prepared_vehicle_head_ultimate01'
    frozen = json.loads((d / 'FROZEN.json').read_text('utf8'))
    need(frozen['frozen'] and frozen['candidate_sha256'] == 'a0629d169d6b5a0d88f31faa5dc4866c7fef99245b278caedc92f523acb3f024', '동결 후보')
    for name, digest in frozen['files'].items():
        need(sha((d / name).read_bytes()) == digest, '동결 파일 변경')
    q['previous_ledger'] = ev(H / 'fullform_ledger41.json')
    q['current_candidates']['PL02_U.ARC'] = {**ev(d / 'PL02_U.ARC'), 'frozen_record': ev(d / 'FROZEN.json'), 'final_verification': ev(d / 'final_verification.json'), 'prepared_lock': ev(d / 'PREPARED_LOCK.json'), 'frozen': True, 'integrated': False, 'gameplay_verified': False}
    tiny = {**q.pop('tiny_vehicle_head_pending'), 'frozen_record': ev(d / 'FROZEN.json'), 'final_verification': ev(d / 'final_verification.json'), 'root_review': ev(H.parent / 'root_review_checkpoint160.json'), 'frozen': True, 'integrated': False, 'status': '새 작은머리 1셀의 19원위치×전후 38표시를 a0629로 동결했다. 95층/608부분/493비대상raw·원MIPS19·3재현11거부·Root160 실제7판과 두 독립자를 결속했다. 현재19동형 정책과 귀 사이±1셀, 실기미실행은 유지한다.'}
    q['tiny_vehicle_head_ultimate_frozen'] = tiny
    base = {
        'forms': ['base', 'fourth'], 'refs': list(frozen['selected_refs']), 'empty_preserved': [198],
        'generated': ev(H / 'vehicle_head_base_inputs01/generated_v1.png'),
        'registration': ev(H / 'vehicle_head_base_native02/registration.json'),
        'targets': ev(H / 'vehicle_head_base_targets01/manifest.json'),
        'semantic_independent': ev(H.parent / 'nana_audit/shibuki_vehicle_head_base_semantic_read01/report.json'),
        'semantic_independent_lock': ev(H.parent / 'nana_audit/shibuki_vehicle_head_base_semantic_read01/READER_LOCK.json'),
        'storage_analysis': ev(H / 'vehicle_head_base_storage_probe02/report.json'),
        'target_layers': 95, 'source_owner_layers': 38, 'partial_RGBA': 608,
        'generated_fixed_cells': 2, 'packed': False, 'ARC_written': False, 'frozen': False, 'integrated': False,
        'status': '새 원화93fb의 전체96 고정등록→기본 공통머리/포스 장식39셀을 직접 독립 재구성했다. 기존13×15/144alpha·홍채 위치와19원점을 보존한다. 메모리 수납에서 기존순서head5 초과12B는 무손실 기록공유로 여유12B가 되며 gfx0 여유는32→150B지만 ARC를 저장하지 않았다. Root 호버 최종 부모를 기다린다.',
        'rebase_required': '최신 PL00 호버 부모를 명시하고184..203의100층/팔레트가 기준36d4와 같은지 확인한 뒤 최종 패킹한다.'
    }
    q['tiny_vehicle_head_base_pending'] = base
    runtime_path = H.parent / 'runtime/br30_hover_summary.json'
    runtime = json.loads(runtime_path.read_text('utf8'))
    need(runtime['bin_sha256'] == q['active_integration']['bin_sha256'] and runtime['source_asset_sha256'] == q['hover_frozen_ultimate']['candidate']['sha256'], '실기 자원 결속')
    for row in runtime['actually_viewed_files']:
        need(sha((ROOT / row['path']).read_bytes()) == row['sha256'], '실기 검토판 변경')
    q['hover_frozen_ultimate']['limited_runtime_by_root'] = {'evidence': ev(runtime_path), 'observer': '/root', 'captures': runtime['recorded_captures'], 'actual_boards': len(runtime['actually_viewed_files']), 'forms': ['ultimate_after'], 'facing': 'right', 'motion': '전진/후진/정지 및 사격', 'new_run_or_visual_review_by_UI': False, 'limits': runtime['limits']}
    q['hover_pending']['status'] = 'Root 기본/포스 호버 새50층의 고정은행 수납 조사 중. Root 전달 기준 무손실 공유/타일순열 후472B 초과이며 새 자원 미통합. 작은머리 메모리 수납의118B 개선은 별도이고 아직 결합하지 않았다.'
    q['next_generation'] = {'scope': '현재 UI 새 생성 예약 없음. Ultimate 작은머리 동결 전달 완료, 기본/포스 작은머리19는 최신 Root 호버 부모를 기다리며 ARC 미저장.', 'blocked_unchanged': 'Ultimate135의 거부된 팔 편집은 재시도하지 않고 부모를 보존한다.', 'all_forms_done': False}
    arcs = {'base': Archive((H / 'prepared_nova_strike_base01/PL00_U.ARC').read_bytes()), 'ultimate': Archive((d / 'PL02_U.ARC').read_bytes())}
    unique, empty = {}, []
    for row in q['references']:
        if not row['structural_decode']:
            continue
        form, n = row['form'], row['ref']
        kind = 'ultimate' if form.startswith('ultimate') else 'base'
        a = arcs[kind]
        mask = row.get('effective_render_mask', 15 if form in ('fourth', 'ultimate_before') else 0)
        pix = np.array(a.composite(n, mask)[0])
        row['current_rgba_sha256'] = sha(pix.tobytes())
        ys, xs = np.nonzero(pix[:, :, 3])
        row['opaque_pixels'] = int(len(xs))
        if n in tiny['refs']:
            if kind == 'ultimate':
                row.update(status='new_art_frozen_for_integration', decision='새 고글·머릿결의19위치별칭을a0629로 동결했다. 현재19동형 정책/귀 사이±1셀/실기미실행을 유지한다.', changed_from_reviewed_parent=True)
                row.pop('in_progress_unapplied_art', None)
            else:
                row.update(status='new_art_source_registered_pending_pack', decision='기본 새 공통머릿결과 포스 검보라/금색 장식39셀을 등록했다. 현재RGBA는36d4 기존그림이며 새 원화는 ARC 미저장 상태다.', in_progress_unapplied_art=base)
        if not len(xs):
            empty.append({'form': form, 'ref': n, 'status': row['status']})
            continue
        crop = pix[ys.min():ys.max() + 1, xs.min():xs.max() + 1].copy()
        crop[crop[:, :, 3] == 0] = 0
        key = sha(struct.pack('<HH', crop.shape[1], crop.shape[0]) + crop.tobytes())
        group = unique.setdefault((form, key), {'form': form, 'normalized_rgba_sha256': key, 'size': [crop.shape[1], crop.shape[0]], 'refs': [], 'origins': [], 'status_by_ref': {}, 'groups': set()})
        group['refs'].append(n)
        group['origins'].append([n, int(xs.min()) - 160, int(ys.min()) - 160])
        group['status_by_ref'][str(n)] = row['status']
        group['groups'].add(row['group'])
    status = Counter(row['status'] for row in q['references'])
    q['counts'].update(status_counts=dict(status), new_frozen_form_images=status['new_art_frozen_for_integration'], new_registered_unpacked_form_images=status['new_art_source_registered_pending_pack'], new_prepared_form_images=0)
    for group in q['groups']:
        group['status_counts'] = dict(Counter(row['status'] for row in q['references'] if row['form'] == group['form'] and row['ref'] in group['refs']))
    q['full_art_unification_complete'] = False
    write(H / 'fullform_ledger42.json', q)
    keys, remaining = [], defaultdict(list)
    for (form, _), group in sorted(unique.items()):
        group['groups'] = sorted(group['groups'])
        states = set(group['status_by_ref'].values())
        group['status'] = next(iter(states)) if len(states) == 1 else 'mixed_review_status'
        group['refs'].sort()
        keys.append(group)
        if states & {'art_rework_group_pending', 'new_art_source_registered_pending_pack'}:
            for motion in group['groups']:
                remaining[(form, motion)].extend(group['refs'])
    report = {'scope': '기본36d4 및 Ultimate a0629 최신 동결의 폼별 고유표시. 실제 통합은 BR30의3f168이며 작은머리 동결은 아직 별도다. 기본/포스 새 작은머리2셀은 등록만 완료했다. 품질완료율이 아니다.', 'definition': '같은 폼의 불투명bbox 크기와RGBA가 같은 평행이동만 합친다. 부분/UI 제외.', 'source_ledger': ev(H / 'fullform_ledger42.json'), 'candidates': q['current_candidates'], 'counts': {'visible_unique_keys': len(keys), 'unique_key_status_counts': dict(Counter(k['status'] for k in keys)), 'reference_status_counts': dict(status), 'empty_decoded_slots': empty}, 'keys': keys, 'pending_motion_groups': [{'form': f, 'group': g, 'refs': sorted(set(refs))} for (f, g), refs in sorted(remaining.items())], 'full_art_unification_complete': False, 'no_percent_estimated': True, 'integration': q['active_integration'], 'pending_art': q['hover_pending'], 'tiny_heads': {'ultimate_frozen': tiny, 'base_pending': base}}
    write(H / 'unique_art_keys42.json', report)
    print(json.dumps({'ledger': ev(H / 'fullform_ledger42.json'), 'keys': ev(H / 'unique_art_keys42.json'), 'unique_status': report['counts']['unique_key_status_counts']}))


if __name__ == '__main__':
    main()
