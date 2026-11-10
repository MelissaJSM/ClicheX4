"""Read current UI copies and distinguish historical live evidence from new art."""
from pathlib import Path
import hashlib
import json
import sys
import numpy as np

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from scripts.prepare_riko_ui import entry, SELECTION_MAPPING
from scripts.overhaul_sprites_audit import render
from src.psx_player import graphics_bank, decode_stream, composition_frame

W = ROOT / 'work/sprite_style_unification_20261107'
D = Path(__file__).parent
O = D / 'rin_extension/validation_scope303'
O.mkdir(exist_ok=True)
read = lambda p: json.loads(p.read_text('utf8'))
sha = lambda b: hashlib.sha256(b).hexdigest()
plan_path = W / 'staging_rn_v15.json'
plan = read(plan_path)
assert plan['sync_zero_selection_body'] is True
body_path = ROOT / plan['resources']['PL01_U.ARC']['path']
body = body_path.read_bytes()
assert sha(body) == plan['resources']['PL01_U.ARC']['after'] == '1dde3e8793628d5f38b4318543e8d9f3a22b37ad350622a96f4f4f63e92610b9'
ui_path = ROOT / plan['resources']['ST0E_U1.ARC']['path']
ui = ui_path.read_bytes()
assert sha(ui) == plan['resources']['ST0E_U1.ARC']['after']

