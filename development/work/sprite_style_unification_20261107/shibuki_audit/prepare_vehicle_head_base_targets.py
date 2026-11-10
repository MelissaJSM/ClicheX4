"""기본/포스 새 작은머리2셀을 기존19원점에 등록한다. 최종 ARC 부모는 별도 결속."""
from pathlib import Path
import json
import sys
import numpy as np
from PIL import Image

H = Path(__file__).resolve().parent
ROOT = H.parents[2]
sys.path.insert(0, str(ROOT))
from native_pose_pack import need, sha, write
from scripts.export_x_consistency import Archive, page
from prepare_lowhp_final import compose

GEOMETRY = H / 'prepared_nova_strike_base01/PL00_U.ARC'
GEOMETRY_SHA = '36d4d0293abc77052c476e0495f4f4542ca75471c7a149f200e4bdb8f4e1bd4e'
PBS = (0, 5, 6, 7, 8)
REFS = tuple(n for n in range(184, 204) if n != 198)
TD = H / 'vehicle_head_base_targets01'


def main():
    need(not TD.exists(), '기존 목표 보호')
    need(sha(GEOMETRY.read_bytes()) == GEOMETRY_SHA, '기준 자원 변경')
    a = Archive(GEOMETRY.read_bytes())
    source = H / 'vehicle_head_base_native02'
    registration = json.loads((source / 'registration.json').read_text('utf8'))
    need(sha((source / 'registration.json').read_bytes()) == 'e437f09beb62981696e24dd27c091ca08895bbfd7c39dac58b3087ba49128a9b', '등록 변경')
    for name, digest in registration['files'].items():
        need(sha((source / name).read_bytes()) == digest, '등록 이미지 변경')
    for name, digest in registration['source_files'].items():
        need(sha((ROOT / name).read_bytes()) == digest, '등록 출처 변경')
    master = {b: np.array(Image.open(source / f'184_bank{b}_indices.png')) for b in (0, 5)}
    old = {mask: a.composite(184, mask)[0] for mask in (0, 15)}
    bb = old[0].getbbox()
    need(np.array_equal(master[0] > 0, a.layer(184, 0)[0] > 0), '144 알파 보호')
    need(int((master[0] > 0).sum()) == 144 and int((master[5] > 0).sum()) == 39, '소유 수')
    need(master[0][135, 156] == 7 and master[5][135, 156] == 0, '공통 홍채 보호')
    targets = {}
    shifts = []
    expected_parent_layers = {}
    partial_count = 0
    for n in range(184, 204):
        ll = {b: a.layer(n, b)[0].copy() for b in PBS}
        expected_parent_layers[str(n)] = {str(b): sha(z.tobytes()) for b, z in ll.items()}
        if n == 198:
            need(not any(z.any() for z in ll.values()), '198 빈층')
            continue
        nb = a.composite(n, 0)[0].getbbox()
        dx, dy = nb[0] - bb[0], nb[1] - bb[1]
        for mask in (0, 15):
            im = a.composite(n, mask)[0]
            need(im.crop(im.getbbox()).tobytes() == old[mask].crop(bb).tobytes(), '기존19 동형 정책')
        need(not any(ll[b].any() for b in (6, 7, 8)), '기존 빈678')
        for b in (0, 5):
            out = np.zeros((384, 384), np.uint8)
            ys, xs = np.nonzero(master[b])
            out[ys + dy, xs + dx] = master[b][ys, xs]
            ll[b] = out
        for arm in (1, 2):
            for mask in range(16):
                got = compose(a, ll, mask, arm)
                expected = compose(a, ll, 1 if mask & 1 else 0, arm)
                need(got.tobytes() == expected.tobytes(), '머리 bit 외 표시 영향')
                need(np.array_equal(np.array(got)[:, :, 3], np.array(a.composite(n, mask, arm)[0])[:, :, 3]), '모든 부분 알파 보호')
                partial_count += 1
        targets[n] = ll
        shifts.append({'ref': n, 'translation_from184': [dx, dy], 'bbox_world': [v - 160 for v in nb], 'eye_world': [-4 + dx, -25 + dy], 'parent_normalized_two_forms_exact': True, 'target_alpha_exact_to_parent': True})
    TD.mkdir()
    for n, ll in targets.items():
        for b, z in ll.items():
            Image.fromarray(z).save(TD / f'{n:03}_bank{b}_indices.png')
        for form, mask in (('base', 0), ('fourth', 15)):
            compose(a, ll, mask).save(TD / f'{form}_{n:03}.png')
    for form, mask in (('base', 0), ('fourth', 15)):
        for i in range(2):
            page([(f'{n} {form}', compose(a, targets[n], mask)) for n in REFS[i * 10:i * 10 + 10]], a.composite(0, mask)[0], TD / f'{form}_registered_{i:02}.png', cols=5, scale=4)
    for n in (184, 196):
        page([(f'{n} mask{mask:X}', compose(a, targets[n], mask)) for mask in range(16)], a.composite(0, 0)[0], TD / f'ownership_{n:03}.png', cols=4, scale=3)
    files = {GEOMETRY.relative_to(ROOT).as_posix(): GEOMETRY_SHA}
    for folder in ('vehicle_head_accessory_read01', 'vehicle_head_base_inputs01', 'vehicle_head_base_native02'):
        for p in sorted((H / folder).rglob('*')):
            if p.is_file():
                files[p.relative_to(ROOT).as_posix()] = sha(p.read_bytes())
    for name in ('prepare_vehicle_head_base_input.py', 'prepare_vehicle_head_base_materials.py', 'register_vehicle_head_base.py', 'register_vehicle_head_base_semantic.py', Path(__file__).name):
        p = H / name
        files[p.relative_to(ROOT).as_posix()] = sha(p.read_bytes())
    write(TD / 'manifest.json', {
        'source_geometry_parent': GEOMETRY.relative_to(ROOT).as_posix(), 'source_geometry_parent_sha256': GEOMETRY_SHA,
        'final_packing_parent_pending_root_hover': True, 'refs': list(REFS), 'parts_banks': list(PBS),
        'source_files': files, 'expected_unchanged_parent_layers_for_rebase': expected_parent_layers,
        'targets': {str(n): {str(b): sha(z.tobytes()) for b, z in ll.items()} for n, ll in targets.items()},
        'translations': shifts, 'master_ref': 184, 'partial_RGBA_conditions_checked': partial_count,
        'preserve_empty_ref198': True, 'preserve_existing_empty678_records': True,
        'source_policy': '새 기본 원화의 머리/얼굴을 공통으로, 새 포스 원화의 장식39셀을 head5로 등록했다. 기존144alpha 내부만 사용하며 원화 외곽추가3/5셀은 입력에서 정한 내부 편집 범위 밖으로 제외했다. 기존 RGB 복사는 없다.',
        'alias_policy': '현재 수용 시부키19동형 정책과 각 원점을 보존한다. 원US의5/6고유 머리 복원은 아니다.',
        'rebase_rule': '후속 Root PL00 호버 부모는 SHA를 새 패킹 입력에 명시하고 팔레트 및184..203의100층이 이 기준 부모와 같은지 확인한 뒤 사용한다. 이전 PL00 전체를 새 호버 위에 덮지 않는다.',
        'arc_written': False, 'runtime_verified': False,
    })
    print(json.dumps({'manifest': sha((TD / 'manifest.json').read_bytes()), 'refs': len(REFS), 'layers': 95, 'partial_RGBA': partial_count, 'sources': len(files)}))


if __name__ == '__main__':
    main()
