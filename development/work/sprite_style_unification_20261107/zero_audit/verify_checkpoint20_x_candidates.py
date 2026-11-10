"""독립 읽기 감사: 제작/등록/패킹 모듈 없이 세 작업 ARC를 재독출한다."""
from pathlib import Path
import sys, json, hashlib, collections, gc
import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from scripts.export_x_consistency import Archive
from scripts.prepare_riko_ui import replace_entry
from src.psx_player import decode_stream, composition_frame, bank_offsets, indexed_atlas

D = Path(__file__).parent
H = D.parent / 'shibuki_audit'
N = D.parent / 'nana_audit/ultimate_air_repaint'
PBS = (0, 5, 6, 7, 8)
VALID = [n for n in range(237) if n not in {105, *range(175, 183)}]
OUT = D / 'checkpoint20_x_independent'
sha = lambda data: hashlib.sha256(data).hexdigest()
rel = lambda p: p.relative_to(ROOT).as_posix()
tracked = {}

def read(p):
    data = p.read_bytes()
    tracked[p] = sha(data)
    return data

def js(p): return json.loads(read(p))

def arr(p):
    read(p)
    v = np.array(Image.open(p))
    assert v.dtype == np.uint8 and v.shape == (384, 384) and v.max() < 16, str(p)
    return v

