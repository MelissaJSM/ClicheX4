"""PL02 피격13 독립 reader. 제작/정합/패킹 모듈은 호출하지 않는다."""
from pathlib import Path
import argparse, collections, hashlib, json, sys
import numpy as np
from PIL import Image, ImageDraw
from scipy.ndimage import binary_dilation

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from scripts.export_x_consistency import Archive
from scripts.discover_inputs import psx_arc
from src.psx_player import decode_stream, composition_frame, bank_offsets, indexed_atlas, compose_indices
from src.psx_ui_atlas import local_composition

D = Path(__file__).parent
H = D.parent / 'shibuki_audit'
T = H / 'ultimate_hurt_effect_probe02'
C = H / 'ultimate_hurt_common_probe02'
PBS = (0, 5, 6, 7, 8)
REFS = set(range(106, 115)) | set(range(233, 237))
RESERVED = {105, *range(175, 183)}
sha = lambda b: hashlib.sha256(b).hexdigest()
read = lambda p: json.loads(p.read_text('utf8'))
rel = lambda p: p.relative_to(ROOT).as_posix()
tracked = {}

def blob(p):
    v = p.read_bytes()
    tracked[rel(p)] = sha(v)
    return v

def png(p):
    blob(p)
    return np.asarray(Image.open(p))

def npy(p):
    blob(p)
    return np.load(p)

def parts(ar, pb, n):
    return composition_frame(ar.c, pb, n)['parts']

def sig(p):
    return p['flags'], p['tile'], p['x'], p['y']

def raw(ar, gb, n):
    f = ar.banks[gb]['frames'][n]
    return decode_stream(ar.g, f['offset'], f['limit'], f['tile_count'] * 128).data

def tile(ar, n, t):
    f = ar.banks[0]['frames'][n]
    at = np.frombuffer(indexed_atlas(raw(ar, 0, n), f['tile_count'])[0], np.uint8).reshape(-1, 256)
    x, y = t % 16 * 16, t // 16 * 16
    return at[y:y+16, x:x+16]

def render(ar, n, pb, ps):
    z = np.zeros((384, 384), np.uint8)
    if not ps:
        return z
    cp = {'parts': ps}
    if pb:
        cp = local_composition(cp)
    px, size, box, _ = compose_indices(raw(ar, 0, n), ar.banks[0]['frames'][n]['tile_count'], cp, allowed_cluts={0, 1, 2, 3})
    sm = np.frombuffer(px, np.uint8).reshape(size[1], size[0])
    y, x = np.nonzero(sm)
    z[y+box[1]+160, x+box[0]+160] = sm[y, x]
    return z

def polygons(items):
    out = Image.new('1', (384, 384))
    draw = ImageDraw.Draw(out)
    for pts in items:
        draw.polygon([(x+160, y+160) for x, y in pts], fill=1)
    return np.array(out, bool)

