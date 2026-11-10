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
N = D.parent / 'nana_audit/ultimate_wall_repaint'
PBS = (0, 5, 6, 7, 8)
VALID = [n for n in range(237) if n not in {105, *range(175, 183)}]
OUT = D / 'nana_wall_independent'
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

def targets_nana(a):
    td=N/'joint_native_targets_v1';m=js(td/'manifest.json');assert m['source_arc_sha256']==sha(a.data)
    assert m['selected_refs']==list(range(55,67)) and [q['ref']for q in m['frames']]==list(range(55,67))
    tt={};costumes={};corrections=[]
    for row in m['frames']:
        n=row['ref'];vv={}
        for form in('before','after'):
            p=N/row[form+'_source'];assert sha(read(p))==row[form+'_source_sha256'];vv[form]=arr(p).copy()
        outside=(vv['after']>0)&(vv['before']==0)
        expected={56:{(-15,-6),(-8,-6),(-7,-6)},58:{(-15,-8)},60:{(-15,-8),(-1,-3)},62:set(),64:{(-3,-3),(-2,-3),(-8,-2),(-7,-2)},66:{(0,-2)}}.get(n,set())
        assert {(int(x)-160,int(y)-160)for y,x in zip(*np.where(outside))}==expected
        assert {tuple(x['world'])for x in row['local_source_corrections']}==expected
        for q in row['local_source_corrections']:
            x,y=q['world'];assert vv['after'][y+160,x+160]==q['before_index'] and q['after_index']==0
        vv['after'][outside]=0
        for form,start,mask in(('before',16,15),('after',0,0)):
            ar=arr(td/f'{form}_{n:03}.png');assert sha(ar.tobytes())==row[form+'_sha256'] and np.array_equal(ar,vv[form]);costumes[n,mask]=color(ar,a.words,start)
        before,after=vv['before'],vv['after']
        for pb in PBS:
            ar=arr(td/f'layer{pb}_{n:03}.png');assert sha(ar.tobytes())==row['layers'][str(pb)]
            want=after if pb==0 else np.where((before!=after)|(before==15),before,0)if pb==5 else np.zeros_like(after)
            assert np.array_equal(ar,want);tt[n,pb]=ar
        corrections.extend([{'ref':n,**q}for q in row['local_source_corrections']])
    assert len(corrections)==11
    return tt,costumes,{'manifest':rel(td/'manifest.json'),'manifest_sha256':sha(read(td/'manifest.json')),'source_corrections':corrections}

def nana_guns(a):
    td=N/'weapon_constraints_v1';m=js(td/'manifest.json');assert m['source_arc_sha256']==sha(a.data);Y,X=np.indices((384,384));guns={}
    for row in m['frames']:
        n=row['ref'];bar=arr(td/f'case_{n:03}.png');assert sha(bar.tobytes())==row['barrel_index_sha256'];old=full_indices(a,n)
        x0,y0,x1,y1=row['gun_window_world'];gate=(X>=160+x0)&(X<160+x1)&(Y>=160+y0)&(Y<160+y1);assert x1-x0==8
        assert np.array_equal(bar,np.where(gate,old,0)),('original gun',n)
        ys,xs=np.where(bar);gx=int(xs.min());my=float(np.median(ys[xs==gx]));gate=(X>=gx)&(X<gx+8)&(Y>=my-3)&(Y<=my+5)
        guns[n]=(gate,color(bar,a.words,16))
    assert set(guns)==set(range(56,67,2));return guns

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
    for odd in (range(55, 67, 2) if name == 'nana_ultimate_wall12' else [98]):
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
    guns = nana_guns(a) if name == 'nana_ultimate_wall12' else {}
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
    if name != 'nana_ultimate_wall12':
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
    result['visual_observations'] = ['실제 최종 readback1/2의 벽6몸체·사격6짝·두 의상을 직접 열람했다. 대기와 비교해 머릿결, 재킷 소매와 맨팔의 구분이 명확하다.', '56/58의 접힌 옛 손 잔여가 제거되어 어깨부터 손목까지 한 팔로 읽히고60의 굽힌 무릎이 사격 팔에 섞이지 않는다.62/64/66도 목·상완이 이어진다.', '원총구8열·그립과 새 손의 연결을 정지 시트에서 확인했다. 벽손과 발이 원위치에 놓이는지의 실제 플레이·필터·반전 가독성은 별도이며 전수 실기 수용으로 세지 않는다.']
    OUT.mkdir(exist_ok=True)
    path = OUT / f'{name}.json'
    path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', 'utf8')
    print(json.dumps({'name': name, 'passed': True, 'counts': dict(count)}), flush=True)
    return {'path': rel(path), 'sha256': sha(path.read_bytes()), 'candidate_sha256': newhash, 'passed': True}

if __name__=='__main__':
    out=audit('nana_ultimate_wall12',N.parent/'ultimate_air_repaint/packed_air_candidate_v1/PL02_U.ARC',N/'packed_wall_candidate_v1/PL02_U.ARC',
      '122c92c29fd0599772e18ac5ed3f918c8f0d40703fe08c396e4ccbdbb92f2c18','e151044c37b5a59016f10d8c4d9637ffd4e192563f03c6a76df528383cfb4031',
      set(range(55,67)),targets_nana,[N/'packed_wall_candidate_v1'/f'readback_{i}.png'for i in(1,2)])
    for p,h in tracked.items():assert sha(p.read_bytes())==h
    p=OUT/'nana_ultimate_wall12.json';j=js(p);j['all_inputs_readonly_sha256']={rel(k):v for k,v in tracked.items()if k!=p};p.write_text(json.dumps(j,ensure_ascii=False,indent=2)+'\n','utf8');print(sha(p.read_bytes()))
