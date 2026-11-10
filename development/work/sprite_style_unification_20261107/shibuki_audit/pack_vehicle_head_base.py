"""새 기본/포스 작은머리19를 명시한 최신 PL00 부모의 고정은행에 수납한다."""
from pathlib import Path
import argparse
import io
import json
import struct
import sys
import numpy as np
from PIL import Image

H = Path(__file__).resolve().parent
ROOT = H.parents[2]
sys.path.insert(0, str(ROOT))
from native_pose_pack import need, sha, write
from prepare_vehicle_head_base_targets import GEOMETRY, GEOMETRY_SHA, PBS, REFS, TD
from scripts.export_x_consistency import Archive, page
from scripts.prepare_shibuki_ultimate_production import repack_parts, records
from scripts.prepare_riko_ui import replace_entry
from src.psx_player import bank_offsets, composition_frame, indexed_atlas
from pack_shibuki_hurt import raw, repack_fixed_global
from pack_dash_complete import protected_entries
from prepare_lowhp_final import compose
from repack_part_records_lossless import repack as repack_lossless

MANIFEST = '06cfdfbd56001ada3ea53b3074aa7a7c9c6194af05be456ee38009fc73a9dbd5'


def validate(data, parent_sha256, read=lambda p: p.read_bytes()):
    need(sha(data) == parent_sha256, '명시한 부모 해시 불일치')
    blob = read(TD / 'manifest.json')
    need(sha(blob) == MANIFEST, '목표 목록 변경')
    meta = json.loads(blob)
    for name, digest in meta['source_files'].items():
        need(sha(read(ROOT / name)) == digest, '출처 변경: ' + name)
    reference = Archive(read(GEOMETRY))
    need(sha(reference.data) == GEOMETRY_SHA, '원점 기준 부모 변경')
    a = Archive(data)
    need(a.p == reference.p, '새 부모 팔레트가 기준과 다름')
    for ns, layers in meta['expected_unchanged_parent_layers_for_rebase'].items():
        for bs, digest in layers.items():
            need(sha(a.layer(int(ns), int(bs))[0].tobytes()) == digest, '새 부모의 작은머리100층 변경')
    for n in REFS:
        for b in PBS:
            z = np.array(Image.open(io.BytesIO(read(TD / f'{n:03}_bank{b}_indices.png'))))
            need(z.shape == (384, 384) and z.dtype == np.uint8 and z.max() < 16, '목표 색인 형식')
            need(sha(z.tobytes()) == meta['targets'][str(n)][str(b)], '목표층 변경')
    return meta


