"""Read current Nana ladder graphics, compositions and prior original-code proof."""
from pathlib import Path
import collections
import hashlib
import json
import sys
import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from scripts.export_x_consistency import Archive
from src.psx_player import composition_frame, decode_stream, indexed_atlas, bank_offsets

D = Path(__file__).parent
OUT = D / 'nana_ladder_relations01'
OUT.mkdir(exist_ok=True)
SOURCE = D.parent / 'nana_audit/hurt_repaint/packed_hurt_candidate_v1/PL00_U.ARC'
EXPECTED = '978a9fc18e31f221d20568d747078f098f37fb120c303c64afc916442721be9f'
PBS = (0, 5, 6, 7, 8)
REFS = list(range(143, 156)) + [183]
sha = lambda b: hashlib.sha256(b).hexdigest()
rel = lambda p: p.relative_to(ROOT).as_posix()
data = SOURCE.read_bytes()
assert sha(data) == EXPECTED
a = Archive(data)

def bbox(mask):
    ys, xs = np.nonzero(mask)
    return [int(xs.min()-160), int(ys.min()-160), int(xs.max()+1-160), int(ys.max()+1-160)] if len(xs) else None

def mirror(v, k):
    out = np.zeros_like(v)
    m = v[:, :, 3] > 0 if v.ndim == 3 else v > 0
    ys, xs = np.nonzero(m)
    tx = 320 - xs + k
    assert np.all((tx >= 0) & (tx < 384))
    out[ys, tx] = v[ys, xs]
    return out

def delta(v, w):
    m = np.any(v != w, axis=2) if v.ndim == 3 else v != w
    av, aw = (v[:, :, 3] > 0, w[:, :, 3] > 0) if v.ndim == 3 else (v > 0, w > 0)
    return {'changed_pixels': int(m.sum()), 'changed_alpha_pixels': int(np.count_nonzero(av != aw)), 'bbox_world': bbox(m)}

def cp(n, pb):
    return composition_frame(a.c, pb, n)

def signature(n, pb):
    return [(p['flags'], p['tile'], p['x'], p['y']) for p in cp(n, pb)['parts']]

def frame_keys(n):
    f = a.banks[0]['frames'][n]
    return f['offset'], f['tile_count']

all_raw_owners = collections.defaultdict(list)
for gb, bank in enumerate(a.banks):
    for f in bank['frames']:
        all_raw_owners[(f['offset'], f['tile_count'])].append([gb, f['index']])

