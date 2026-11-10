"""새 공중22참조를 기존 PL02 경계 안에 패킹하고 전후44표시를 재검증한다."""
from pathlib import Path
import argparse, json, sys
H = Path(__file__).resolve().parent
ROOT = H.parents[2]
sys.path.insert(0, str(ROOT))
import numpy as np
from PIL import Image
import pack_ultimate_lowhp as core
from native_pose_pack import need, sha, write, same_rgba
from scripts.export_x_consistency import Archive, page
from scripts.discover_inputs import psx_arc
from src.psx_player import bank_offsets, composition_frame, decode_stream, indexed_atlas

PARENT = H / 'prepared_rising_right_ultimate01/PL02_U.ARC'
PARENT_SHA = 'd636032c2ace44e66f5f6303c62315ad4335b9d2bf46b0eff61c3cf1bf94a39d'
TARGETS = H / 'ultimate_air_targets02'
LOCK_SHA = 'bd7ca64adbf3dd1c65964d74984a47f905ff0776b8fcdcb6871d87fcea0b6ef4'
REFS = set(range(33, 55))

def validate_inputs(data, read=lambda p: p.read_bytes()):
    need(sha(data) == PARENT_SHA, 'Wrong frozen exact parent')
    raw = read(TARGETS / 'LOCK.json')
    need(sha(raw) == LOCK_SHA, 'Wrong target lock')
    lock = json.loads(raw)
    need(lock['refs'] == sorted(REFS) and len(lock['files']) == 44, 'Wrong exact scope')
    for name, digest in lock['files'].items():
        need(sha(read(TARGETS / name)) == digest, 'Target changed: ' + name)
    for name, digest in lock['source_files'].items():
        need(sha(read(H / name)) == digest, 'Source changed: ' + name)
    return lock

def values():
    return {form: {ref: np.array(Image.open(TARGETS / f'{form}_{ref:03}_indices.png')) for ref in REFS} for form in ('before', 'after')}

def build(data, targets):
    core.PSHA = PARENT_SHA
    core.SELECTED = REFS
    return core.pack(data, targets['before'], targets['after'])