def static_frame(tex, parts, ref):
    canvas = np.zeros((384, 384), np.uint8)
    comp = composition_frame(parts, 0, ref)
    for p in comp['parts']:
        t = p['page'] * 256 + p['tile']
        z = np.zeros((16, 16), np.uint8)
        for y in range(16):
            for x in range(16):
                off = (t // 16 * 16 + y) * 128 + t % 16 * 8 + x // 2
                z[y, x] = (tex[off] >> (4 * (x % 2))) & 15
        if p['flip_x']: z = z[:, ::-1]
        if p['flip_y']: z = z[::-1]
        assert p['clut'] == 0
        x, y = 160 + p['x'], 160 + p['y']
        target = canvas[y:y+16, x:x+16]
        mask = z > 0
        target[mask] = z[mask]
    return canvas

copies = []
for ref, (bank, n) in SELECTION_MAPPING.items():
    expected = render(body, bank, bank * 5, n)[0]
    actual = static_frame(entry(ui, 0x10102)[:40960], entry(ui, 10), ref)
    assert np.array_equal(expected, actual), (ref, bank, n)
    copies.append({'ui_ref': ref, 'player': f'b{bank}_{n:03}', 'indexed_pixels_and_origin_exact': True})
assert len(copies) == 32
selection = {
    'passed': True, 'scope': 'v15 준비 조합의 현재 린303 본체와 기존 선택32사본을 제작 함수 없이 읽어 색인·원점을 대조했다.',
    'plan': str(plan_path.relative_to(ROOT)), 'plan_sha256': sha(plan_path.read_bytes()),
    'body_path': str(body_path.relative_to(ROOT)), 'body_sha256': sha(body),
    'selection_path': str(ui_path.relative_to(ROOT)), 'selection_sha256': sha(ui),
    'copies': copies, 'copies_exact': len(copies), 'additional_selection_repaint_needed_for_current_body': False,
    'ui38_meaning': 'UI38은 b1_11 가는 귀환빛이다. {38:0}은 CLUT0 강제이며 idle0 프레임 별칭이 아니다.',
    'runtime_verified': False,
    'limits': ['이번 검사는 현재32사본의 색인/원점 일치만 재확인했다. 비소유 타일·flip GPU 의미는 기존 selection_sync_independent01 증거이며 이번에 재검사하지 않았다.', 'COL0E 팔레트 및 실제 선택 화면은 이번에 새 실행하지 않았다.']
}
(O / 'selection_current.json').write_text(json.dumps(selection, ensure_ascii=False, indent=2) + '\n', 'utf8')

newgfx, newparts = entry(body, 2), entry(body, 3)
newframes = {b:graphics_bank(newgfx, b)['frames'] for b in (0,1)}
def raw(g, f):
    return decode_stream(g, f['offset'], f['limit'], f['tile_count'] * 128).data
def geometry(c):
    return [(p['flags'],p['tile'],p['x'],p['y']) for p in c['parts']]

sessions = []
same_display = set()
same_upload_and_display = set()
observed_old = set()
for version in (10,11):
    summary_path = W / f'runtime/rin_checkpoint{version}_summary.json'
    summary = read(summary_path)
    old_plan = read(W / f'staging_rn_v{version}.json')
    old_path = ROOT / old_plan['resources']['PL01_U.ARC']['path']
    old = old_path.read_bytes()
    assert sha(old) == summary['rin_pl01_sha256'] == old_plan['resources']['PL01_U.ARC']['after']
    gfx, parts = entry(old,2), entry(old,3)
    frames = {b:graphics_bank(gfx,b)['frames'] for b in (0,1)}
    rows = []
    assert entry(old,9) == entry(body,9)
    for bank, ref in summary['verified_bank_frames']:
        key = f'b{bank}_{ref:03}'
        before, after = render(old,bank,bank*5,ref)[0], render(body,bank,bank*5,ref)[0]
        display = np.array_equal(before, after)
        f,nf = frames[bank][ref],newframes[bank][ref]
        payload = f['tile_count']==nf['tile_count'] and raw(gfx,f)==raw(newgfx,nf)
        geom = geometry(composition_frame(parts,bank*5,ref)) == geometry(composition_frame(newparts,bank*5,ref))
        observed_old.add(key)
        if display: same_display.add(key)
        if display and payload and geom: same_upload_and_display.add(key)
        rows.append({'ref':key, 'same_current_display_and_normal_palette':bool(display), 'same_current_decoded_upload':bool(payload), 'same_current_part_geometry':bool(geom)})
    sessions.append({
        'source_summary':str(summary_path.relative_to(ROOT)), 'summary_sha256':sha(summary_path.read_bytes()),
        'disc_version':summary['disc_version'], 'disc_sha256':summary['disc_sha256'], 'body_sha256':sha(old),
        'actual_window_frames':summary['actual_window_frames'], 'normal_only':True,
        'root_actually_viewed_capture_sheets':len(summary['root_actually_viewed']),
        'verified_then':len(rows), 'same_display_now':sum(r['same_current_display_and_normal_palette'] for r in rows),
        'same_upload_geometry_and_display_now':sum(all(r[k] for k in ('same_current_display_and_normal_palette','same_current_decoded_upload','same_current_part_geometry')) for r in rows),
        'references':rows, 'unverified_transient_events':summary['unverified_transient_events']
    })

groupmap=read(D/'group_map.json')['rin']
body_refs=set(r for g in groupmap.values() for r in g['body_or_head_refs'])
assert len(body_refs)==315
groups=[]
for name,g in groupmap.items():
    refs=set(g['body_or_head_refs'])
    if not refs:continue
    groups.append({'group':name, 'body_refs':sorted(refs), 'prior_same_display_evidence':sorted(refs&same_display), 'no_same_display_live_evidence_in_v10_v11':sorted(refs-same_display)})

report={
    'scope':'기존 v10/v11 정상색 린 실기 기록을 현재303 자원과 읽기 대조한 검증 범위 장부. 새 게임 검증을 수행하지 않았다.',
    'current_body_sha256':sha(body), 'sessions':sessions,
    'historically_observed_unique_refs':len(observed_old),
    'current_display_exact_to_at_least_one_prior_observed_ref':len(same_display),
    'current_upload_geometry_and_display_exact_to_prior_observation':len(same_upload_and_display),
    'current_changed_since_all_historical_observations':sorted(observed_old-same_display),
    'groups':groups,
    'priority_manual_checks':[
        {'group':'낙봉파 최신9', 'refs':[f'b1_{i:03}' for i in (177,178,179,180,181,186,187,188,189)], 'reason':'v10에 같은 번호가 관측됐지만 이번303에서 몸체·신발이 달라졌다. 양방향 준비 구체→발동182..185→회복186..189 동시 화면을 새 통합본으로 확인한다.'},
        {'group':'신규 탑승/체이서', 'refs':[f'b1_{i:03}' for i in range(14,42)], 'reason':'차량 몸체·가림·원리본 위상과 조종석75/77 높이는 단독 미술 시트만으로 완료할 수 없다. 탑승 머리19도 해당 장면에서 함께 확인한다.'},
        {'group':'사다리와 지상 질풍아', 'refs':['b0_197','b0_212']+groupmap['shippuuga']['body_or_head_refs'], 'reason':'197/212는 v11 미관측. 지상 질풍아 b0_155/156/158/160/162/164/166/168/170/172는 그 뒤 새214/222에서 바뀌었으므로 이전 v11 같은 번호를 현재 그림의 실기로 세지 않는다. b1_156/158 용염인 후속과 혼동하지 않는다.'},
        {'group':'등장·승리·회복', 'refs':[f'b0_{i:03}' for i in range(247,254)]+[f'b1_{i:03}' for i in range(1,9)]+[f'b1_{i:03}' for i in range(128,132)], 'reason':'최신 섬광/몸체 전환과 승리/회복은 별도 실기 표본이 필요하다.'},
        {'group':'레드 린', 'refs':[], 'reason':'여기 읽은 두 실기는 정상색만이다. 레드 팔레트 전체 시각 재검토58판 중29판은 정적 근거이며 레드 실기를 대신하지 않는다.'}
    ],
    'limits':[
        '과거 업로드와 현재 그림이 같아도 현재BIN을 새로 실행한 증거가 되지 않는다. 자원 동일성의 범위만 표시한다.',
        '약16fps 캡처·비동기 RAM/VRAM 표본의 전환 미안정 사건을 삭제하거나 전체60Hz 검증으로 확대하지 않았다.',
        '이 장부는 v10/v11 두 인게임 요약을 대조한다. 다른 시기의 선택화면 실기나 외부 무기 객체의 전수 검증을 합산하지 않는다.',
        '부분 VRAM b1_42..49는 이전 업로드 의존성이 있으므로 독립 완성체/미사용으로 판정하지 않는다.'
    ],
    'runtime_executed_this_audit':False, 'all_runtime_complete':False, 'user_accepted':False
}
(O/'runtime_scope.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf8')
print(json.dumps({'selection_copies':32,'runtime_old_unique':len(observed_old),'same_display':len(same_display),'same_payload_geometry':len(same_upload_and_display),'selection_report_sha256':sha((O/'selection_current.json').read_bytes()),'runtime_report_sha256':sha((O/'runtime_scope.json').read_bytes())}))
