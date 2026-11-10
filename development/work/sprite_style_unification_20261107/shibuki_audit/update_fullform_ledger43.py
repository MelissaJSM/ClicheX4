"""네 폼 작은머리와 기본/포스 호버 동결을 실제 최신 ARC로 집계한다."""
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


def read(p):
    return json.loads(p.read_text('utf8'))


def ev(p):
    return {'path': p.relative_to(ROOT).as_posix(), 'sha256': sha(p.read_bytes())}


def frozen(d, expected):
    q = read(d / 'FROZEN.json')
    need(q['frozen'] and q['candidate_sha256'] == expected, '동결 후보')
    for name, digest in q['files'].items():
        need(sha((d / name).read_bytes()) == digest, '동결 파일 변경: ' + name)
    v = read(d / 'final_verification.json')
    need(v['passed'] and v['candidate_sha256'] == expected, '최종 검증')
    evidence = v['evidence']
    if isinstance(evidence, dict):
        evidence = [{'path': k, 'sha256': h} for k, h in evidence.items()]
    for row in evidence:
        need(sha((ROOT / row['path']).read_bytes()) == row['sha256'], '최종 근거 변경: ' + row['path'])
    return q


def main():
    need(not (H / 'fullform_ledger43.json').exists(), '새 장부 보호')
    q = read(H / 'fullform_ledger42.json')
    base_d = H / 'prepared_vehicle_head_base01'
    ult_d = H / 'prepared_vehicle_head_ultimate01'
    hover_d = H.parent / 'root_shibuki_hover/packed_hover_candidate03'
    base = frozen(base_d, '4ceab054c4fa9170a0e785fb00baa01f05afaceb4d2dfc2dcc4e80eab30ee36f')
    frozen(ult_d, 'a0629d169d6b5a0d88f31faa5dc4866c7fef99245b278caedc92f523acb3f024')
    hover = frozen(hover_d, '8b4cc387a59c5cc04b365bac7bc31cacfca79a02054e891e90049e2943b53397')
    need(hover['parent_arc_sha256'] == base['candidate_sha256'], '호버 부모')
    q['previous_ledger'] = ev(H / 'fullform_ledger42.json')
    q['current_candidates']['PL00_U.ARC'] = {
        **ev(hover_d / 'PL00_U.ARC'), 'frozen_record': ev(hover_d / 'FROZEN.json'),
        'final_verification': ev(hover_d / 'final_verification.json'), 'frozen': True,
        'integrated': False, 'gameplay_verified': False,
        'small_head_parent': ev(base_d / 'FROZEN.json'),
    }
    tiny = q.pop('tiny_vehicle_head_base_pending')
    tiny.pop('rebase_required', None)
    tiny.update({
        'candidate': ev(base_d / 'PL00_U.ARC'), 'frozen_record': ev(base_d / 'FROZEN.json'),
        'final_verification': ev(base_d / 'final_verification.json'),
        'root_review': ev(H.parent / 'root_review_checkpoint163.json'),
        'independent_report': ev(H.parent / 'nana_audit/shibuki_vehicle_head_base19_independent01/report.json'),
        'packed': True, 'ARC_written': True, 'frozen': True, 'integrated': False,
        'status': '새 기본/포스 머리2셀의19원위치×2폼38표시를4cea로 동결했다. 192입력·95층/608부분·원MIPS19·3재현13거부·Root163 실제7판과 Audio 실제6판을 결속했다. 기존13×15/144alpha·홍채 위치는 보존하며 포스 장식39셀은 head5 소유다. 동일4바이트 기록 공유로 head5 여유12B, gfx 중복 제거로118B 절감했다. Root 새 호버는 이 동결본을 부모로 쓴다.',
        'storage_analysis_is_historical': True,
        'gameplay_verified': False,
    })
    q['tiny_vehicle_head_base_frozen'] = tiny
    ho = q.pop('hover_pending')
    ho.update({
        'candidate': ev(hover_d / 'PL00_U.ARC'), 'frozen_record': ev(hover_d / 'FROZEN.json'),
        'final_verification': ev(hover_d / 'final_verification.json'),
        'independent': ev(H.parent / 'zero_audit/shibuki_base_hover10_independent01/conclusions.json'),
        'packed': True, 'frozen': True, 'integrated': False, 'gameplay_verified': False,
        'status': 'Root 기본/포스 새 호버10참조50층을8b4cc로 동결했다. 작은머리4cea를 보존하고 저장용16참조는512전체타일 역순열 및80조립 타일번호만 변경했다. 256입력·3재현10거부·원MIPS45변경참조·원표12/84canvas·독립832부분/411GPU와 최종 실제 판을 결속했다. 고정 gfx 여유26B이며 원화 축소/생략은 없다. 실제 통합·실기는 아직 별도다.',
    })
    q['hover_frozen_base_fourth'] = ho
    q['next_generation'] = {
        'scope': '현재 UI 새 생성 예약 없음. 허용된 시부키 새 미술은 작은머리와 Root 호버까지 동결했으며 통합·실기 지원을 이어간다.',
        'blocked_unchanged': 'Ultimate135 전후 두 표시의 거부된 팔 편집은 재시도하지 않고 부모를 보존한다.',
        'all_forms_done': False,
    }
    q['current_remaining'] = {
        'art_not_completed': [{'forms': ['ultimate_before', 'ultimate_after'], 'refs': [135], 'reason': '도구 거부 후 부모 보존. 재시도·우회 금지.'}],
        'pending_integration': [ev(hover_d / 'FROZEN.json'), ev(ult_d / 'FROZEN.json')],
        'unverified_runtime': ['네 폼 작은머리의 실제 조종석/가림', '기본/포스 새 호버', '차량162..174 실제 손잡이/발판', '그 밖의 폼·방향·부분아머·60Hz 전수'],
        'new_source_generation_needed_without_blocked_work': [],
        'all_character_or_user_final_acceptance': False,
        'previous_notes_are_historical': '이전 단계 메모보다 references와 current_remaining 및 최신 동결 근거를 우선한다.',
    }
    arcs = {'base': Archive((hover_d / 'PL00_U.ARC').read_bytes()), 'ultimate': Archive((ult_d / 'PL02_U.ARC').read_bytes())}
    unique, empty = {}, []
    for row in q['references']:
        if not row['structural_decode']:
            continue
        form, n = row['form'], row['ref']
        kind = 'ultimate' if form.startswith('ultimate') else 'base'
        mask = row.get('effective_render_mask', 15 if form in ('fourth', 'ultimate_before') else 0)
        pix = np.array(arcs[kind].composite(n, mask)[0])
        row['current_rgba_sha256'] = sha(pix.tobytes())
        ys, xs = np.nonzero(pix[:, :, 3])
        row['opaque_pixels'] = int(len(xs))
        if n in tiny['refs'] and kind == 'base':
            row.update(status='new_art_frozen_for_integration', decision='새 머릿결·포스 장식19원위치를4cea로 동결했고 최신8b4cc에서 raw/5층/부분RGBA 보존을 독립 확인했다.', changed_from_reviewed_parent=True)
            row.pop('in_progress_unapplied_art', None)
        if kind == 'base' and 221 <= n <= 230:
            row.update(status='new_art_frozen_for_integration', decision='Root 새 호버 몸5·사격5의50층을8b4cc로 동결했다. 원제트15위상/탄환7·총구·부분소유와 고정은행을 검증했으며 실제게임은 별도다.', changed_from_reviewed_parent=True)
            row.pop('in_progress_unapplied_art', None)
        if n == 198:
            need(len(xs) == 0, '빈198')
            row.update(status='preserve_verified_blank_reference', decision='실제 빈198의 raw·5층·32부분·빈 조립 기록을 보존했다. 장식 미완료나 새그림으로 세지 않는다.')
        if not len(xs):
            empty.append({'form': form, 'ref': n, 'status': row['status']})
            continue
        crop = pix[ys.min():ys.max() + 1, xs.min():xs.max() + 1].copy()
        crop[crop[:, :, 3] == 0] = 0
        key = sha(struct.pack('<HH', crop.shape[1], crop.shape[0]) + crop.tobytes())
        g = unique.setdefault((form, key), {'form': form, 'normalized_rgba_sha256': key, 'size': [crop.shape[1], crop.shape[0]], 'refs': [], 'origins': [], 'status_by_ref': {}, 'groups': set()})
        g['refs'].append(n)
        g['origins'].append([n, int(xs.min()) - 160, int(ys.min()) - 160])
        g['status_by_ref'][str(n)] = row['status']
        g['groups'].add(row['group'])
    status = Counter(row['status'] for row in q['references'])
    q['counts'].update(status_counts=dict(status), new_frozen_form_images=status['new_art_frozen_for_integration'], new_registered_unpacked_form_images=0, new_prepared_form_images=0)
    for group in q['groups']:
        group['status_counts'] = dict(Counter(row['status'] for row in q['references'] if row['form'] == group['form'] and row['ref'] in group['refs']))
    need(status['art_rework_group_pending'] == 2, '보류135 두 폼만 미완료')
    q['full_art_unification_complete'] = False
    write(H / 'fullform_ledger43.json', q)
    keys, remaining = [], defaultdict(list)
    for (form, _), group in sorted(unique.items()):
        group['groups'] = sorted(group['groups'])
        states = set(group['status_by_ref'].values())
        group['status'] = next(iter(states)) if len(states) == 1 else 'mixed_review_status'
        group['refs'].sort()
        keys.append(group)
        if states & {'art_rework_group_pending'}:
            for motion in group['groups']:
                remaining[(form, motion)].extend(group['refs'])
    report = {
        'scope': '기본8b4cc 및 Ultimate a0629 최신 동결의 폼별 고유표시. 실제 통합은 아직 BR30의36d4/3f168로 분리한다. 변경 표시 비율이나 품질완료율이 아니다.',
        'definition': '같은 폼의 불투명bbox 크기와RGBA가 같은 평행이동만 합친다. 부분/UI 제외.',
        'source_ledger': ev(H / 'fullform_ledger43.json'), 'candidates': q['current_candidates'],
        'counts': {'visible_unique_keys': len(keys), 'unique_key_status_counts': dict(Counter(k['status'] for k in keys)), 'reference_status_counts': dict(status), 'empty_decoded_slots': empty},
        'keys': keys, 'pending_motion_groups': [{'form': f, 'group': g, 'refs': sorted(set(refs))} for (f, g), refs in sorted(remaining.items())],
        'full_art_unification_complete': False, 'no_percent_estimated': True, 'integration': q['active_integration'],
        'remaining': q['current_remaining'], 'tiny_heads': {'ultimate_frozen': q['tiny_vehicle_head_ultimate_frozen'], 'base_frozen': tiny},
    }
    write(H / 'unique_art_keys43.json', report)
    print(json.dumps({'ledger': ev(H / 'fullform_ledger43.json'), 'keys': ev(H / 'unique_art_keys43.json'), 'unique_status': report['counts']['unique_key_status_counts'], 'remaining': report['pending_motion_groups']}))


if __name__ == '__main__':
    main()