def color(v, words, start=0):
    table = np.array([[(int(w) >> s & 31) * 255 // 31 for s in (0, 5, 10)] +
                      [0 if i % 16 == 0 else 255]
                      for i, w in enumerate(words[start:])], np.uint8)
    return table[v]

def composite(layers, words, mask, arm):
    result = color(layers[0], words)
    for bit, pb in ((8, 8), (1, 5), (4, 7), (2, 6)):
        if mask & bit:
            v = color(layers[pb], words, 32 if pb == 7 and arm == 2 else 16)
            opaque = v[:, :, 3] > 0
            result[opaque] = v[opaque]
    return result

def check_lock(directory):
    lock = js(directory / 'LOCK.json')
    for name, digest in lock['files'].items(): assert sha(read(directory / name)) == digest
    for name, digest in lock['source_files'].items(): assert sha(read(H / name)) == digest
    return lock

def full_indices(a, n):
    v = a.layer(n, 0)[0].copy()
    for pb in (8, 5, 7, 6):
        layer = a.layer(n, pb)[0]
        v[layer > 0] = layer[layer > 0]
    return v

def targets_base(a):
    directory = H / 'double_cyclone_layers_probe02'
    lock = check_lock(directory)
    assert lock['parent_sha256'] == sha(a.data)
    target = {(n, pb): np.roll(arr(directory / f'098_bank{pb}_indices.png'), n - 98, 1)
              for n in (98, 99) for pb in PBS}
    return target, {}, {'lock': rel(directory / 'LOCK.json')}

def targets_ultimate(a):
    directory = H / 'double_cyclone_ultimate_shared01'
    lock = check_lock(directory)
    assert lock['parent_sha256'] == sha(a.data)
    before = arr(directory / 'before_098_indices.png')
    after = arr(directory / 'after_098_indices.png')
    assert not ((after > 0) & (before == 0)).any()
    same = np.all(color(before, a.words, 16) == color(after, a.words), axis=2)
    overlay = np.where(same, 0, before).astype(np.uint8)
    target, costumes = {}, {}
    for n in (98, 99):
        for pb in PBS:
            v = after if pb == 0 else overlay if pb == 5 else np.zeros_like(after)
            target[n, pb] = np.roll(v, n - 98, 1)
        costumes[n, 0] = color(np.roll(after, n - 98, 1), a.words)
        costumes[n, 15] = color(np.roll(before, n - 98, 1), a.words, 16)
    return target, costumes, {'lock': rel(directory / 'LOCK.json')}

def targets_nana(a):
    directory = N / 'joint_native_targets_v2'
    manifest = js(directory / 'manifest.json')
    assert manifest['source_arc_sha256'] == sha(a.data)
    assert manifest['selected_refs'] == list(range(33, 55))
    assert [r['ref'] for r in manifest['frames']] == list(range(33, 55))
    target, costumes, corrections = {}, {}, []
    for row in manifest['frames']:
        n = row['ref']
        raw = {}
        for form in ('before', 'after'):
            path = N / row[form + '_source']
            assert sha(read(path)) == row[form + '_source_sha256']
            raw[form] = arr(path).copy()
        local = row['local_source_corrections']
        if n == 38:
            assert len(local) == 1 and local[0]['xy'] == [-5, 3]
            assert raw['after'][163, 155] == 3
            raw['after'][163, 155] = 0
        elif n == 44:
            assert len(local) == 1
            fixed = arr(N / 'costume43_boundary_v3/after_043.png')
            previous = arr(N / 'costume_pair_probe_v2/after_043.png')
            mask = fixed != previous
            assert mask.sum() == 6
            assert np.array_equal(raw['after'][mask], previous[mask])
            assert sorted(local[0]['coordinates']) == sorted([[int(x)-160, int(y)-160] for y,x in zip(*np.where(mask))])
            raw['after'][mask] = fixed[mask]
        else:
            assert local == []
        for form, start, mask in (('before', 16, 15), ('after', 0, 0)):
            v = arr(directory / f'{form}_{n:03}.png')
            assert sha(v.tobytes()) == row[form + '_sha256']
            assert np.array_equal(v, raw[form]), (n, form, 'source reconstruction')
            costumes[n, mask] = color(v, a.words, start)
        assert not ((raw['after'] > 0) & (raw['before'] == 0)).any()
        for pb in PBS:
            v = arr(directory / f'layer{pb}_{n:03}.png')
            assert sha(v.tobytes()) == row['layers'][str(pb)]
            want = raw['after'] if pb == 0 else np.where(raw['before'] != raw['after'], raw['before'], 0) if pb == 5 else np.zeros_like(v)
            assert np.array_equal(v, want)
            target[n, pb] = v
        corrections.extend([{'ref': n, **q} for q in local])
    return target, costumes, {'manifest': rel(directory / 'manifest.json'), 'source_corrections': corrections}

def nana_guns(a):
    directory = N / 'weapon_constraints_v1'
    manifest = js(directory / 'manifest.json')
    assert manifest['parent_sha256'] == sha(a.data)
    Y, X = np.indices((384, 384))
    result = {}
    for n in range(34, 55, 2):
        original = full_indices(a, n)
        y, x = np.nonzero(original)
        gx = int(x.min()); my = float(np.median(y[x == gx]))
        source_window = (X >= gx) & (X < gx + 8) & (Y >= np.floor(my) - 2) & (Y <= np.ceil(my) + 3)
        bar = arr(directory / f'case_{n:03}.png')
        assert np.array_equal(bar, np.where(source_window, original, 0))
        row = next(q for q in manifest['frames'] if q['ref'] == n)
        assert sha(bar.tobytes()) == row['original_indexed_sha256']
        y, x = np.nonzero(bar); gx = int(x.min()); my = float(np.median(y[x == gx]))
        gate = (X >= gx) & (X < gx + 8) & (Y >= my - 3) & (Y <= my + 5)
        result[n] = (gate, color(bar, a.words, 16))
    return result

def audit(name, oldpath, newpath, oldhash, newhash, refs, loader, sheet_paths, pngdir=None):
    old, new = read(oldpath), read(newpath)
    assert sha(old) == oldhash and sha(new) == newhash
    a, b = Archive(old), Archive(new)
    target, costumes, meta = loader(a)
    assert set(target) == {(n, pb) for n in refs for pb in PBS}
    assert len(old) == len(new) and replace_entry(replace_entry(new, 2, a.g), 3, a.c) == old
    assert a.p == b.p
    assert bank_offsets(a.g, allow_aliases=True) == bank_offsets(b.g, allow_aliases=True)
    assert bank_offsets(a.c) == bank_offsets(b.c)
    count = collections.Counter()
    raw_targets = {}
    for gb, (aa, bb) in enumerate(zip(a.banks, b.banks)):
        assert (aa['base'], aa['end'], len(aa['frames'])) == (bb['base'], bb['end'], len(bb['frames']))
        for o, n in zip(aa['frames'], bb['frames']):
            assert o['index'] == n['index']
            x = decode_stream(a.g, o['offset'], o['limit'], o['tile_count'] * 128)
            y = decode_stream(b.g, n['offset'], n['limit'], n['tile_count'] * 128)
            assert x.serialize() == a.g[x.start:x.end] and y.serialize() == b.g[y.start:y.end]
            count['raw_checked'] += 1
            if gb == 0 and n['index'] in refs:
                assert n['tile_count'] == 32
                raw_targets[n['index']] = np.frombuffer(indexed_atlas(y.data, 32)[0], np.uint8).reshape(32, 256)
            else:
                assert x.data == y.data and o['tile_count'] == n['tile_count']
                count['non_target_raw_exact'] += 1
    for odd in (range(33, 55, 2) if name == 'nana_ultimate_air22' else [98]):
        assert a.banks[0]['frames'][odd]['offset'] == a.banks[0]['frames'][odd+1]['offset']
        assert b.banks[0]['frames'][odd]['offset'] == b.banks[0]['frames'][odd+1]['offset']
        count['original_pairs_shared_stream'] += 1
    for pb in range(len(bank_offsets(a.c))):
        assert composition_frame(a.c, pb, 0)['bank_frame_count'] == composition_frame(b.c, pb, 0)['bank_frame_count']
        for n in range(composition_frame(a.c, pb, 0)['bank_frame_count']):
            x, y = composition_frame(a.c, pb, n), composition_frame(b.c, pb, n)
            sem = lambda q: [(p['flags'], p['tile'], p['x'], p['y']) for p in q['parts']]
            if pb in PBS and n in refs:
                atlas = raw_targets[n]
                for p in y['parts']:
                    t = p['tile']; assert 0 <= t < 32
                    tile = atlas[t//16*16:t//16*16+16, t%16*16:t%16*16+16]
                    assert t % 16 != 0 or not tile[:, 0].any()
                    assert not p['flip_y'] or not tile[0].any()
                    count['target_gpu_parts_safe'] += 1
            else:
                assert sem(x) == sem(y), (name, pb, n, 'non-target assembly')
                count['non_target_composition_records_exact'] += 1
    guns = nana_guns(a) if name == 'nana_ultimate_air22' else {}
    changed = []
    for n in VALID:
        layers = {}
        for pb in PBS:
            v = b.layer(n, pb)[0]
            count['layers_checked'] += 1
            if n in refs:
                assert np.array_equal(v, target[n, pb]), (name, n, pb, 'authored layer')
                count['authored_layer_exact'] += 1
                layers[pb] = v
            else:
                assert np.array_equal(v, a.layer(n, pb)[0]), (name, n, pb, 'non-target layer')
                count['non_target_layer_exact'] += 1
        if n not in refs:
            continue
        for mask in range(16):
            for arm in (1, 2):
                actual = np.array(b.composite(n, mask, arm)[0])
                assert np.array_equal(actual, composite(layers, b.words, mask, arm))
                count['selected_RGBA_combinations'] += 1
                if n in guns:
                    gate, expected = guns[n]
                    assert np.array_equal(actual[gate], expected[gate]), (n, mask, arm, 'muzzle')
                    count['original_muzzle_RGBA_conditions'] += 1
                if (n, mask) in costumes:
                    assert np.array_equal(actual, costumes[n, mask]), (n, mask, arm, 'full costume')
                    count['authored_full_RGBA_conditions'] += 1
        for mask in (0, 15):
            oldim = np.array(a.composite(n, mask)[0]); newim = np.array(b.composite(n, mask)[0])
            change = int(np.any(oldim != newim, axis=2).sum())
            assert change > 0
            changed.append({'ref': n, 'mask': mask, 'changed_RGBA_pixels': change})
            if pngdir:
                prefix = ('base' if mask == 0 else 'fourth') if name == 'shibuki_base_cyclone' else ('after' if mask == 0 else 'before')
                png = pngdir / f'{prefix}_{n:03}.png'
                read(png)
                assert np.array_equal(np.array(Image.open(png)), newim)
                count['individual_readback_PNGs_exact'] += 1
    assert count['raw_checked'] == (508 if name == 'shibuki_base_cyclone' else 512)
    assert count['non_target_raw_exact'] == count['raw_checked'] - len(refs)
    assert count['layers_checked'] == 1140 and count['authored_layer_exact'] == len(refs) * 5
    if name != 'nana_ultimate_air22':
        for pb in PBS:
            assert np.array_equal(b.layer(99, pb)[0], np.roll(b.layer(98, pb)[0], 1, 1))
        count['99_is_98_x_plus_one_layers'] = 5
    visual = [{'path': rel(p), 'sha256': sha(read(p))} for p in sheet_paths]
    result = {'passed': True, 'scope': '제작 함수를 호출하지 않고 실제 출력 ARC와 원화 등록 PNG를 별도로 읽었다. 픽셀 검증과 정지 시트 미술 검토이며 게임 실기 검증은 아니다.',
              'source': rel(oldpath), 'source_sha256': oldhash, 'candidate': rel(newpath), 'candidate_sha256': newhash,
              'metadata': meta, 'counts': dict(count), 'changed_full_displays': changed,
              'all_other_entries_palette_audio_static_exact': True, 'fixed_bank_boundaries': True,
              'non_target_partial_masks_preserved_by_identical_layers_and_palette': True,
              'native_MIPS_executed_here': False, 'gameplay_runtime_verified': False,
              'producer_functions_called': False, 'actually_viewed_sheets': visual}
    if name.startswith('shibuki'):
        result['visual_observations'] = ['네 의상별 원래/새98·99 시트에서 머릿결·커프·옷 주름의 세분화와 팔/허리 연결을 직접 확인했다.', '99는 새98의 원래 1픽셀 수평 이동을 보존하며, 무기 효과의 실행 시점과 동적 팔레트 색은 이 미술 감사의 검증 범위 밖이다.']
        if name == 'shibuki_base_cyclone': result['visual_observations'].append('부분아머16조합 시트도 직접 열람했다. 큰 신체 단절이나 기본 꽃의 포스 머리장식 위 잔류는 보이지 않는다.')
    else:
        result['visual_observations'] = ['네 재독출 시트의 공중11자세·사격11짝·두 의상을 직접 열람했다. 새 머릿결/의상 명암과 손목/팔꿈치 연결이 유지되어 보인다.', '43·44 획득후 어깨에는 앞서 지적했던 분홍 소매 테두리가 남지 않았으며,37의 붉은 부분은 후두부 머리로 이어진다.', '51·52 착지 지지발과 뒤 무릎이 분리되어 읽힌다. 연속 동작의 실제 속도와 모든 무기 팔레트 가독성은 아직 이 정지 검토로 확정하지 않는다.']
    OUT.mkdir(exist_ok=True)
    path = OUT / f'{name}.json'
    path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', 'utf8')
    print(json.dumps({'name': name, 'passed': True, 'counts': dict(count)}), flush=True)
    return {'path': rel(path), 'sha256': sha(path.read_bytes()), 'candidate_sha256': newhash, 'passed': True}

def main():
    cases = [
        ('shibuki_base_cyclone', H/'air_pack_probe01/candidate_PL00_U.ARC', H/'prepared_double_cyclone_base01/PL00_U.ARC',
         'c580b371564252fd73cb97aa31d3282dcebabf5855cbec6d5b00acc7f7b7c6be', '61495a2aaf002efc32492a4e12c3724a77c82b3f42464538ae1e2cc855da74c0', {98,99}, targets_base,
         [H/'double_cyclone_base_pack02'/p for p in ('base_readback.png','fourth_readback.png','partial_readback.png')], H/'double_cyclone_base_pack02'),
        ('shibuki_ultimate_cyclone', H/'prepared_ultimate_wall01/PL02_U.ARC', H/'prepared_double_cyclone_ultimate01/PL02_U.ARC',
         'c851fb17b2369281667970c414be63eb31fb1f02fe5641ad667bfb4b5c8507cf', 'dd6416c8840a1a0e5fd7ff4c73fe33b6ebd90e69b5f86f9be5f9671cc4d53c1d', {98,99}, targets_ultimate,
         [H/'double_cyclone_ultimate_pack01'/p for p in ('before_readback.png','after_readback.png')], H/'double_cyclone_ultimate_pack01'),
        ('nana_ultimate_air22', N.parent/'native_restore/nova_sync_v1/PL02_U.ARC', N/'packed_air_candidate_v1/PL02_U.ARC',
         'bced7f9086a9e6a72440bab25cda7e0c87ccc121a2ffbbc970f750dee257da45', '122c92c29fd0599772e18ac5ed3f918c8f0d40703fe08c396e4ccbdbb92f2c18', set(range(33,55)), targets_nana,
         [N/'packed_air_candidate_v1'/f'readback_{n}.png' for n in range(1,5)], None)]
    results = {}
    for case in cases:
        results[case[0]] = audit(*case)
        gc.collect()
    for p, digest in tracked.items(): assert sha(p.read_bytes()) == digest, str(p)
    final = {'passed': True, 'scope': '후보 ARC 3개 독립 읽기 감사. 원본/후보/원화 입력 파일의 전후 해시를 보존했다.',
             'results': results, 'tracked_readonly_files': len(tracked), 'source_hashes': {rel(p):h for p,h in tracked.items()},
             'gameplay_runtime_verified': False, 'no_game_BIN_pointer_save_writes': True}
    (OUT/'bundle.json').write_text(json.dumps(final, ensure_ascii=False, indent=2)+'\n', 'utf8')
    print(json.dumps({'passed':True,'bundle':rel(OUT/'bundle.json'),'sha256':sha((OUT/'bundle.json').read_bytes())}))

if __name__ == '__main__': main()
