"""기본/포스 작은머리19의 재현·거부·호버 보존을 검증하고 고정 준비본을 만든다."""
from pathlib import Path
import json
import shutil
import sys

H = Path(__file__).resolve().parent
ROOT = H.parents[2]
sys.path.insert(0, str(ROOT))
from native_pose_pack import need, sha, write
from pack_vehicle_head_base import build, validate, GEOMETRY, GEOMETRY_SHA, TD, MANIFEST, REFS
from scripts.export_x_consistency import Archive
from scripts.prepare_riko_ui import replace_entry

FINAL = '4ceab054c4fa9170a0e785fb00baa01f05afaceb4d2dfc2dcc4e80eab30ee36f'


def main():
    d = H / 'prepared_vehicle_head_base01'
    need(not d.exists(), '기존 준비본 보호')
    src = H / 'vehicle_head_base_pack01'
    candidate = (src / 'PL00_U.ARC').read_bytes()
    need(sha(candidate) == FINAL, '후보 변경')
    source = GEOMETRY.read_bytes()
    need(sha(source) == GEOMETRY_SHA, '부모 변경')
    repro = []
    for i in range(2):
        result, proof = build(source, GEOMETRY_SHA)
        need(result == candidate, '동일 재현 실패')
        repro.append(sha(result))
        print(json.dumps({'reproduction': i + 2, 'sha256': sha(result)}), flush=True)
    rejected = []
    normal = lambda p: p.read_bytes()

    def reject(name, data, expected, reader):
        try:
            validate(data, expected, reader)
        except (ValueError, json.JSONDecodeError, OSError) as ex:
            rejected.append({'case': name, 'reason': str(ex), 'rejected': True})
            return
        raise ValueError('변조 입력 수용: ' + name)

    bad = bytearray(source)
    bad[100] ^= 1
    reject('wrong_parent', bytes(bad), GEOMETRY_SHA, normal)
    reject('truncated_parent', source[:-1], GEOMETRY_SHA, normal)
    paths = [TD / 'manifest.json', TD / '184_bank0_indices.png', TD / '203_bank5_indices.png', TD / '196_bank8_indices.png', H / 'vehicle_head_base_inputs01/generated_v1.png', H / 'vehicle_head_base_inputs01/prompt_materials_v2.txt', H / 'vehicle_head_base_native02/registration.json', H / 'register_vehicle_head_base_semantic.py', H / 'prepare_vehicle_head_base_targets.py']
    for p in paths:
        def changed_reader(q, changed=p):
            blob = normal(q)
            return bytes([blob[0] ^ 1]) + blob[1:] if q.resolve() == changed.resolve() else blob
        reject('changed_' + p.relative_to(H).as_posix(), source, GEOMETRY_SHA, changed_reader)
    # 신규 부모를 허용하더라도 팔레트 또는 작은머리 의미층이 바뀌면 재결속을 거부한다.
    a = Archive(source)
    palette = bytearray(a.p)
    palette[2] ^= 1
    invalid = replace_entry(source, 9, bytes(palette))
    reject('forged_parent_changed_palette', invalid, sha(invalid), normal)
    reject('forged_parent_changed_head_layers', candidate, FINAL, normal)
    need(len(rejected) == 13, '거부 검사 수')
    b = Archive(candidate)
    hover = []
    for n in range(221, 231):
        for bank in (0, 5, 6, 7, 8):
            old, new = a.layer(n, bank)[0], b.layer(n, bank)[0]
            need(old.tobytes() == new.tobytes(), 'Root 호버 부모50층 보존')
            hover.append({'ref': n, 'layer': bank, 'sha256': sha(new.tobytes())})
    need(a.p == b.p, '팔레트 보존')
    need(sha(GEOMETRY.read_bytes()) == GEOMETRY_SHA, '부모 쓰기 발생')
    previous = json.loads((H / 'prepared_nova_strike_base01/proposal.json').read_text('utf8'))
    before_slack = json.loads((H / 'prepared_nova_strike_base01/verification.json').read_text('utf8'))['graphics']['remaining_slack']
    need(before_slack == 32 and proof['graphics']['remaining_slack'] == 150, '118B 절감 근거')
    d.mkdir()
    for p in src.glob('*.png'):
        shutil.copy2(p, d / p.name)
    shutil.copy2(src / 'PL00_U.ARC', d / 'PL00_U.ARC')
    proof.update(total_identical_builds=3, reproduction_sha256=repro, rejected_inputs=rejected, rejected_count=len(rejected), source_parent_preserved=True, hover10_50layers_exact=hover, palette_exact=True, graphics_remaining_before=before_slack, graphics_saved=118, first_part_packing_overflow_bytes=12, final_head5_slack=12, root_future_hover_rebase_required=True)
    write(d / 'verification.json', proof)
    meta = json.loads((TD / 'manifest.json').read_text('utf8'))
    files = dict(meta['source_files'])
    for p in TD.iterdir():
        if p.is_file():
            files[p.relative_to(ROOT).as_posix()] = sha(p.read_bytes())
    deps = ['pack_vehicle_head_base.py', 'verify_vehicle_head_base.py', 'native_pose_pack.py', 'pack_shibuki_hurt.py', 'pack_dash_complete.py', 'prepare_lowhp_final.py', 'repack_part_records_lossless.py']
    for name in deps:
        p = H / name
        files[p.relative_to(ROOT).as_posix()] = sha(p.read_bytes())
    for name in ('scripts/export_x_consistency.py', 'scripts/prepare_shibuki_ultimate_production.py', 'scripts/prepare_riko_ui.py', 'src/psx_player.py', 'src/psx_compress.py'):
        files[name] = sha((ROOT / name).read_bytes())
    write(d / 'INPUT_LOCK.json', {'parent_sha256': GEOMETRY_SHA, 'candidate_sha256': FINAL, 'target_manifest_sha256': MANIFEST, 'refs': list(REFS), 'files': files, 'all_inputs_fixed': True})
    lock_sha = sha((d / 'INPUT_LOCK.json').read_bytes())
    write(d / 'proposal.json', {
        'project': 'ver_buki_riko', 'baseline_sha256': previous['baseline_sha256'],
        'files': {'PL00_U.ARC': {'path': (d / 'PL00_U.ARC').relative_to(ROOT).as_posix(), 'before': previous['files']['PL00_U.ARC']['before'], 'after': FINAL}},
        'sequential_parent': {'path': GEOMETRY.relative_to(ROOT).as_posix(), 'sha256': GEOMETRY_SHA},
        'selected_refs': list(REFS), 'target_manifest': (TD / 'manifest.json').relative_to(ROOT).as_posix(), 'target_manifest_sha256': MANIFEST,
        'target_lock': (d / 'INPUT_LOCK.json').relative_to(ROOT).as_posix(), 'target_lock_sha256': lock_sha,
        'scope': '기본/포스 새 작은머리2셀의 공통 머릿결과 포스 장식39셀을19위치에 등록했다. 기존13×15/144alpha/홍채 원점과 빈198/678기록을 유지한다.95목표층·608부분·508raw/489비대상·1045층/1749기타조립·95GPU를 검증했다.',
        'storage_policy': '4타일 새 공통stream 및 동일 조립기록의 접두/접미 저장 공유만 사용한다. head5 첫초과12B→여유12B, gfx0 여유32→150B. 파츠별4바이트 순서/내용, 은행/entry/전체길이를 보존하며 새은행 이동·도트삭제·색축소가 없다.',
        'future_hover_parent': 'Root 호버10의50층/팔레트가36d4와 같은 상태다. 추후 호버는 이후보를 명시적 부모로 사용하고 작은머리19 및 다른범위를 보호한다.',
        'limits': ['현재 시부키19동형 정책이며 원US5/6고유 머리 복원이 아니다.', '원화에서 추가된 외곽3/5셀은 처음 요청한 내부 편집 범위 밖으로 제외했다. 기존144alpha 안은 새 source가 모두 존재하며 옛RGB 복사는 없다.', '포스39셀만 새 장식 donor로 사용하며 머리/얼굴은 기본공통, 홍채는CLUT0 색7을 유지한다. 금색3표본은 이미 최근접CLUT16 색10으로 추가 색변경이 없다.', '원 조종석·머리반전·실제 차량 게임 동작은 별도 검증이다.'],
        'native_cpu_pending': True, 'independent_pending': True, 'root_final_art_pending': True, 'runtime_verified': False, 'frozen': False,
    })
    write(d / 'PREPARED_LOCK.json', {'files': {p.name: sha(p.read_bytes()) for p in sorted(d.iterdir()) if p.is_file()}, 'source_scripts': {name: sha((H / name).read_bytes()) for name in deps}, 'target_lock_sha256': lock_sha, 'candidate_assets_fixed': True})
    write(H / 'vehicle_head_base_components.json', {'project': 'ver_buki_riko', 'source_bin': 'out/ver_buki_riko/sprite_style_unification_20261107_v30/shibuki_riko.bin', 'source_sha256': 'ccdf6058c2f105057dbb105c71988d683ffca604492b60c665e5f2eab2f69875', 'resources': {'PL00_U.ARC': {'path': (d / 'PL00_U.ARC').relative_to(ROOT).as_posix(), 'before': GEOMETRY_SHA, 'after': FINAL}}, 'checkpoint_only': True, 'scope_note': '기본/포스 작은머리19 원디코더/업로드/GPU 검사. 실제게임 또는 전체directory 검사가 아니다.'})
    print(json.dumps({'candidate': FINAL, 'input_lock': lock_sha, 'input_files': len(files), 'rejected': len(rejected), 'proposal': sha((d / 'proposal.json').read_bytes()), 'prepared_lock': sha((d / 'PREPARED_LOCK.json').read_bytes())}))


if __name__ == '__main__':
    main()