def rejection_tests(data):
    cases = []
    wrong = bytearray(data); wrong[1024] ^= 1
    try:
        validate_inputs(bytes(wrong))
    except ValueError:
        cases.append('parent_hash')
    else:
        raise ValueError('Wrong parent accepted')
    for target in [TARGETS / 'LOCK.json', TARGETS / 'after_044_indices.png', H / 'ultimate_air_shot_inputs01/page04/generated.png']:
        def bad_read(path):
            raw = path.read_bytes()
            return raw + b'wrong' if path == target else raw
        try:
            validate_inputs(data, bad_read)
        except ValueError:
            cases.append(target.relative_to(H).as_posix())
        else:
            raise ValueError('Wrong source accepted')
    return cases

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', default='prepared_ultimate_air01')
    args = ap.parse_args()
    out = (H / args.out).resolve()
    need(out.is_relative_to(H.resolve()) and out != H.resolve() and not out.exists(), 'Fresh owned output required')
    data = PARENT.read_bytes()
    lock = validate_inputs(data)
    target = values()
    packed, proof = build(data, target)
    reproduced, _ = build(data, target)
    need(packed == reproduced, 'Nondeterministic packing')
    a, b = Archive(data), Archive(packed)
    need(bank_offsets(a.c) == bank_offsets(b.c), 'Composition bank boundaries moved')
    for old, new in zip(a.banks, b.banks):
        need((old['base'], old['end'], len(old['frames'])) == (new['base'], new['end'], len(new['frames'])), 'Graphics bank boundaries moved')
    layers = non_layers = partials = gpu_parts = casings = 0
    for ref in range(237):
        if ref in {105, *range(175, 183)}:
            continue
        expected = None
        if ref in REFS:
            before, after = target['before'][ref], target['after'][ref]
            expected = {0: after, 5: np.where(same_rgba(a, before, after), 0, before).astype(np.uint8)}
            expected.update({p: np.zeros((384, 384), np.uint8) for p in (6, 7, 8)})
        for pb in (0, 5, 6, 7, 8):
            want = expected[pb] if expected is not None else a.layer(ref, pb)[0]
            need(np.array_equal(b.layer(ref, pb)[0], want), f'Layer mismatch: {ref}/{pb}')
            layers += 1
            non_layers += int(ref not in REFS)
        if ref not in REFS:
            continue
        for mask in range(16):
            for arm in (1, 2):
                want = a.rgba(before, 16) if mask & 1 else a.rgba(after, 0)
                need(b.composite(ref, mask, arm)[0].tobytes() == want.tobytes(), f'Partial mask mismatch: {ref}/{mask}/{arm}')
                partials += 1
        f = b.banks[0]['frames'][ref]
        need(f['tile_count'] == 32, 'Target tile count changed')
        raw = decode_stream(b.g, f['offset'], f['limit'], 4096).data
        atlas = np.frombuffer(indexed_atlas(raw, 32)[0], np.uint8).reshape(32, 256)
        for pb in (0, 5, 6, 7, 8):
            for part in composition_frame(b.c, pb, ref)['parts']:
                t = part['tile']
                tile = atlas[t // 16 * 16:t // 16 * 16 + 16, t % 16 * 16:t % 16 * 16 + 16]
                if t % 16 == 0:
                    need(not tile[:, 0].any(), 'GPU U boundary hazard')
                if part['flip_y']:
                    need(not tile[0].any(), 'GPU flipped first-row hazard')
                gpu_parts += 1
        if ref % 2 == 0:
            gun = np.array(Image.open(H / 'ultimate_air_shot_inputs01/barrels' / f'{ref:03}_indices.png'))
            guard = np.array(Image.open(H / 'ultimate_air_shot_inputs01/barrels' / f'{ref:03}_mask.png')) > 0
            for form, mask, pal in [('before', 15, 16), ('after', 0, 0)]:
                actual = np.array(b.composite(ref, mask)[0]); want = np.array(a.rgba(gun, pal))
                need(np.array_equal(actual[guard], want[guard]), 'Accepted casing/muzzle mismatch')
                casings += 1
    allowed = np.zeros(len(data), bool)
    for e in psx_arc(data):
        if int(e['type'], 16) in (2, 3):
            allowed[e['offset']:e['offset'] + e['size']] = True
    need(len(data) == len(packed) and not np.any((np.frombuffer(data, np.uint8) != np.frombuffer(packed, np.uint8)) & ~allowed), 'Non-graphics byte changed')
    rejected = rejection_tests(data)
    out.mkdir()
    (out / 'PL02_U.ARC').write_bytes(packed)
    sheets = []
    for form, mask in [('before', 15), ('after', 0)]:
        pics = []
        for ref in sorted(REFS):
            actual = b.composite(ref, mask)[0]
            actual.save(out / f'{form}_{ref:03}.png')
            pics.extend([(f'{ref} parent', a.composite(ref, mask)[0]), (f'{ref} actual packed', actual)])
        for i in range(0, len(pics), 12):
            name = f'{form}_readback_{i // 12:02}.png'
            page(pics[i:i + 12], b.composite(0, mask)[0], out / name, cols=4, scale=5)
            sheets.append(name)
    proof.update({'all_layers_checked': layers, 'non_target_layers_preserved': non_layers, 'partial_costume_combinations': partials, 'gpu_parts_checked': gpu_parts, 'casing_rgba_checks': casings, 'casing_module': '原PL02 after34の60pix；각 원래 총구 좌표로 평행이동. 각옛총열모양 완전보존 아님.', 'target_lock_sha256': LOCK_SHA, 'source_art_manifest': (TARGETS / 'LOCK.json').relative_to(ROOT).as_posix(), 'reproducible_same_sha256': sha(reproduced), 'rejected_bad_inputs': rejected, 'fixed_graphics_and_composition_boundaries': True, 'outside_graphics_entries_exact': True, 'actual_readback_sheets': sheets, 'actual_gameplay_tested': False, 'independent_review_pending': True, 'root_native_cpu_gpu_pending': True, 'root_visual_review_pending': True, 'full_unification_complete': False})
    write(out / 'verification.json', proof)
    write(out / 'proposal.json', {'project': 'ver_buki_riko', 'baseline_sha256': '21bee159a1267d56561d4fa15c99ec652780af782fe08a433859c9eb7676099a', 'files': {'PL02_U.ARC': {'path': (out / 'PL02_U.ARC').relative_to(ROOT).as_posix(), 'before': '98ab01e8581d6bca15d75d703e7605899f2a871e042f5b09b13c5f2e07cf132e', 'after': sha(packed)}}, 'sequential_parent': {'path': PARENT.relative_to(ROOT).as_posix(), 'sha256': PARENT_SHA}, 'replaces': (PARENT.parent / 'proposal.json').relative_to(ROOT).as_posix(), 'parent_arc_sha256': PARENT_SHA, 'supersedes': 'prepared_rising_right_ultimate01; all earlier accepted run/wall/lowHP/rising/capsule preserved', 'selected_visual_refs': sorted(REFS), 'source_art_manifest': (TARGETS / 'LOCK.json').relative_to(ROOT).as_posix(), 'source_art_manifest_sha256': LOCK_SHA, 'scope': '얼티밋 공중/사격33..54의 두 의상44표시 상세화. 새머리·옷·팔·다리 사용, 원총구 좌표·성능·시간표·효과 유지.', 'static_review_passed': True, 'actual_gameplay_pending': True, 'native_cpu_pending': True, 'independent_review_pending': True})
    write(out / 'INPUT_FROZEN.json', {'files': {name: sha((out / name).read_bytes()) for name in ('PL02_U.ARC', 'proposal.json', 'verification.json')}, 'target_lock_sha256': LOCK_SHA, 'source_files': lock['source_files'], 'input_art_immutable': True, 'approved_for_game_integration': False})
    print(json.dumps({k: proof[k] for k in ('after_arc_sha256', 'parts_slack', 'raw_checked', 'non_target_raw_preserved', 'all_layers_checked', 'partial_costume_combinations', 'gpu_parts_checked', 'casing_rgba_checks')}))

if __name__ == '__main__':
    main()
