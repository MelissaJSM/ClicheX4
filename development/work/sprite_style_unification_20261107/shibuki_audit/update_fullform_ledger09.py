"""실기에서 발견된 Rising 손 교정과 아직 미패킹인 공중11키를 분리 집계."""
from pathlib import Path
from collections import Counter
import json, struct, sys
H = Path(__file__).resolve().parent
ROOT = H.parents[2]
sys.path.insert(0, str(ROOT))
import numpy as np
from scripts.export_x_consistency import Archive
from native_pose_pack import need, sha, write

def evidence(path):
    p = ROOT / path
    return {'path': path, 'sha256': sha(p.read_bytes())}

def main():
    out = H / 'fullform_ledger09.json'
    need(not out.exists(), 'Fresh ledger required')
    q = json.loads((H / 'fullform_ledger08.json').read_text('utf8'))
    arcs = {}
    for kind, name, folder in [('base', 'PL00_U.ARC', 'prepared_rising_right_base01'), ('ultimate', 'PL02_U.ARC', 'prepared_rising_right_ultimate01')]:
        d = H / folder
        p = json.loads((d / 'proposal.json').read_text('utf8'))
        data = (d / name).read_bytes()
        need(sha(data) == p['files'][name]['after'], 'Candidate changed')
        need((d / 'FROZEN.json').is_file(), 'Not frozen')
        arcs[kind] = Archive(data)
        q['current_candidates'][name] = {'path': (d / name).relative_to(ROOT).as_posix(), 'sha256': sha(data), 'frozen_record': evidence((d / 'FROZEN.json').relative_to(ROOT).as_posix()), 'independent_and_full_native_pending': False, 'new_right_hand_gameplay_verified': False}
    grouped = {}
    empty = []
    for r in q['references']:
        if not r['structural_decode']:
            continue
        form, n = r['form'], r['ref']
        a = arcs['ultimate' if form.startswith('ultimate') else 'base']
        mask = r.get('effective_render_mask', 15 if form in ('fourth', 'ultimate_before') else 0)
        pix = np.array(a.composite(n, mask)[0])
        r['current_rgba_sha256'] = sha(pix.tobytes())
        if n in (103, 104):
            r['decision'] = '원US subtype1 효과 발생점(+6,-12)에 맞춰 오른손 준비→올림을 새 원화로 교정. 전신 반전 없이 의상·발 접점 보존. 원MIPS/GPU·독립 source/readback·루트 최종 미술 검수 후 동결. 새 교정본 실제 플레이와 사용자 수용은 아직 없음.'
        yy, xx = np.nonzero(pix[:, :, 3])
        r['opaque_pixels'] = int(len(xx))
        if not len(xx):
            empty.append({'form': form, 'ref': n, 'status': r['status']})
            continue
        crop = pix[yy.min():yy.max() + 1, xx.min():xx.max() + 1].copy()
        crop[crop[:, :, 3] == 0] = 0
        key = sha(struct.pack('<HH', crop.shape[1], crop.shape[0]) + crop.tobytes())
        block = grouped.setdefault((form, key), {'form': form, 'normalized_rgba_sha256': key, 'size': [crop.shape[1], crop.shape[0]], 'refs': [], 'status_by_ref': {}, 'groups': set()})
        block['refs'].append(n)
        block['status_by_ref'][str(n)] = r['status']
        block['groups'].add(r['group'])
    keys = []
    for _, block in sorted(grouped.items()):
        states = set(block['status_by_ref'].values())
        block['status'] = next(iter(states)) if len(states) == 1 else 'mixed_review_status'
        block['groups'] = sorted(block['groups'])
        keys.append(block)
    statuses = Counter(r['status'] for r in q['references'])
    q['counts']['status_counts'] = dict(statuses)
    q['counts']['new_frozen_form_images'] = statuses['new_art_frozen_for_integration']
    q['counts']['new_prepared_form_images'] = 0
    q['counts']['previous_stale_aggregate_corrected'] = '08의 new_frozen_form_images=244는 status별 실제272와 달랐다. 이번에는 각 reference 상태에서 다시 계산했다. 새 완료 항목을 추가한 것이 아니다.'
    for group in q['groups']:
        group['status_counts'] = dict(Counter(r['status'] for r in q['references'] if r['form'] == group['form'] and r['ref'] in group['refs']))
    q['unpacked_art_in_progress'] = {'group': 'Ultimate air33..54', 'body_keys': list(range(33, 55, 2)), 'body_form_images': 22, 'generated_body_pages': 4, 'native_body_contacts': 'ultimate_air_contacts02', 'after51_local_arm_correction': evidence((H / 'ultimate_air51_arm_registered01/report.json').relative_to(ROOT).as_posix()), 'shot_pairs_remaining': list(range(34, 55, 2)), 'body_packing_pending': True, 'not_counted_as_frozen': True, 'body_and_arm_generation_not_gameplay_verified': True}
    q['right_hand_followup'] = {'cause': '이전 custom104가 원US와 반대손을 올려 공중 불꽃과 분리됨. 단순 기존 custom 접점 보존 검사는 그 오류를 놓쳤음.', 'original_effect_origin': [6, -12], 'old_runtime_proof': 'runtime/shibuki_rising10_review', 'new_native_contact': evidence((H / 'rising_right_packed_contact01/report.json').relative_to(ROOT).as_posix()), 'new_gameplay_verified': False, 'user_final_accepted': False}
    q['full_art_unification_complete'] = False
    write(out, q)
    u = json.loads((H / 'unique_art_keys08.json').read_text('utf8'))
    u['source_ledger'] = evidence(out.relative_to(ROOT).as_posix())
    u['candidates'] = q['current_candidates']
    u['keys'] = keys
    u['counts'] = {'visible_unique_keys': len(keys), 'unique_key_status_counts': dict(Counter(k['status'] for k in keys)), 'reference_status_counts': dict(statuses), 'empty_decoded_slots': empty}
    for form, row in u['forms'].items():
        selected = [k for k in keys if k['form'] == form]
        row['unique_visible_art_keys'] = len(selected)
        row['reference_status_counts'] = dict(Counter(r['status'] for r in q['references'] if r['form'] == form))
        row['unique_key_status_counts'] = dict(Counter(k['status'] for k in selected))
    write(H / 'unique_art_keys09.json', u)
    lines = ['# 시부키 고유 표시 키 집계 09', '', u['definition'], '', '동결은 통합용 정적·네이티브·미술 검수 상태이며 전체 실기/사용자 수용이나 재작업 완료율이 아니다.', '', '| 폼 | 참조 슬롯 | 디코딩 | 고유 표시 키 |', '| --- | ---: | ---: | ---: |']
    for form, row in u['forms'].items():
        lines.append(f"| {form} | {row['native_reference_slots']} | {row['decoded_slots']} | {row['unique_visible_art_keys']} |")
    lines += ['', '상태별 고유 키:', ''] + [f'- {state}: {count}' for state, count in u['counts']['unique_key_status_counts'].items()]
    lines += ['', '남은 핵심 동작군:', ''] + [f"- {row['form']} / {row['group']}: {row['unique_keys']}키; refs {','.join(map(str, row['refs']))}" for row in u['pending_motion_groups']]
    lines += ['', 'Ultimate 공중11몸체·22표시는 새 원화/접점 등록 중이며 동결 집계에 포함하지 않았다. 사격11짝은 아직 새 팔 제작 전이다.', '라이징103/104 오른손 교정은 네 의상 동결 완료. 이전 라이징 실기에서 발견한 오류의 수정이며, 새 수정본의 실기 통과로 바꿔 쓰지 않는다.', '전체 미술 통일화: 미완료.']
    (H / 'UNIQUE_ART_KEYS09.md').write_text('\n'.join(lines) + '\n', encoding='utf8')
    print(json.dumps(u['counts'], ensure_ascii=False))

if __name__ == '__main__':
    main()