def color(ar, z, start=0):
    tab = np.array([[(int(w) >> s & 31)*255//31 for s in (0, 5, 10)] + [0 if i % 16 == 0 else 255]
                    for i, w in enumerate(ar.words[start:])], np.uint8)
    return tab[z]

def silhouette(n, res, body):
    z = res.copy()
    mask = body > 0
    ring = binary_dilation(mask)
    if n == 112:
        z[ring] = 6
        z[mask] = 14
    elif n == 113:
        z[ring] = 1
    else:
        z[ring] = 1
        z[mask] = 3
        z[np.isin(body, (1, 2, 4, 8, 15)) & mask] = 5
        z[np.isin(body, (6, 9)) & mask] = 1
    return np.where(z, z+32, 0).astype(np.uint8)

def flash(body):
    z = np.zeros_like(body)
    z[binary_dilation(body > 0)] = 9
    z[body > 0] = 14
    return z

def verify_sources(a):
    source_path = D / 'shibuki_hurt_sources01/report.json'
    assert sha(blob(source_path)) == '202898054ae9061a626b1a9088bfde79bf3ef15339963acfc3f4d3d0c49b348c'
    src = read(source_path)['archives'][1]
    assert src['source_sha256'] == sha(a.data)
    assert sha(blob(T / 'manifest.json')) == '7e1310d1e8411d66d539d2520e36413a978ed5dd0ca5b2650ad0f87f0a84cc4d'
    meta = read(T / 'manifest.json')
    assert sha(blob(C / 'report.json')) == meta['body_report_sha256']
    cm = read(C / 'report.json')
    for p, h in meta['source_arrays'].items():
        assert sha(blob(ROOT / p)) == h
    rgb = np.array([[(int(w) >> s & 31)*255//31 for s in (0, 5, 10)] for w in a.words], np.int32)
    lut = np.r_[0, 1+((rgb[17:32, None] - rgb[None, 1:16])**2).sum(2).argmin(1)].astype(np.uint8)
    assert lut.tolist() == cm['palette_map']
    before, after, expected = {}, {}, {}
    common_rows = []
    for q in cm['rows']:
        n = q['ref']
        source = ROOT / q['source']
        for name, h in q['source_files'].items():
            assert sha(blob(source / name)) == h
        bef = png(source / f'before_{n:03}_indices.png')
        aft = png(source / f'after_{n:03}_indices.png').copy()
        arm = polygons(q['arm_polygons'])
        if q['local_arm_source']:
            donor = png(H / q['local_arm_source'])
            aft[arm] = donor[arm]
        head = polygons(q['head_polygons'])
        legs = polygons(q['leg_polygons'])
        hands = np.zeros_like(head)
        for x0, y0, x1, y1 in q['hand_skin_rectangles']:
            hands[y0+160:y1+160, x0+160:x1+160] = True
        hands &= np.isin(bef, (10, 11, 12, 13))
        if n == 106:
            hands[169:172, 163:168] = True
        if n == 110:
            head[173, 163] = True
        common = head | legs | hands
        aft[common] = lut[bef][common]
        assert np.array_equal(bef, png(C / f'before_{n:03}_indices.png'))
        assert np.array_equal(aft, png(C / f'after_{n:03}_indices.png'))
        assert not np.any((aft > 0) & (bef == 0))
        same = np.all(color(a, bef, 16) == color(a, aft), axis=2)
        layers = {0: aft, 5: np.where(same, 0, bef).astype(np.uint8)}
        layers.update({pb: np.zeros_like(aft) for pb in (6, 7, 8)})
        expected[n] = layers
        before[n], after[n] = bef, aft
        common_rows.append({'ref': n, 'registered_native_to_common_exact': True,
                            'common_mask_pixels': int(common.sum()), 'new_arm_polygon_pixels': int(arm.sum()),
                            'old_art_copied': False, 'after_outside_before': 0})
    effects = []
    base_path = H / 'prepared_hurt_base01/PL00_U.ARC'
    base_data = blob(base_path)
    assert sha(base_data) == '87e7d1db40c2380815ca2986bc27382db73f718d9c338d2eaad776372a2e257b'
    base = Archive(base_data)
    for q in src['effects']:
        n, core = q['ref'], q['core']
        if n in (107, 108):
            fx = npy(ROOT / q['effect_npy'])
            assert np.array_equal(fx, render(base, n, 0, q['original_effect_parts']))
            assert set(np.unique(fx)) == {0, 8} and np.count_nonzero(fx) == {107: 99, 108: 76}[n]
            policy = '원US 전체 전기99/76px 복원. 과거 몸체가 가리던22~25px까지 동일가림이라고 주장하지 않음.'
        else:
            fx = render(a, n, 0, q['actual_CLUT2_records'])
            assert np.count_nonzero(fx) == 194
            policy = '현재PL02 실제12개 CLUT2기록/194px. 원US기록이나 기본202px와 혼용하지 않음.'
        layers = {pb: v.copy() for pb, v in expected[core].items()}
        layers[0] = np.where(fx, fx, layers[0]).astype(np.uint8)
        layers[5] = np.where(fx, fx % 16, layers[5]).astype(np.uint8)
        for idx in np.unique(fx[fx > 0]):
            assert a.words[int(idx)] == a.words[16+int(idx) % 16]
        expected[n] = layers
        effects.append({'ref': n, 'pixels': int(np.count_nonzero(fx)), 'exact_source': True, 'policy': policy})
    af, bf = flash(after[106]), flash(before[106])
    expected[109] = {0: af, 5: np.where(af != bf, bf, 0).astype(np.uint8)}
    expected[109].update({pb: np.zeros_like(af) for pb in (6, 7, 8)})
    derived = []
    old_before110 = a.layer(110, 0)[0].copy()
    v = a.layer(110, 5)[0]
    old_before110[v > 0] = v[v > 0]
    for q in src['silhouettes112_114']:
        n = q['ref']
        assert not q['small_components_deleted_coordinates']
        res = npy(ROOT / q['residual_path'])
        assert np.array_equal(silhouette(n, res, old_before110), a.layer(n, 0)[0]), ('historical silhouette', n)
        v = silhouette(n, res, before[110])
        expected[n] = {0: v, **{pb: np.zeros_like(v) for pb in PBS[1:]}}
        derived.append({'ref': n, 'parent_rule_exact': True, 'new_before110_rule_exact': True,
                        'source_external_pixels': int(np.count_nonzero(res)), 'new_small_components_deleted': False})
    auras = []
    for q in src['aura235_236']:
        n = q['ref']
        fx = npy(ROOT / q['historical_effect_path'])
        assert np.count_nonzero(fx) == q['historical_original_effect_pixels']
        layers = {pb: v.copy() for pb, v in expected[234].items()}
        layers[0] = np.where(layers[0], layers[0], fx).astype(np.uint8)
        expected[n] = layers
        auras.append({'ref': n, 'whole_historical_effect_pixels': int(np.count_nonzero(fx)),
                      'before_visible': int(np.count_nonzero((fx > 0) & (before[234] == 0))),
                      'after_visible': int(np.count_nonzero((fx > 0) & (after[234] == 0))),
                      'whole_effect_not_moved_or_recolored': True, 'old_costume_fragments_not_copied': True})
    assert set(expected) == REFS
    for n, layers in expected.items():
        for pb, v in layers.items():
            assert sha(v.tobytes()) == meta['targets'][str(n)][str(pb)]
            assert np.array_equal(v, png(T / f'{n:03}_bank{pb}_indices.png')), ('target', n, pb)
    return expected, src, base, {'common_body_reconstruction': common_rows, 'effects': effects,
                               'flash109_each_costume_14_and9': True, 'CLUT2_derived': derived, 'auras': auras}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--candidate-folder')
    ap.add_argument('--candidate-sha256')
    ap.add_argument('--lock-sha256')
    args = ap.parse_args()
    parent = H / 'prepared_ultimate_ladder01/PL02_U.ARC'
    old = blob(parent)
    assert sha(old) == '03a675626035b93ad2e2feef8dd643365ed8a3e1a61a1eb02a476063e2c55e8a'
    a = Archive(old)
    targets, src, base, sourceproof = verify_sources(a)
    o = D / 'shibuki_ultimate_hurt13_independent01'
    o.mkdir(exist_ok=True)
    if not args.candidate_folder:
        report = {'passed': True, 'scope': '새 등록8그림→공통부→65목표층과 원효과 출처만 독립 재구성. ARC 검사는 아직 아님.',
                  'source_proof': sourceproof, 'inputs': tracked, 'candidate_checked': False}
        (o / 'source_report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n', 'utf8')
        print(json.dumps({'source_passed': True, 'sha256': sha((o / 'source_report.json').read_bytes())}))
        return
    p = ROOT / args.candidate_folder
    blob(p / 'proposal.json')
    proposal = read(p / 'proposal.json')
    candidate = p / 'PL02_U.ARC'
    new = blob(candidate)
    assert sha(new) == args.candidate_sha256
    assert proposal['files']['PL02_U.ARC']['after'] == sha(new)
    assert proposal['sequential_parent']['sha256'] == sha(old)
    lockpath = ROOT / proposal['target_lock']
    assert sha(blob(lockpath)) == args.lock_sha256
    lock = read(lockpath)
    assert lock['parent_sha256'] == sha(old) and lock['candidate_sha256'] == sha(new) and set(lock['refs']) == REFS
    for name, h in lock['files'].items():
        assert sha(blob(ROOT / name)) == h, name
    b = Archive(new)
    counts = collections.Counter()
    assert len(old) == len(new) and a.p == b.p
    ae, be = psx_arc(old), psx_arc(new)
    assert [(q['type'], q['offset'], q['size']) for q in ae] == [(q['type'], q['offset'], q['size']) for q in be]
    allow = np.zeros(len(old), bool)
    for e in ae:
        if int(e['type'], 16) in (2, 3):
            allow[e['offset']:e['offset']+e['size']] = True
    assert not np.any((np.frombuffer(old, np.uint8) != np.frombuffer(new, np.uint8)) & ~allow)
    assert bank_offsets(a.g, allow_aliases=True) == bank_offsets(b.g, allow_aliases=True)
    assert bank_offsets(a.c) == bank_offsets(b.c)
    for gb, (ab, bb) in enumerate(zip(a.banks, b.banks)):
        assert (ab['base'], ab['end'], len(ab['frames'])) == (bb['base'], bb['end'], len(bb['frames']))
        if gb:
            assert a.g[ab['base']:ab['end']] == b.g[bb['base']:bb['end']]
            counts['other_graphics_banks_byte_exact'] += 1
        for f, g in zip(ab['frames'], bb['frames']):
            n = f['index']
            assert n == g['index']
            r0, r1 = raw(a, gb, n), raw(b, gb, n)
            counts['raw_checked'] += 1
            if gb == 0 and n in REFS:
                assert g['tile_count'] == 32
            else:
                assert r0 == r1 and f['tile_count'] == g['tile_count']
                counts['non_target_raw_exact'] += 1
    for n in range(237):
        if n in RESERVED:
            continue
        for pb in PBS:
            z = b.layer(n, pb)[0]
            want = targets[n][pb] if n in REFS else a.layer(n, pb)[0]
            assert np.array_equal(z, want), (n, pb)
            counts['layers_checked'] += 1
            counts['target_layers_exact' if n in REFS else 'non_target_layers_exact'] += 1
    edges = []
    for pb in range(len(bank_offsets(a.c))):
        for n in range(composition_frame(a.c, pb, 0)['bank_frame_count']):
            op, bp = parts(a, pb, n), parts(b, pb, n)
            if pb in PBS and n in REFS:
                assert len(bp) <= 24
                for q in bp:
                    t = q['tile'] + q['page']*256
                    assert 0 <= t < 32
                    v = tile(b, n, t)
                    u = t % 16 == 0 and bool(v[:, 0].any())
                    vv = q['flip_y'] and t // 16 == 0 and bool(v[0].any())
                    if u or vv:
                        assert any(sig(q) == sig(z) for z in op) and np.array_equal(v, tile(a, n, t)), ('new GPU edge', n, pb, t)
                        edges.append({'ref': n, 'bank': pb, 'part': sig(q), 'U': bool(u), 'V': bool(vv)})
                    counts['target_GPU_parts_checked'] += 1
            else:
                assert [sig(q) for q in op] == [sig(q) for q in bp]
                counts['non_target_compositions_exact'] += 1
    preserved_effects = []
    for q in src['effects']:
        n, core = q['ref'], q['core']
        ps = q['original_effect_parts'] if n in (107, 108) else q['actual_CLUT2_records']
        origin = base if n in (107, 108) else a
        assert b.banks[0]['frames'][core]['offset'] == b.banks[0]['frames'][n]['offset']
        assert [sig(z) for z in parts(b, 0, n)] == [sig(z) for z in parts(b, 0, core)] + [sig(z) for z in ps]
        for t in sorted({z['tile'] for z in ps}):
            assert np.array_equal(tile(origin, n, t), tile(b, n, t))
            counts['whole_original_effect_tile_uses_exact'] += 1
        old_fx = render(origin, n, 0, ps)
        assert np.array_equal(old_fx, render(b, n, 0, ps))
        # layer5 may move a full source tile to a GPU-safe slot; shape/flags/xy stay exact.
        core5 = parts(b, 5, core)
        actual5 = parts(b, 5, n)
        assert [sig(z) for z in actual5[:len(core5)]] == [sig(z) for z in core5]
        effect5 = actual5[len(core5):]
        assert len(effect5) == len(ps)
        copies = []
        for s, d in zip(ps, effect5):
            assert (s['flags'], s['x'], s['y']) == (d['flags'], d['x'], d['y'])
            assert np.array_equal(tile(origin, n, s['tile']), tile(b, n, d['tile']))
            copies.append({'source_tile': s['tile'], 'destination_tile': d['tile'], 'whole_tile_exact': True})
        assert np.array_equal(old_fx % 16, render(b, n, 5, effect5))
        preserved_effects.append({'ref': n, 'base_records_and_tiles_exact': True, 'layer5_whole_tile_copies': copies})
    share = []
    for ns in ((106, 107, 108), (110, 111), (109,), (112,), (113,), (114,), (233,), (234, 235), (236,)):
        offsets = {b.banks[0]['frames'][n]['offset'] for n in ns}
        assert len(offsets) == 1
        actual_owners = [f['index'] for f in b.banks[0]['frames'] if f['offset'] in offsets]
        assert actual_owners == list(ns)
        share.append({'owners': actual_owners, 'count': 32})
    bodyparts = parts(b, 0, 234)
    ps235 = parts(b, 0, 235)
    assert [sig(z) for z in ps235[-len(bodyparts):]] == [sig(z) for z in bodyparts]
    assert np.array_equal(render(b, 235, 0, ps235[:-len(bodyparts)]), npy(ROOT / src['aura235_236'][0]['historical_effect_path']))
    for n in sorted(REFS):
        for mask in range(16):
            for arm in (1, 2):
                expected = color(b, targets[n][0])
                for bit, pb in ((8, 8), (1, 5), (4, 7), (2, 6)):
                    if mask & bit:
                        v = color(b, targets[n][pb], 32 if pb == 7 and arm == 2 else 16)
                        covered = v[:, :, 3] > 0
                        expected[covered] = v[covered]
                assert np.array_equal(expected, np.asarray(b.composite(n, mask, arm)[0]))
                counts['independent_partial_RGBA'] += 1
    # The first candidate was rejected by the producer's native GPU check.
    # Its entire displayed target stays fixed; only the new layer5 boundary use moves.
    rejected_path = H / 'prepared_ultimate_hurt01/PL02_U.ARC'
    rejected_data = blob(rejected_path)
    assert sha(rejected_data) == '8c9a83077a6973b5ea2fff46ee3273ae281bf0d0d2190db4f67dbc792ee3e3c3'
    rejected = Archive(rejected_data)
    changed_raw = []
    for gb, bank in enumerate(b.banks):
        for f in bank['frames']:
            n = f['index']
            if raw(rejected, gb, n) != raw(b, gb, n):
                assert gb == 0 and n in (110, 111)
                for t in range(32):
                    if t == 31:
                        assert not tile(rejected, n, t).any()
                        assert np.array_equal(tile(b, n, 31), tile(rejected, n, 16))
                    else:
                        assert np.array_equal(tile(b, n, t), tile(rejected, n, t))
                changed_raw.append([gb, n])
    assert changed_raw == [[0, 110], [0, 111]]
    changed_parts = []
    for pb in range(len(bank_offsets(b.c))):
        for n in range(composition_frame(b.c, pb, 0)['bank_frame_count']):
            prev, now = parts(rejected, pb, n), parts(b, pb, n)
            assert len(prev) == len(now)
            for i, (q, r) in enumerate(zip(prev, now)):
                if sig(q) != sig(r):
                    assert (pb, n) == (5, 111) and q['tile'] == 16 and r['tile'] == 31
                    assert (q['flags'], q['x'], q['y']) == (r['flags'], r['x'], r['y'])
                    changed_parts.append({'bank': pb, 'ref': n, 'index': i, 'old': sig(q), 'new': sig(r)})
    assert len(changed_parts) == 1
    native_path = H / 'ultimate_hurt_probe02_components_native_checks.json'
    blob(native_path)
    native = read(native_path)
    assert native['passed'] and native['resources']['PL02_U.ARC']['candidate_sha256'] == sha(new)
    decoder = native['resources']['PL02_U.ARC']['banks'][0]['native_decoder_checks']
    decoder_by_ref = {q['frame']: q for q in decoder}
    for n in REFS:
        assert decoder_by_ref[n]['decoded_sha256'] == sha(raw(b, 0, n))
    sheets = []
    for i, ns in enumerate(((106, 110), (233, 234), (107, 108, 109), (111, 112, 113), (114, 235, 236))):
        cw, ch = 292, 300
        board = Image.new('RGB', (cw*4, ch*len(ns)), '#263345')
        draw = ImageDraw.Draw(board)
        for row, n in enumerate(ns):
            for col, (label, ar, mask) in enumerate((('old before', a, 15), ('new before', b, 15), ('old after', a, 0), ('new after', b, 0))):
                x, y = col*cw, row*ch
                draw.text((x+4, y+4), f'{n} {label}', fill='white')
                im = ar.composite(n, mask)[0].crop((127, 126, 197, 194)).resize((280, 272), Image.Resampling.NEAREST)
                board.paste(im, (x+6, y+23), im)
        dest = o / f'readback_{i:02}.png'
        board.save(dest)
        sheets.append({'path': rel(dest), 'sha256': sha(dest.read_bytes())})
    assert counts['raw_checked'] == 512 and counts['non_target_raw_exact'] == 499
    assert counts['target_layers_exact'] == 65 and counts['non_target_layers_exact'] == 1075
    assert counts['independent_partial_RGBA'] == 416
    for name, h in tracked.items():
        assert sha((ROOT / name).read_bytes()) == h, ('input changed during audit', name)
    report = {'passed': True, 'scope': 'Ultimate 피격13의 등록/공통/역사효과→65층→실제ARC 독립 reader. 제작/패킹 모듈 미호출.',
              'candidate': rel(candidate), 'candidate_sha256': sha(new), 'parent_sha256': sha(old),
              'target_manifest_sha256': sha((T / 'manifest.json').read_bytes()), 'lock_sha256': args.lock_sha256,
              'locked_inputs': len(lock['files']), 'counts': dict(counts), 'source_proof': sourceproof,
              'effect_tile_and_record_proof': preserved_effects, 'preserved_GPU_edge_exceptions': edges, 'new_GPU_edge_invasions': 0,
              'archive_length_directory_other_entries_palette_audio_exact': True, 'all_bank_boundaries_exact': True,
              'shared_streams': share, 'shared234235_effect_then_body_order_exact': True,
              'rejected_v1_GPU_fix': {'rejected_sha256': sha(rejected_data), 'changed_raw_refs': changed_raw,
                                      'whole_tile16_to31_copy': True, 'changed_parts': changed_parts,
                                      'all_display_targets_unchanged': True},
              'producer_native_evidence': {'path': rel(native_path), 'sha256': sha(native_path.read_bytes()),
                                           'passed': True, 'independent13_raw_hashes_match_native_decode': True,
                                           'not_executed_here': True},
              'non_target_partial_RGBA_follows_exact1075_layers_and_palette': True, 'inputs': tracked,
              'readback_sheets': sheets, 'readback_actually_viewed': False,
              'generation_requantized_here': False, 'native_MIPS_executed_here': False, 'runtime_verified': False,
              'limits': ['등록8그림과234새팔 donor 이후의 공통화/파생을 독립 재구성했다. 생성원화 고정배율 양자화는 별도다.',
                         '107/108은 원US 전기99/76px 전체표시,112..114는 새재킷110 공통실루엣이라는 새제작 정책이다.',
                         '235/236은 역사오라256/464를 먼저그리고 새234로 가린다. 구형 의상조각/재색상은 복사하지 않는다.',
                         '게임/실제효과 시간순서/사용자수용은 별도다.']}
    (o / 'report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n', 'utf8')
    print(json.dumps({'passed': True, 'counts': dict(counts), 'sha256': sha((o / 'report.json').read_bytes())}))

if __name__ == '__main__':
    main()
