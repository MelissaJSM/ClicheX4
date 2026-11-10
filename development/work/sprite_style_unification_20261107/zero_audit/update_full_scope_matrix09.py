"""BR22/RN34의 기존 근거만 연결한다. 게임·원화·동결자료를 수정하지 않는다."""
from pathlib import Path
import copy, hashlib, html, json, os, re

ROOT = Path(__file__).resolve().parents[3]
D = Path(__file__).parent
B = D.parent
H, N = B/'shibuki_audit', B/'nana_audit'
P, O = D/'full_scope_matrix08/coverage.json', D/'full_scope_matrix09'
read = lambda p: json.loads(p.read_text('utf8'))
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
old = read(P)
j = copy.deepcopy(old)
old_zero = [c for c in old['cells'] if c['character'] in ('riko', 'rin')]
j['previous_snapshot'] = {'path': P.relative_to(ROOT).as_posix(), 'sha256': sha(P)}
new_inputs = {}


def ev(key, path, purpose):
    assert path.is_file(), path
    item = {'path': path.relative_to(ROOT).as_posix(), 'sha256': sha(path), 'purpose': purpose}
    assert key not in old['evidence'], key
    j['evidence'][key] = item
    new_inputs[key] = item


def state(status, label, refs):
    return {'status': status, 'label': label, 'refs': refs}


j['prior_integration'] = copy.deepcopy(old['integration'])
j['integration'] = {}
for key, project, version in [('br22', 'ver_buki_riko', 22), ('rn34', 'ver_rin_nana', 34)]:
    plan_path = B/f'staging_{key[:2]}_v{version}.json'
    native_path = B/f'staging_{key[:2]}_v{version}_native_checks.json'
    disc_path = ROOT/f'out/{project}/sprite_style_unification_20261107_v{version}/manifest.json'
    plan, native, disc = map(read, [plan_path, native_path, disc_path])
    assert native['passed'] and disc['disc_readback_verified']
    assert disc['all_disc_sectors_compared'] == 251793 and disc['gameplay_timing_code_palettes_audio_preserved']
    for name, resource in plan['resources'].items():
        assert resource['after'] == disc['resources'][name]['after']
        assert sha(ROOT/resource['path']) == resource['after']
    for name, bound in plan['candidate_freeze_bindings'].items():
        assert sha(ROOT/bound['path']) == bound['sha256']
    ev(key, plan_path, '현재 통합 계획; 파일·자원·동결 해시 결속만 확인, 재빌드 없음.')
    ev(key+'_native', native_path, '기존 원MIPS/GPU 통과 기록; 이번 집계에서 재실행 없음.')
    ev(key+'_disc', disc_path, '기존 전섹터·재추출 검사 기록; 이번 집계에서 재실행 없음.')
    j['integration'][key] = {'output': plan['output'], 'resources': plan['resources'],
                            'bin_sha256': disc['modified_bin']['sha256'],
                            'preserve_x_selection': plan['preserve_x_selection']}
assert j['integration']['br22']['bin_sha256'] == '54e53da83b0255e6123dc3c9d6ffeab867bc5201107b1a0ed89c798038739e99'
assert j['integration']['rn34']['bin_sha256'] == '43b63a99328f4aa4e2aa004e8799834397efe91ff4510a36d4cd6b4dd48445d0'

