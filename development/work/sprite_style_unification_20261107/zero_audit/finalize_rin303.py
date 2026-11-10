"""낙봉파 303 교정본의 출처/독립/원CPU/미술 검토를 결속한다."""
from pathlib import Path
import argparse, hashlib, json, sys
D = Path(__file__).parent
ROOT = D.parents[2]
sys.path.insert(0, str(ROOT))
from scripts.c01_audio_build import read_disc
from scripts.build_sprite_style_unification import check_static_body

R = D / 'rin_extension'
P = R / 'prepared_burst_remaining02'
EXPECTED = '1dde3e8793628d5f38b4318543e8d9f3a22b37ad350622a96f4f4f63e92610b9'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
rel = lambda p: p.relative_to(ROOT).as_posix()
read = lambda p: json.loads(p.read_text('utf8'))
def dump(p, data):
    p.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', 'utf8')

ap = argparse.ArgumentParser()
ap.add_argument('--root-review-sha', required=True)
args = ap.parse_args()
assert sha(P / 'PL01_U.ARC') == EXPECTED and not (P / 'FROZEN.json').exists()
q = read(P / 'proposal.json')
ledger = read(R / 'progress_ledger.json')
assert ledger['prepared_count'] == 294
done = set(ledger['new_art_prepared_refs']) | set(q['new_art_refs'])
body = {k for g in ledger['groups'] for k in g['body_or_head_refs']}
remaining = sorted(body - done)
assert len(done) == 303 and len(remaining) == 12

proofs = {
    'source_reproduction_rejections': R / 'rin303_v2_source_proof.json',
    'native_gpu': R / 'rin303_v2_components_native_checks.json',
    'independent_first_body': D.parent / 'nana_audit/rin303_independent_readback.json',
    'independent_shoe_delta': D.parent / 'nana_audit/rin303_shoes_independent_readback.json',
    'original_sequence_native': R / 'burst303_review_v2/report.json',
}
assert sha(proofs['independent_first_body']) == '2ab41fc50e68bbce7f564fedeaeff48c19323c7eb8162604db07ad34216a917b'
assert sha(proofs['independent_shoe_delta']) == 'f87236bd7fdd93825220657e0ea14b6d98fadc2853f813c8c46dd8de7bfc6ee4'
for key, p in proofs.items():
    j = read(p)
    assert j['passed'], key
    if key not in ('independent_first_body', 'independent_shoe_delta'):
        assert j.get('candidate_sha256', EXPECTED) == EXPECTED

review = D.parent / 'root_review_checkpoint52.json'
assert sha(review) == args.root_review_sha
rv = read(review)
assert rv['candidate_sha256'] == EXPECTED
assert not any('??' in s for k in ('findings', 'limits') for s in rv.get(k, []))
own_images = [im for im in rv['art_review_images'] if '/zero_audit/rin_extension/' in im['path']]
assert len(own_images) == 16
for im in own_images:
    assert im['root_actually_viewed'] and sha(ROOT / im['path']) == im['sha256']
visual = R / 'burst303_review_v2/visual_review.json'
v = read(visual)
assert len(v['actually_viewed_by_agent']) == 16
for im in v['actually_viewed_by_agent']:
    assert im['actually_viewed'] and sha(ROOT / im['path']) == im['sha256']

remaining_review = R / 'remaining303_review/report.json'
rr = read(remaining_review)
assert rr['candidate_sha256'] == EXPECTED and len(rr['sheets']) == 3
for im in rr['sheets']:
    assert sha(ROOT / im['path']) == im['sha256']
    im['actually_viewed'] = True
rr.update(all_visually_reviewed=True, observations=[
    '일반/레드 대기·전환 두 판과 정적 효과 한 판을 실제 열람했다. 0/1/2/146은 같은 호흡 낮은 위상, 147/148은 한 셀 눈 차이이며 새로 단순화된 몸체가 아니다.',
    '5/6/1:86/1:0은 대기147과 표시가 완전히 같다. 머릿결·커프·치맛단·흰 부츠와 파란/레드 발끝은 기준 대기 그대로 보존한다.',
    '정적23/24의 몸체는 새185/182에서 동기화한 별도 파생 사본이다. 과거 CLUT 프리뷰에서 몸/원효과 연결을 확인했으며 현재 실기 팔레트 검증으로 세지 않는다.',
], full_art_unification_complete=False)

plan = read(R / 'rin303_v2_components.json')
base = read_disc(ROOT / plan['source_bin'], ('PL01_U.ARC',))[0]['PL01_U.ARC']
static = check_static_body(base, (P / 'PL01_U.ARC').read_bytes(), q['static_body_patch'])
sp = R / 'rin303_static_binding_check.json'
dump(sp, {'passed': True, 'candidate_sha256': EXPECTED, 'result': static})
proofs['static_binding'] = sp
dump(remaining_review, rr)