groups = []
for key in sorted(set(frame_keys(n) for n in REFS)):
    owners = all_raw_owners[key]
    f = next(a.banks[gb]['frames'][n] for gb, n in owners)
    raw = decode_stream(a.g, f['offset'], f['limit'], f['tile_count'] * 128)
    atlas = np.frombuffer(indexed_atlas(raw.data, f['tile_count'])[0], np.uint8).reshape(-1, 256)
    consumed = {}
    for gb, n in owners:
        if gb != 0:
            continue
        used = set()
        layers = {}
        for pb in PBS:
            ps = cp(n, pb)['parts']
            tiles = sorted({p['page'] * 256 + p['tile'] for p in ps})
            used.update(tiles)
            layers[str(pb)] = tiles
        consumed[str(n)] = {'layers': layers, 'union': sorted(used)}
    union = sorted(set(t for v in consumed.values() for t in v['union']))
    groups.append({'entry2_offset': key[0], 'tile_count': key[1], 'owners': owners,
                   'decoded_sha256': sha(raw.data), 'compressed_end': raw.end,
                   'consumed_tiles': consumed, 'whole_group_tile_union': union,
                   'unused_by_player5_layers': sorted(set(range(key[1])) - set(union)),
                   'tile_sha256': {str(t): sha(atlas[t//16*16:t//16*16+16, t%16*16:t%16*16+16].tobytes()) for t in union}})

frames = []
for n in REFS:
    f = a.banks[0]['frames'][n]
    layers = {}
    for pb in PBS:
        v = a.layer(n, pb)[0]
        ps = cp(n, pb)['parts']
        records = [p['record_offset'] for p in ps]
        owners = [m for m in range(cp(n, pb)['bank_frame_count'])
                  if [p['record_offset'] for p in cp(m, pb)['parts']] == records] if records else []
        layers[str(pb)] = {'parts': ps, 'exact_record_range_owners': owners,
                           'indexed_sha256': sha(v.tobytes()), 'opaque': int(np.count_nonzero(v)), 'bbox_world': bbox(v > 0)}
    frames.append({'ref': n, 'stream': f, 'layers': layers})

pairs = []
for s, t, expected_k in [(144, 145, -1), (146, 147, 0), (149, 148, 0), (151, 152, 0)]:
    layers = {}
    for pb in PBS:
        x, y = a.layer(s, pb)[0], a.layer(t, pb)[0]
        tests = [{'k': k, **delta(mirror(x, k), y)} for k in range(-3, 4)]
        layers[str(pb)] = {'exact_k': [x['k'] for x in tests if not x['changed_pixels']],
                           'expected_k_comparison': next(v for v in tests if v['k'] == expected_k),
                           'best': min(tests, key=lambda v: v['changed_pixels'])}
    forms = {}
    for mask, arm, label in [(0, 1, 'base'), (15, 1, 'fourth_arm1'), (15, 2, 'fourth_arm2')]:
        x = np.asarray(a.composite(s, mask, arm)[0]); y = np.asarray(a.composite(t, mask, arm)[0])
        forms[label] = delta(mirror(x, expected_k), y)
    pairs.append({'source': s, 'target': t, 'world_x_rule': f'-source_x{expected_k:+d}',
                  'same_raw_stream': frame_keys(s) == frame_keys(t), 'layers': layers, 'forms': forms})

shotcomparisons = []
for s, t in [(149, 150), (149, 155), (150, 155), (154, 155)]:
    forms = {}
    for mask, arm, label in [(0, 1, 'base'), (15, 1, 'fourth_arm1'), (15, 2, 'fourth_arm2')]:
        x = np.asarray(a.composite(s, mask, arm)[0]); y = np.asarray(a.composite(t, mask, arm)[0])
        forms[label] = delta(x, y)
    shotcomparisons.append({'source': s, 'target': t,
                            'same_raw_stream': frame_keys(s) == frame_keys(t),
                            'layers': {str(pb): delta(a.layer(s, pb)[0], a.layer(t, pb)[0]) for pb in PBS},
                            'forms': forms})

historic = ROOT / 'work/ver_rin_nana/nana_art/ladder_v1/production01'
meta = json.loads((historic / 'art.json').read_text('utf8'))
gunproof = []
for n in (150, 155):
    rec = next(q for q in meta['frames'] if q['frame'] == n)
    g = np.asarray(Image.open(historic / f'gun_{n:03}.png'))
    full = np.zeros((384, 384), np.uint8)
    full[120:200, 112:208] = g
    yy, xx = np.nonzero(full)
    edge = xx == xx.min()
    muzzle = [int(xx.min()-160), float(np.median(yy[edge])-160)]
    # Authored gun can be covered by body; report true overlap separately.
    vg = full > 0
    base = a.layer(n, 0)[0]
    mismatches = vg & (full != base)
    forms = {}
    for mask, arm, label in [(0, 1, 'base'), (15, 1, 'fourth_arm1'), (15, 2, 'fourth_arm2')]:
        rgba = np.asarray(a.composite(n, mask, arm)[0])
        gx, my = rec['original_muzzle_world']
        X, Y = np.meshgrid(np.arange(384)-160, np.arange(384)-160)
        roi = (X >= gx) & (X < gx+8) & (Y >= my-3) & (Y <= my+5)
        forms[label] = {'roi_world': [gx, my-3, gx+8, my+6], 'rgba_sha256': sha(rgba[roi].tobytes()),
                        'base_rgba_exact': bool(np.array_equal(rgba[roi], np.asarray(a.composite(n, 0, 1)[0])[roi]))}
    gunproof.append({'ref': n, 'source_image': rel(historic/f'gun_{n:03}.png'),
                     'source_sha256': sha((historic/f'gun_{n:03}.png').read_bytes()),
                     'historical_original_muzzle_world': rec['original_muzzle_world'],
                     'current_source_left_edge_world': muzzle, 'source_gun_opaque': int(vg.sum()),
                     'current_base_source_mismatches': int(mismatches.sum()),
                     'mismatch_bbox': bbox(mismatches), 'forms_first8column_window': forms})

sheets = []
def sheet(name, refs):
    crop = (112, 112, 208, 208); scale = 3; cw, ch = 306, 316
    board = Image.new('RGB', (cw*len(refs), ch*2), '#263345'); dr = ImageDraw.Draw(board)
    for row, mask in enumerate((0, 15)):
        for col, n in enumerate(refs):
            im = a.composite(n, mask, 2)[0].crop(crop).resize((288, 288), Image.Resampling.NEAREST)
            board.paste(im, (col*cw+8, row*ch+24), im)
            dr.text((col*cw+8, row*ch+5), f'current Nana {n} mask{mask}', fill='white')
    p = OUT / name; board.save(p)
    sheets.append({'path': rel(p), 'sha256': sha(p.read_bytes()), 'refs': refs, 'scale': scale, 'crop_world': [-48, -48, 48, 48]})

sheet('shots.png', [0, 149, 150, 155, 154])
sheet('mirror_a.png', [144, 145, 146, 147])
sheet('mirror_b.png', [149, 148, 151, 152])
shotold = D / 'ultimate_ladder_shots01/report.json'
mirrorold = D / 'ultimate_ladder_aliases01/report.json'
old = json.loads(shotold.read_text('utf8'))
result = {'scope': '최신 나나 기본/포스 사다리14의 읽기 전용 공유·반전·사격 관계 조사. 새 원화/패킹/실기 검증은 아니다.',
          'source': rel(SOURCE), 'source_sha256': EXPECTED, 'graphics_groups': groups, 'frames': frames,
          'mirror_pairs': pairs, 'shooting_comparisons': shotcomparisons, 'pistol_source': gunproof,
          'original_code_evidence': [{'path': rel(p), 'sha256': sha(p.read_bytes())} for p in (shotold, mirrorold)],
          'original_92_93': old['sequences'][-2:],
          'historic_art_metadata': {'path': rel(historic/'art.json'), 'sha256': sha((historic/'art.json').read_bytes())},
          'producer_code_read_only': [{'path': rel(ROOT/p), 'sha256': sha((ROOT/p).read_bytes())} for p in
              ['scripts/normalize_nana_ladder.py', 'scripts/prepare_nana_fourth_ladder_art.py',
               'work/sprite_style_unification_20261107/nana_audit/native_restore/prepare_native.py']],
          'sheets': sheets, 'actual_sheet_views': True,
          'view_notes': 'shots、mirror_a、mirror_b의 현재 기본/포스 정지 비교3판을 실제 열람했다. 150/155의 몸과 다리는 동일하고 팔·권총만 뒤/위로 이동하며,154는 별도 웅크린 사다리 끝 자세로 읽힌다. 네 쌍의 손발 교대 반전도 보았다. 새 원화의 최종 미술 수용이나 실제 사다리 접촉 검증은 아니다.',
          'conclusions': [
              '14참조는9개 원시 스트림을 사용한다. 그룹은143 /144·145 /146·147 /148·149·150 /151·152 /153 /154 /155 /183이며 이 스트림의 다른 은행 또는 대상 밖 소유자는 없다.',
              '현재 나나 네 반전쌍은5층 전체와 기본/포스 arm1·arm2 합성 모두 정확 반전이다.145=-144-1,147=-146,148=-149,152=-151이며 world_y는 같다. 원US Ultimate overlay의 발끝 예외를 현재PL00의 실패로 가져오지 않는다.',
              '현재150과155는149의 하체 및 원래leg8을 정확히 공유한다. 전체합성 차이는150 x[-24,-2),155 x[-21,1), 공통y[-14,-2)의 팔/총·머리 가림뿐이다.154는155의 원래 몸체 짝이 아니다.',
              '155의 원시 스트림은 별도지만 현재 그림은149 공통몸체+다른 팔/총이다. 기존 제작코드도 이 정책을 명시한다. 원US155의 전신 반동을 동일 복원한 것으로 보고하지 않는다.',
              '역사 gun150/155의84개 불투명 색인이 각각 현재base와 모두 같다. 총구(-24,-9)→(-21,-13)이고 첫8열 창은 기본/포스 arm1·arm2 사이 및 두 사격에서 같은RGBA이다. 원총구에 맞추는 새팔 제작에 사용할 수 있는 현재 위치 근거다.',
              '원표92/93은150→155→150이며93 첫 유지시간은 호출자가 attack_pose_timer-8로 덮는다. 원표/호출자 증거는 기존 원US 보고에 연결하며 새 CPU 실행으로 세지 않는다.'
          ],
          'limits': ['표시 비교와 원래 코드 근거 재사용이다. 새 MIPS/게임 실행과 원화 제작은 하지 않았다.',
                     'unused_by_player5_layers는 현재 그룹의 다섯 플레이어층에 한정한 관찰이며 자동 삭제 허용 목록이 아니다.']}
assert SOURCE.read_bytes() == data
(OUT/'report.json').write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n', encoding='utf8')
print(json.dumps({'report_sha256': sha((OUT/'report.json').read_bytes()),
                  'groups': [{'refs': g['owners'], 'tiles': g['tile_count']} for g in groups],
                  'mirrors': [{k:p[k] for k in ('source','target','same_raw_stream','forms')} for p in pairs],
                  'shots': shotcomparisons, 'gun': gunproof}, ensure_ascii=False))