entries = {
    'nana_ledger21': (N/'scope_summary_v21/manifest.json', '558 참조×폼 당시 장부. 루트 승리4·귀환3은 아직 제외되어 있어 이 스냅샷에서 별도 결합한다.'),
    'shibuki_ledger28': (H/'fullform_ledger28.json', '특수3 양자원 동결 당시 장부. 통합 예정 표시는 현재 BR22 계획으로 보완한다.'),
    'shibuki_ledger29': (H/'fullform_ledger29.json', 'BR22 실제 통합·85..92 미패킹 최신 장부.771고유표시 분류는 원화수/완료율 아님.'),
    'shibuki_standing_candidate09': (H/'standing_fire_targets_probe01/manifest.json', '85..92 기본/포스 새7몸체+88 효과의 40층 제작 후보. 미패킹·미수용.'),
    'shibuki_standing_capacity09': (H/'standing_fire_capacity03/report.json', '목표 픽셀 보존 배치의 gfx0 2140B 초과 진단. 새 ARC 없음.'),
    'shibuki_standing_sharing09': (H/'standing_fire_shared01/report.json', '새타일 exact 공유 시험.85/86·87/92 공동atlas, 미출력.'),
    'shibuki_standing_order09': (H/'standing_fire_tileorder01/report.json', '동일타일 순열 압축시험.공동atlas와 결합해730B절감·1410B부족, 미출력.'),
    'nana_vehicle_candidate09': (B/'root_nana_vehicle/joint_targets03/manifest.json', '기본/포스 차량162..174 제작 중. 통합·동결 완료로 세지 않음.'),
    'nana_special_finish_candidate09': (N/'ultimate_special_finish_repaint/hand98_local_probe_v1/manifest.json', 'Ultimate95/98 정합 및98 새손 후보.96/99 파생·패킹 전.'),
    'nana_arrival30_runtime': (B/'runtime/nana_arrival30_summary.json', '새 등장7의 mask0 실제 관측. 포스 보유와 실제 표시 마스크를 구분.'),
    'nana_arrival30_root': (B/'root_review_checkpoint126.json', '시간 보정된 등장3판 및 기존 RN26 charge6판 재열람.'),
    'nana_latest28_runtime': (B/'runtime/nana_fourth_latest28_summary.json', '포스90/91·138/139 양방향 실제 표본 성공. 기본형/Ultimate로 확대하지 않음.'),
    'nana_latest28_root': (B/'root_review_checkpoint123.json', 'RN28 포스 실제463창 중 시간순8판 직접열람.'),
    'protection41': (B/'protection_checkpoint41.json', '루트 보호41: 80파일/5카드쌍·프로세스 종료의 기존 검사.'),
    'webp_index_audit09': (D/'runtime_webp_index_audit01/report.json', '43촬영의 프레임 병합/시간선 영향 읽기 감사. RAM/GPU 판정과 분리.'),
    'webp_corrected16': (D/'nana_legacy_timeline_review01/manifest.json', 'RN12/RN9 옛16판의 시간 대응 정정.116선택 중108이미지 변경; 최신 아트 실기 아님.'),
    'webp_corrected16_visual': (D/'nana_legacy_timeline_review01/visual_review.json', '시간 정정한 옛16판 실제 열람. 기존 파일 보존.'),
    'selection_mapping_source09': (ROOT/'scripts/prepare_nana_ui_small.py', 'RN X선택16사본의 원래 매핑·좌표변환 코드 읽기. 제작함수 미호출.'),
    'selection_guard_source09': (ROOT/'scripts/build_sprite_style_unification.py', 'preserve_x_selection=true이면 선택 X영역 보존; 현재몸체 동기화 검사와 별개.'),
}
for key, (p, why) in entries.items():
    # 후보 메타파일명은 제작자 저장 형식을 그대로 사용한다.
    if key == 'nana_special_finish_candidate09' and not p.exists():
        alternatives = sorted(p.parent.glob('*.json'))
        assert alternatives, p
        p = alternatives[0]
    ev(key, p, why)

for prefix, folder, label in [
    ('nana_base_arrival7', B/'root_nana_arrival/packed_arrival01', '기본/포스 등장7'),
    ('nana_base_victory4', B/'root_nana_victory/packed_victory02', '기본/포스 승리4'),
    ('nana_base_return3', B/'root_nana_return/packed_return03', '기본/포스 귀환3'),
    ('nana_ultimate_ladder7', N/'ultimate_ladder_repaint/packed_first7_diagnostic_v1', 'Ultimate 허용5몸체+2반전'),
    ('nana_ultimate_standing3', N/'ultimate_standing_repaint/packed_standing_candidate_v1', 'Ultimate88/89/97'),
    ('nana_ultimate_recoil2', N/'ultimate_recoil_repaint/packed_recoil_candidate_v1', 'Ultimate90/91'),
    ('shibuki_special_base3', H/'prepared_standing_special_base01', '기본/포스95/96/97'),
    ('shibuki_special_ultimate3', H/'prepared_standing_special_ultimate01', 'Ultimate95/96/97'),
]:
    ev(prefix+'_frozen09', folder/'FROZEN.json', label+' 동결 근거. 현재 통합은 위 계획으로 별도 확인.')