audit = {
    'passed': True, 'candidate_sha256': EXPECTED, 'cumulative_authored_refs': 303,
    'new_art_refs': 9, 'new_original_bodies': 7, 'accepted_body_reuse177': 'b1_101', 'alias187': 186,
    'proofs': {k: {'path': rel(p), 'sha256': sha(p)} for k, p in proofs.items()},
    'root_review': rel(review), 'root_review_sha256': sha(review),
    'agent_visual_review': rel(visual), 'agent_visual_review_sha256': sha(visual),
    'remaining_review': rel(remaining_review), 'remaining_review_sha256': sha(remaining_review),
    'raw_count': 444, 'non_target_raw_exact': 435, 'display_count': 436,
    'non_target_display_exact': 427, 'partial8_preserved': True,
    'original_effect_world_texels_preserved': 1064, 'composition_xy_bytes_changed': 52,
    'shoe_source_color_pixels': 154, 'native_calls_until_land_or_fall_per_direction': 78,
    'runtime_verified': False, 'user_accepted': False,
    'limitations': [
        '첫 후보의 회색 신발은 반려했다. 최종 원화의 실제 파란색154셀만 적용해 알파·흰 부츠·짙은 외곽을 보존했다.',
        '원 효과는 월드 좌표 색인1064셀 보존이다. 이동된 타일창의 raw 효과 타일 바이트 전체 보존 주장과 구분한다.',
        '원MIPS 낙봉파 함수와 allocator를 격리 실행했다. 생성된 효과 객체의 후속 업데이트·맵 충돌·실제 게임은 미검증이다.',
        '원표의 마지막189 유지96은 호출자의 회복 전환으로 생략된다. WEBP 전체 반복은 미술 검토용이다.',
        '303은 공유/파생을 포함한 참조수이며 품질 완료율이 아니다. 남은 대기10·정적2를 자동 재작화하지 않는다.',
    ],
}
audit_path = R / 'final303_readback_audit.json'
dump(audit_path, audit)
q.update(source_bin=plan['source_bin'], source_bin_sha256=plan['source_sha256'],
         integration_baseline_arc_sha256=plan['resources']['PL01_U.ARC']['before'],
         incremental_parent_arc_sha256=q['source_arc_sha256'], independent_report=rel(audit_path),
         native_report=rel(proofs['native_gpu']), visual_report=rel(visual),
         root_art_review_pending=False, root_review=rel(review), root_review_sha256=sha(review),
         ready_for_checkpoint_integration=True, full_art_unification_complete=False)
dump(P / 'proposal.json', q)
frozen = {
    'candidate_sha256': EXPECTED, 'proposal_sha256': sha(P / 'proposal.json'),
    'static_recipe_sha256': sha(P / 'static_effects.json'),
    'registration_sha256': sha(R / 'burst_charge_registered_v2/registration.json'),
    'independent_report': rel(audit_path), 'independent_report_sha256': sha(audit_path),
    'root_review': rel(review), 'root_review_sha256': sha(review),
    'technical_checks_passed': True, 'ready_for_checkpoint_integration': True,
    'root_art_review_pending': False, 'runtime_verified': False, 'user_accepted': False,
    'cumulative_main_refs': 303, 'new_art_refs': 9,
    'scope': q['scope'] + ' 신발 색 역할154셀 교정. 최종16판 루트·제작자 실제열람 및 원MIPS 양방향78호출 검증. 새 실기는 별도.',
}
for g in ledger['groups']:
    refs = set(g['body_or_head_refs'])
    g['new_art_prepared'] = sorted(refs & done)
    g['remaining'] = sorted(refs - done)
old = read(R / 'remaining294_manifest.json')
manifest = {
    'candidate_sha256': EXPECTED, 'frozen': rel(P / 'FROZEN.json'),
    'original_body_head_classification': 315, 'new_art_refs_with_aliases_and_effect_derivations': 303,
    'remaining_ledger_refs': 12, 'completion_percentage_not_claimed': True,
    'groups': [g for g in old['groups'] if g['group'] != 'rakuhouha'],
    'remaining_refs': remaining, 'visual_review': rel(remaining_review),
    'concrete_backlog': {'baseline_idle_and_transition_refs_preserve': 10,
                        'derived_static_already_synchronized_refs': 2,
                        'active_repaint_refs_in_original_classification': 0},
    'scope': '원래 장부315 중303 재작화/공유/파생과 수용대기·전환10, 동기화정적2를 구분한다. 최신 전체436 표시를 다시 보고 추가 미술 문제가 있으면 새 후보로 진행한다.',
    'full_art_unification_complete': False, 'runtime_verified_all_refs': False, 'user_accepted': False,
}
ledger.update(current_arc=rel(P / 'PL01_U.ARC'), current_sha256=EXPECTED,
              new_art_prepared_refs=sorted(done), remaining_refs_in_original_audit=remaining,
              prepared_count=303, latest_scope=frozen['scope'], latest_proof=rel(audit_path),
              latest_native=rel(proofs['native_gpu']), latest_frozen=rel(P / 'FROZEN.json'),
              remaining_classification=rel(R / 'remaining303_manifest.json'),
              next_page=None, next_page_scope='최신 전체436 표시 재열람 및 원순서/실기 잔여 대조. 확정 문제가 없으면 기준 대기를 억지로 재작화하지 않는다.',
              next_authored_inputs=[])
ledger['limitations'] = [s for s in ledger['limitations'] if '누적294' not in s] + ['누적303은 품질 완료율이 아니다. 새 낙봉파9 실제 게임 검증은 별도이며 최신 전체 시각 재검토를 이어간다.']
dump(P / 'FROZEN.json', frozen)
manifest['frozen_sha256'] = sha(P / 'FROZEN.json')
dump(R / 'remaining303_manifest.json', manifest)
dump(R / 'progress_ledger.json', ledger)
dump(R / 'progress_ledger303_snapshot.json', ledger)
print(json.dumps({'arc': EXPECTED, 'frozen_sha256': sha(P / 'FROZEN.json'),
                  'proposal_sha256': sha(P / 'proposal.json'), 'recipe_sha256': sha(P / 'static_effects.json'),
                  'audit_sha256': sha(audit_path), 'remaining': len(remaining)}, ensure_ascii=False))