def build(data, parent_sha256):
    meta = validate(data, parent_sha256)
    a = Archive(data)
    targets = {n: {b: np.array(Image.open(TD / f'{n:03}_bank{b}_indices.png')) for b in PBS} for n in REFS}
    changes = {0: {}, 5: {}}
    tilemap = {0: 1, 5: 3}
    atlas = np.zeros((16, 64), np.uint8)
    for b, tile in tilemap.items():
        atlas[:15, tile * 16:tile * 16 + 13] = targets[184][b][123:138, 150:163]
    packed = bytes((atlas[:, ::2] | atlas[:, 1::2] << 4).ravel())
    need(len(packed) == 4 * 128, '4타일 길이')
    full = np.frombuffer(indexed_atlas(packed, 4)[0], np.uint8).reshape(16, 256)
    need(not full[:, :16].any() and not full[:, 32:48].any(), '빈0/2 전체타일 보호')
    shifts = {v['ref']: v['translation_from184'] for v in meta['translations']}
    blank_records = []
    for n in REFS:
        dx, dy = shifts[n]
        for b, tile in tilemap.items():
            changes[b][n] = struct.pack('<BBbb', 0, tile, -10 + dx, -37 + dy)
        for b in (6, 7, 8):
            record = composition_frame(a.c, b, n)
            need(not a.layer(n, b)[0].any(), '기존 빈층')
            need(all(p['tile'] in (0, 2) for p in record['parts']), '기존 빈층 소비타일 변경')
            blank_records.append((b, n, record))
    nc = a.c
    slack = {}
    part_methods = {}
    for b, rr in changes.items():
        try:
            nc, slack[b] = repack_parts(nc, b, rr)
            part_methods[b] = {'method': 'length_order_exact_record_sharing'}
        except ValueError as first_error:
            nc, slack[b], method = repack_lossless(nc, b, rr)
            part_methods[b] = {**method, 'first_method_rejection': str(first_error)}
    ng, graphics = repack_fixed_global(a, {n: packed for n in REFS}, {n: 4 for n in REFS})
    out = replace_entry(replace_entry(data, 2, ng), 3, nc)
    z = Archive(out)
    need(bank_offsets(nc) == bank_offsets(a.c), '조립은행 경계 변경')
    need(ng[:56] == a.g[:56] and ng[a.banks[0]['end']:] == a.g[a.banks[0]['end']:], '다른 그래픽은행 변경')
    raw_count = nonraw = layers = nonlayers = nonrecords = partial = gpu = 0
    for gb, bank in enumerate(a.banks):
        newbank = z.banks[gb]
        need((bank['base'], bank['end'], len(bank['frames'])) == (newbank['base'], newbank['end'], len(newbank['frames'])), '그래픽 경계 변경')
        for frame in bank['frames']:
            n = frame['index']
            selected = gb == 0 and n in REFS
            need(raw(z, gb, n) == (packed if selected else raw(a, gb, n)), '원시 자료 불일치')
            raw_count += 1
            nonraw += not selected
    for n in range(237):
        if n in (105, *range(175, 183)):
            continue
        for b in PBS:
            need(np.array_equal(z.layer(n, b)[0], targets[n][b] if n in targets else a.layer(n, b)[0]), f'층 불일치 {n}/{b}')
            layers += 1
            nonlayers += n not in targets
        if n not in targets:
            continue
        for arm in (1, 2):
            for mask in range(16):
                need(z.composite(n, mask, arm)[0].tobytes() == compose(a, targets[n], mask, arm).tobytes(), '부분 표시 불일치')
                partial += 1
        for b in PBS:
            for part in composition_frame(z.c, b, n)['parts']:
                tile = part['tile']
                texels = full[:, tile % 16 * 16:tile % 16 * 16 + 16]
                need(tile % 16 != 0 or not texels[:, 0].any(), 'GPU U경계')
                need(not part['flip_y'] or not texels[0].any(), 'GPU V경계')
                gpu += 1
    for b in range(len(bank_offsets(a.c))):
        for n in range(composition_frame(a.c, b, 0)['bank_frame_count']):
            if b in changes and n in changes[b]:
                need(records(nc, b, n) == changes[b][n], '목표 기록')
            else:
                need(records(nc, b, n) == records(a.c, b, n), '비대상 기록 변경')
                nonrecords += 1
    for b, n, record in blank_records:
        need(composition_frame(z.c, b, n) == record, '빈678 기록/offset 변경')
    need(raw(z, 0, 198) == raw(a, 0, 198), '198 원시 자료')
    need(all(not z.composite(198, mask, arm)[0].getbbox() for arm in (1, 2) for mask in range(16)), '198 빈 표시')
    return out, {
        'passed': True, 'parent_sha256': parent_sha256, 'candidate_sha256': sha(out), 'target_manifest_sha256': MANIFEST,
        'geometry_parent_sha256': GEOMETRY_SHA, 'rebase_parent_head100layers_and_palette_exact': True,
        'refs': list(REFS), 'counts': {'raw': raw_count, 'non_target_raw': nonraw, 'target_layers': 95, 'changed_owner_layers': 38, 'selected_empty_layers_exact': 57, 'all_layers': layers, 'non_target_layers': nonlayers, 'non_target_records': nonrecords, 'partial_RGBA': partial, 'GPU_parts': gpu},
        'shared_new_stream': {'tile_count': 4, 'raw_sha256': sha(packed), 'owners': list(REFS), 'empty_full_tiles': [0, 2], 'base_tile': 1, 'overlay_tile': 3},
        'translations': meta['translations'], 'part_slack': slack, 'part_methods': part_methods, 'graphics': graphics,
        'all_bank_boundaries_preserved': True, 'protected_entries': protected_entries(data, out),
        'selected_empty678_records_and_offsets_preserved': True, 'ref198_raw_layers_records_preserved': True,
        'old_RGB_copied': False, 'pixel_reduction': False, 'runtime_verified': False,
        'native_cpu_pending': True, 'independent_pending': True, 'root_final_art_pending': True,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--parent', required=True)
    ap.add_argument('--parent-sha256', required=True)
    ap.add_argument('--output', required=True)
    ap.add_argument('--analysis-only', action='store_true')
    args = ap.parse_args()
    parent = (ROOT / args.parent).resolve()
    d = (H / args.output).resolve()
    need(parent.is_relative_to(ROOT) and d.is_relative_to(H) and not d.exists(), '새 소유 출력/부모 경로')
    out, proof = build(parent.read_bytes(), args.parent_sha256)
    proof.update(parent=parent.relative_to(ROOT).as_posix(), analysis_only=args.analysis_only, ARC_written=not args.analysis_only)
    d.mkdir()
    if not args.analysis_only:
        (d / 'PL00_U.ARC').write_bytes(out)
        a = Archive(out)
        for form, mask in (('base', 0), ('fourth', 15)):
            for i in range(2):
                page([(f'{n} {form}', a.composite(n, mask)[0]) for n in REFS[i * 10:i * 10 + 10]], a.composite(0, mask)[0], d / f'{form}_readback_{i:02}.png', cols=5, scale=4)
        for n in (184, 196):
            page([(f'{n} mask{mask:X}', a.composite(n, mask)[0]) for mask in range(16)], a.composite(0, 0)[0], d / f'ownership_{n:03}.png', cols=4, scale=3)
    write(d / 'report.json', proof)
    print(json.dumps({'candidate': sha(out), 'counts': proof['counts'], 'part_slack': proof['part_slack'], 'graphics_slack': proof['graphics']['remaining_slack'], 'ARC_written': not args.analysis_only}))


if __name__ == '__main__':
    main()