for prefix, folder in [
    ('nana_base_arrival7', 'nana_base_arrival7_independent01'),
    ('nana_base_victory4', 'nana_base_victory4_independent01'),
    ('nana_base_return3', 'nana_base_return3_independent01'),
    ('nana_ultimate_ladder7', 'nana_ultimate_ladder_first7_independent01'),
    ('nana_ultimate_standing3', 'nana_ultimate_standing3_independent01'),
    ('nana_ultimate_recoil2', 'nana_ultimate_recoil2_independent01'),
    ('shibuki_special_base3', 'shibuki_standing3_independent01'),
    ('shibuki_special_ultimate3', 'shibuki_ultimate_special3_independent01'),
]:
    ev(prefix+'_reader09', D/folder/'report.json', '기존 독립 source/목표층·비대상/부분·효과 검사. 재실행 없음.')
    ev(prefix+'_visual09', D/folder/'visual_review.json', '기존 실제 재추출판 열람 기록. 이 집계에서 새 전수 열람하지 않음.')
ev('shibuki_special_directory09', D/'shibuki_standing3_directory_native01/report.json', '280B 내부배치의 실제 로더→directory→객체→decode/upload 508참조 독립 MIPS. 재실행 없음.')

album = ROOT/'out/sprite_style_unification_20261107/review_v27'
am, ac = read(album/'manifest.json'), read(album/'browser_checks.json')
assert ac['passed'] and ac['html_sha256'] == am['sha256'] == sha(album/'ALL_SPRITES_CURRENT.html')
assert am['sources']['ver_buki_riko']['sha256'] == j['integration']['br22']['bin_sha256']
assert am['sources']['ver_rin_nana']['sha256'] == j['integration']['rn34']['bin_sha256']
ev('album27', album/'manifest.json', 'BR22/RN34 실제 BIN에서 만든 앨범27. 표시 레코드는 원화 수나 완료 수가 아님.')
ev('album27_browser', album/'browser_checks.json', '앨범27의 기존28폼·변경픽셀·원표/루프 자동검사. 실기 아님.')
j['current_album'] = {'evidence': 'album27', 'browser_evidence': 'album27_browser',
    'display_records': sum(q['references'] for q in am['counts'].values()),
    'forms': sum(q['forms'] for q in am['counts'].values()), 'changed_display_records': len(am['changes']),
    'completion_percentage': None, 'sources': am['sources'], 'matches_latest_integration': True,
    'difference': None, 'new_visual_review_here': False}
assert j['current_album']['display_records'] == 4510 and j['current_album']['forms'] == 28
assert j['current_album']['changed_display_records'] == 2592
assert read(B/'protection_checkpoint41.json')['passed']

for c in j['cells']:
    char, form, cat = c['character'], c['form'], c['category']
    if char in ('riko', 'rin'):
        continue
    keys = ['rn34', 'nana_ledger21'] if char == 'nana' else ['br22', 'shibuki_ledger28', 'shibuki_ledger29']
    ult = form.startswith('ultimate')
    if char == 'nana' and cat == 'special':
        c['states'] = [state('preserve_reviewed' if ult else 'review_before_decision', '기존 세부 보존 판단' if ult else '기존 세부 추가 판단', '85,86'),
            state('preserve_reviewed', '기존 대기 연결 보존', '87,92'),
            state('integrated_derived_effect', '새89 기반 원83픽셀 효과·통합', '88'),
            state('integrated_new_art', '새 세부 동결·통합', '89..91,97' if ult else '89..91,95..99'),
            state('integrated_new_art', '라이징7 동결·기존 대표실기', '100..104,231,232'),
            state('review_before_decision', '별도 효과/세부 추가 판단', '208..212'),
            state('reachability_review_required', '사용 경로·몸체/효과·아머 조건 분리', '213..230')]
        if ult:
            c['states'] += [state('registered_candidate', '새95/98 원점·손발/총 정합 중', '95,98'), state('not_packed', '새몸체의 X+1 파생정책·패킹 전', '96,99')]
            c['note'] = '88/89/97 및90/91 동결·현재RN34 누적통합. 새90/91의 최종 재추출·부분·원MIPS는 정적 근거이며 실기는 없음.95/98 첫 긴 하체안 미채택, 새95 눈/바닥·98 몸/손 국소정합 중.96/99는 후폼 원그림 차이와 신규 X+1 정책을 구분해야 한다.217/218/220 머리만 복원을 전신 완료로 확대하지 않는다.'
            keys += ['nana_ultimate_standing3_frozen09', 'nana_ultimate_standing3_reader09', 'nana_ultimate_recoil2_frozen09', 'nana_ultimate_recoil2_visual09', 'nana_special_finish_candidate09']
        else:
            c['note'] = 'standing3·special4·recoil2 동결·RN34 누적통합. 포스 양방향88/89/95..99는RN26, 새90/91은RN28 실제 관측 근거가 있다. 이 관측을 기본형 또는 부분아머 실기로 확대하지 않는다.85/86 및208..212는 미재작화 자체가 결함이라는 판정은 아니다.'
            keys += ['nana_special26_runtime', 'nana_latest28_runtime', 'nana_latest28_root']
            c['runtime_coverage_latest'] = {'evidence': 'nana_latest28_runtime', 'observed_form': 'fourth', 'current_cell_observed': form == 'fourth', 'refs': [90,91] if form == 'fourth' else [], 'all_gameplay_verified': False}
        c['art_review'] = '새 후보별 FROZEN·독립 실제열람·루트 열람의 기존 범위를 계승한다. 현재 제작 중95/98은 이 수용에 포함하지 않는다.'
    if char == 'nana' and ult and cat == 'ladder':
        c['states'] = [state('integrated_new_art', '허용5몸체 동결·RN29 이후통합', '143,144,146,154,183'), state('integrated_mirrored_art', '새 양폼 반전정책2·통합', '145,147'), state('held_unfinished', '보류7·현재 부모그림 그대로', '148..153,155')]
        c['note'] = '전체14 중7만 새후보 dcaf로 동결·통합.149/151/153 교정 거부 이후 재시도·우회하지 않았고 그 연동 반전/사격148/150/152/155도 미완료다.보류7의 raw·5층·조립은 그대로.새145/147의 양폼 반전은 기존후폼 차이를 그대로 복원했다는 뜻이 아니다.사다리 실제 플레이는 미검증.'
        c['art_review'] = '허용7의 재추출3판 독립·root124 수용과 FROZEN 근거.보류7에 수용을 확대하지 않음.'
        keys += ['nana_ultimate_ladder7_frozen09', 'nana_ultimate_ladder7_reader09', 'nana_ultimate_ladder7_visual09']
    if char == 'nana' and not ult and cat == 'ceremony':
        c['states'] = [state('integrated_new_art', '새 등장5몸체·통합', '133,135..138'), state('integrated_derived_effect', '실루엣/구체·회복 파생·통합', '130,131,134,139'), state('integrated_new_art', '승리4 동결·RN32 이후통합', '204..207'), state('integrated_new_art', '귀환156 새몸체·RN34통합', '156'), state('integrated_derived_effect', '새몸 테두리·기존빛1875px·RN34통합', '157,158'), state('effect_only', '기존 별도 광선/에너지', '126..129,132,159..161'), state('review_before_decision', '기존 대기실루엣 추가 판단', '140'), state('preserve_reviewed', '대기/먼지 사본 보존', '141,142')]
        c['note'] = 'RN30 새 등장7 관측은 엔진소유아머15인 포스세이브에서도 실제표시mask0.140부터mask15이며 새7의 포스층 표시검증은 아니다.319촬영/286WebP의 시간을 보정한30선택·3판을 root가 봤다.포스138/139는RN28 양방향실기.최신 승리4·귀환3은 동결/원MIPS/정적미술까지이며 실제 승리·전송장면은 아직이다.귀환157은Manhattan1/2(13안·7밖),158은새몸y−10+원159빛1875px.'
        c['art_review'] = '등장 독립/루트 최종판, 승리 전체4+부분4, 귀환 전체3+부분3 실제열람의 기존근거.이번 표는 새열람이 아니다.'
        c['runtime_arrival'] = {'evidence': 'nana_arrival30_runtime', 'save_engine_armor': 15, 'actual_visual_mask': 0, 'refs': [130,131,133,134,135,136,137], 'new_fourth_layers_observed': False, 'unresolved_loading_event': [0], 'new_ref_gpu_success': True}
        keys += ['nana_base_arrival7_frozen09', 'nana_base_arrival7_reader09', 'nana_arrival30_runtime', 'nana_arrival30_root', 'nana_latest28_runtime', 'nana_base_victory4_frozen09', 'nana_base_victory4_visual09', 'nana_base_return3_frozen09', 'nana_base_return3_reader09', 'nana_base_return3_visual09']
    if char == 'nana' and cat == 'ride':
        c['states'] = [state('needs_redraw' if ult else 'registered_candidate', '차량13 별도 후속' if ult else '루트 새 차량13 정합/공통층 제작 중', '162..174'), state('preserve_reviewed', '기존 작은 탑승머리 보존 판단', '184..203')]
        c['note'] = '기본/포스162..174는 root_nana_vehicle의 새후보 정합 중이며 현재RN34에 없다. Ultimate체이서도 별개 잔여다.184..203은 작은 머리로 기존root72 용도별 보존판단을 계승하며 이번에 새보존판정을 한 것은 아니다.'
        if not ult: keys += ['nana_vehicle_candidate09']
    if char == 'nana' and cat == 'ui':
        c['note'] = 'RN34는 preserve_x_selection=true이며 ST0E X영역을 이전 그대로 보존한다.새승리207·귀환156..158 및정지88..91의 선택화면 별도사본은 RN 고유변환으로 후속 동기화/검토가 남았다.기존매핑0..8/18..24 중 실제변경대상만 확인해야 한다.저장대기·초상화·Rin/X 비소유타일을 보호하고 BR의y/반전정책을 무조건 복사하지 않는다.현재 exact 차이 픽셀수는 이 집계에서 새 측정하지 않았다.'
        keys += ['selection_mapping_source09', 'selection_guard_source09']
    if char == 'shibuki' and cat == 'special':
        c['states'] = [state('needs_redraw' if ult else 'registered_candidate', 'Ultimate 새 원화 미제작' if ult else '새7몸체14원화/40층 후보·최신 gfx0 1410B초과', '85..87,89..92'), state('effect_derivation_pending', '원83픽셀 효과·새89 연동 미완료', '88'), state('integrated_new_art', '95/96/97 새세부·BR22통합', '95..97'), state('integrated_new_art', '기존Cyclone/Rising 새원화 통합', '98..104,231,232'), state('effect_only', '별도 효과/몸체 의존 분리', '208..212,218,219'), state('reachability_review_required', '호버/Nova 자세·아머 사용조건 잔여', '213..217,220..230')]
        c['note'] = 'fdba/26fd 특수3은 동결·BR22통합.기본형 gfx0+280B/캡슐12 미소비꼬리 회수는 로더508참조로 검증했고 새 플레이 전수실기는 아니다.현재85..92는 별도 미패킹 후보이며 일부 부분아머/손·총열 접점도 검수 중이다.총열 정본창과Fourth 덮임을 구분하며 총색을 폼팔레트로 임의 재양자화하지 않는다.'
        c['art_review'] = '95/96/97 기존4재추출/독립·root127 수용.85..92 제작후보의 부분통과를 전체미술 수용으로 세지 않는다.'
        c['note'] += '최초2140B초과에서 동일타일 공유·순열로730B 절감했으나1410B 부족하며 ARC는 아직 없다.'
        keys += ['shibuki_special_base3_frozen09', 'shibuki_special_ultimate3_frozen09', 'shibuki_special_directory09', 'shibuki_standing_candidate09', 'shibuki_standing_capacity09', 'shibuki_standing_sharing09', 'shibuki_standing_order09']
    if char == 'shibuki' and ult and cat == 'ceremony':
        for s in c['states']:
            if s['refs'] == '156..158':
                s.update(status='integrated_new_art', label='귀환3 동결·BR21 이후통합')
        c['note'] = '등장8·승리4·귀환3은BR22에 누적통합.135 거부된 편집은 부모 그대로 미완료다.157은새156 y−1+Chebyshev9/14이며 기존가림을 복사하지 않은 제작정책.158은원159의19저장타일/18prefix 뒤 새몸6파트.새귀환·승리의 실제 장면은 이 범위에서 미검증이다.'
        keys += ['shibuki_return3_frozen']
    c['evidence'] = list(dict.fromkeys(c['evidence'] + keys))

# 표시 수와 그림 수를 합산하지 않는다. 각 원장 당시 단위를 별도 유지한다.
j['ledger_units'] = {'nana_scope21': {'evidence': 'nana_ledger21', 'reference_form_pairs': 558, 'excludes_later_root_victory4_and_return3': True, 'later_added_evidence': ['nana_base_victory4_frozen09', 'nana_base_return3_frozen09']}, 'shibuki_scope29': {'evidence': 'shibuki_ledger29', 'count_kind': '폼별 실제RGBA 동형표시/상태분류; 原画枚数 아님'.replace('原画枚数','원화장수')}, 'counts_are_not_completion_or_quality_scores': True, 'combined_artwork_count': None}
j['new_runtime_scope'] = [
    {'evidence': 'nana_latest28_runtime', 'refs': [90,91,138,139], 'observed_form': 'fourth', 'captures': 463, 'root_viewed_boards': 8, 'all_forms_verified': False},
    {'evidence': 'nana_arrival30_runtime', 'refs': [130,131,133,134,135,136,137], 'actual_mask': 0, 'engine_armor': 15, 'captures': 319, 'encoded_webp_frames': 286, 'root_selected_captures': 30, 'root_viewed_boards': 3, 'new_fourth_layers_verified': False, 'unresolved_loading_event': [0]}]
j['gap_analysis'] = [
    {'owner': 'root', 'scope': 'Nana 선택화면 별도사본', 'finding': 'RN34 새207/156..158 및88..91에 대응하는 ST0E X사본은 보존된 이전 자원.', 'acceptance_needed': 'RN 원매핑·offset/반전으로 실제 새몸과 비교하고 대상만 동기화.선택 원표/FX·비소유Rin/초상화 보호와 실제화면 검토.', 'evidence': ['rn34','selection_mapping_source09','selection_guard_source09']},
    {'owner': 'overhaul_ui', 'scope': 'Shibuki 기본/포스85..92 및Ultimate85..92', 'finding': '기본/포스40층의 최초2140B초과→무손실시험730B절감, 현재1410B부족·미패킹. Ultimate 새원화 미제작.', 'acceptance_needed': '픽셀손실 없는 저장·전체공유/부분소유·새손/총열/원83FX·연속판을 검증하고 별도 동결.새크기/색 손실로 용량을 해결하지 않음.', 'evidence': ['shibuki_standing_candidate09','shibuki_standing_sharing09','shibuki_standing_order09','shibuki_ledger29']},
    {'owner': 'overhaul_audio', 'scope': 'Nana Ultimate95..99 중95/96/98/99', 'finding': '95/98 첫 긴 하체안 미채택; 국소 새몸/손 정합 중.97만 이전동결.', 'acceptance_needed': '대기체형·원점·눈/발·새손/정본총 연결 확인 후96/99 신규파생정책과 현후폼차이 명시.원표·부분·패킹/독립·미술 후 동결.', 'evidence': ['nana_ledger21','nana_special_finish_candidate09']},
    {'owner': 'overhaul_audio', 'scope': 'Nana Ultimate 사다리 보류7', 'finding': '148/149/150/151/152/153/155는 부모 그대로 미완료.허용7과 구분.', 'acceptance_needed': '거부된 생성 요청을 우회/재시도하지 않는다.보류사실과 허용범위 유지; 근거 없는149→154사격복사/후폼exact반전 주장을 하지 않음.', 'evidence': ['nana_ultimate_ladder7_frozen09','nana_ultimate_ladder_relations']},
    {'owner': 'overhaul_ui', 'scope': 'Shibuki Ultimate135', 'finding': '등장8 통합에도 거부된135 편집은 부모 보호·미완료.', 'acceptance_needed': '미완료를 숨기거나 인접 새원화로 무근거 대체하지 않는다.현재 동결 범위와 별도 상태로 유지.', 'evidence': ['shibuki_ledger28','br22']},
    {'owner': 'root / 각 캐릭터 담당', 'scope': '두X 차량162..174·호버/Nova213..230', 'finding': 'Nana 기본/포스 차량만 현재제작.다른폼 차량·호버 전신은 남음.부분머리217/218/220 수정은 전신완료가 아님.', 'acceptance_needed': '실사용 아머/소유마스크·부분VRAM·에너지와 몸체를 구분해 최소고유자세 제작.작은 탑승머리184..203는 별도용도 보존판단과 분리.', 'evidence': ['nana_vehicle_candidate09','nana_ledger21','shibuki_ledger28']},
    {'owner': 'root', 'scope': '새저체력·승리·귀환·Ultimate 후속 대표실기', 'finding': 'RN22 저체력 발동실패 유지.최신 승리/귀환/Ult90..91은 정적검증.새등장RN30은mask0만.', 'acceptance_needed': '실제 발동/마스크/양방향/접점 표본별로 기록.기존 동일참조나 포스세이브라는 이유로 다른폼·새아트 성공을 채우지 않음.', 'evidence': ['nana_lowhp22_runtime_failed','nana_arrival30_runtime','nana_base_victory4_frozen09','nana_base_return3_frozen09','nana_ultimate_recoil2_frozen09']},
    {'owner': 'root', 'scope': '기존 미분류·별도사본 끝점', 'finding': 'Nana85/86·140·208..212 판단잔여, 캡슐48참조/반복대사·타이틀/무기획득은 별도 한계.', 'acceptance_needed': '미재작화를 결함으로 단정하지 않고 용도·실사용·현재대기와 연결을 확인.기존 수용 HQ/잔기는 무조건 다시그리지 않음.', 'evidence': ['nana_ledger21','x_endpoint_views','zero_endpoint_views']},
]
j['next_work'] = [
    {'owner': g['owner'], 'character': 'nana' if 'Nana' in g['scope'] else ('shibuki' if 'Shibuki' in g['scope'] else 'all'), 'scope': g['scope'], 'stage': g['finding'], 'evidence': g['evidence']} for g in j['gap_analysis'][:7]
] + [p for p in old['next_work'] if p['character'] in ('riko,rin','all')]
j['completed_milestones_since_previous'] = [{'scope': s, 'evidence': es, 'runtime_verified': False} for s, es in [
    ('BR22 특수3 양자원·귀환 누적통합', ['br22']), ('RN34 등장7·승리4·귀환3·Ultimate사다리7/standing3/recoil2 누적통합', ['rn34']), ('시간 병합 영향 옛16판 정정·실제열람', ['webp_corrected16','webp_corrected16_visual'])]]
j['coverage_limits'] += [
    'RN30은319실제캡처/286WebP.합산시간 보정한30선택·3판 미술근거이며 초기loading0 한사건은 미확정.새등장7 mask0를 mask15 실기로 세지 않는다.',
    'RN28 새90/91·138/139는 포스 양방향 표본만.최신 Ultimate90/91·기본/포스승리/귀환의 실기완료를 뜻하지 않는다.',
    '옛RN12 dash/RN9 Ultimate16판 시간정정은 옛BIN/옛아트 증거.116선택 중108그림이 바뀌었으며 RAM/GPU 결과는 별도이다.이를 최신 아트 실기로 소급하지 않는다.',
    '선택 X 사본은 현재 RN34 preserve_x_selection 조건 때문에 이전 자원을 유지한다.새전신 동결 수에 별도 선택사본 동기화를 자동 포함하지 않는다.',
    '표본 수/변경 표시2592/앨범4510/28폼 및 담당 원장의 참조×폼 수는 모두 서로 다른 단위다.분모로 나누어 품질·전체완료율을 만들지 않는다.'
]
j['snapshot_summary'] = 'BR22/RN34 및 앨범27(4510표시·28폼·2592변경)의 근거를 결합했다.새 승리·귀환·Ultimate90/91은 정적/원MIPS까지, RN30등장7은 실제mask0만이다.포스90/91·138/139 실기와 옛16판 시간정정을 별도 연결했다.시부키85..92·나나Ultimate95..99·차량은 제작 중이며 사다리보류7/시부키135/나나선택별도사본을 잔여로 유지한다.'
j['all_art_complete'] = j['all_gameplay_verified'] = j['user_final_accepted'] = j['game_or_art_modified'] = False
assert old_zero == [c for c in j['cells'] if c['character'] in ('riko','rin')]
for key, value in old['evidence'].items(): assert j['evidence'][key] == value

# X의 비예약228참조는 폼마다 단 하나의 모션분류를 가져야 한다.
def refs(text):
    out = []
    for item in text.replace(' ', '').split(','):
        if '..' in item:
            a,b = map(int,item.split('..'));out.extend(range(a,b+1))
        elif item: out.append(int(item))
    return out
coverage_checks = []
for char in ('shibuki','nana'):
    for form in ('base','fourth','ultimate_before','ultimate_after'):
        rows = [c for c in j['cells'] if c['character']==char and c['form']==form]
        rr = [r for c in rows for s in c['states'] for r in refs(s['refs'])]
        expected = set(range(237)) - {105,*range(175,183)}
        assert len(rr)==228 and len(set(rr))==228 and set(rr)==expected, (char,form,len(rr),sorted(expected-set(rr)))
        coverage_checks.append({'character':char,'form':form,'unique_classified_refs':228,'missing':[],'duplicate':[],'classification_not_acceptance':True})
for c in j['cells']:
    for k in c['evidence']: assert k in j['evidence']
for k,v in new_inputs.items(): assert sha(ROOT/v['path']) == v['sha256'], k
O.mkdir(exist_ok=True)
(O/'coverage.json').write_text(json.dumps(j,ensure_ascii=False,indent=2)+'\n','utf8')

esc=html.escape
def link(k):
    p=os.path.relpath(ROOT/j['evidence'][k]['path'],O).replace('\\','/')
    return f'<a href="{esc(p)}">{esc(k)}</a>'
page=['<!doctype html><html lang="ko"><meta charset="utf-8"><title>전체 범위09 · BR22 RN34</title>',
 '<style>body{background:#111820;color:#e9edf2;font:15px system-ui;margin:24px}a{color:#9dcfff}table{border-collapse:collapse;width:100%;margin:18px 0 35px}th,td{border:1px solid #405164;padding:10px;text-align:left;vertical-align:top}th{background:#233547}summary{cursor:pointer}small{color:#b7c5d4}.notice{padding:16px;background:#263547}</style>',
 '<h1>네 캐릭터 · 폼별 범위09</h1><p>BR22 / RN34 · 12전신폼 × 12범주. <b>수정 표시 수는 원화 수나 완료율이 아닙니다.</b></p>',
 '<p class="notice">'+esc(j['snapshot_summary'])+'</p>',
 '<p><a href="coverage.json">전체 JSON</a> · <a href="../full_scope_matrix08/COVERAGE.html">이전08</a> · <a href="../final_endpoint_audit01/ZERO_UI_HQ_SUPPLEMENT.html">Zero UI/HQ</a> · <a href="../x_endpoint_supplement01/X_UI_HQ_SUPPLEMENT.html">X UI/HQ</a></p>',
 '<p>현재 근거: '+' · '.join(link(k)for k in ['br22','rn34','album27','album27_browser','protection41','nana_arrival30_runtime','nana_latest28_runtime'])+'</p>',
 '<h2>남은 범위와 수용 조건</h2><table><tr><th>담당·범위</th><th>현재 상태</th><th>남은 수용 조건</th></tr>']
for g in j['gap_analysis']:
    page.append('<tr><td>'+esc(g['owner']+' · '+g['scope'])+'</td><td>'+esc(g['finding'])+'</td><td>'+esc(g['acceptance_needed'])+'<details><summary>근거</summary>'+ '<br>'.join(link(k) for k in g['evidence'])+'</details></td></tr>')
page.append('</table>')
for char,name in {'shibuki':'시부키','nana':'나나','riko':'리코','rin':'린'}.items():
    for form,title in j['forms'].items():
        cells=[c for c in j['cells'] if c['character']==char and c['form']==form]
        if not cells: continue
        page.append('<h2>'+name+' · '+esc(title)+'</h2><table><tr><th>범주</th><th>상태·참조</th><th>판단·잔여</th><th>실제 열람·근거</th></tr>')
        for c in cells:
            states='<br>'.join(esc(s['label']+': '+s['refs']) for s in c['states']) or '별도 사본 범위'
            page.append('<tr><td>'+esc(j['categories'][c['category']])+'</td><td>'+states+'</td><td>'+esc(c['note'])+'</td><td><small>'+esc(c['art_review'])+'</small><details><summary>근거</summary>'+'<br>'.join(link(k)for k in c['evidence'])+'</details></td></tr>')
        page.append('</table>')
page.append('<h2>한계</h2><ul>'+''.join('<li>'+esc(s)+'</li>'for s in j['coverage_limits'])+'</ul></html>')
(O/'COVERAGE.html').write_text('\n'.join(page),'utf8')
links=re.findall(r'href="([^"]+)"',(O/'COVERAGE.html').read_text('utf8'))
assert all((O/html.unescape(p)).resolve().is_file() for p in links)
v={'passed':True,'cells':len(j['cells']),'evidence_files':len(j['evidence']),'new_bound_inputs':len(new_inputs),'local_links':len(links),'broken_links':0,'x_reference_classification':coverage_checks,'zero_cells_unchanged':True,'old_snapshot_sha256':sha(P),'new_gameplay_or_native_tests_performed':False,'browser_test_performed':False,'new_all_sheet_visual_review_performed':False,'source_art_or_game_modified':False,'all_art_complete':False,'album_matches_current_integration':True}
(O/'verification.json').write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n','utf8')
print(json.dumps({'json_sha256':sha(O/'coverage.json'),'html_sha256':sha(O/'COVERAGE.html'),'verification_sha256':sha(O/'verification.json'),**v}))
