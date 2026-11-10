"""작성 담당의 패킹 함수를 사용하지 않는 새 이동/사격 ARC 독립 대조."""
import hashlib
import json
from pathlib import Path
import sys

import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT))
from scripts.c01_audio_build import read_disc
from scripts.discover_inputs import psx_arc
from scripts.export_x_consistency import Archive
from scripts.prepare_riko_ui import entry
from src.psx_disc import file_hash
from src.psx_player import decode_stream, composition_frame


def sha(value):
    return hashlib.sha256(value).hexdigest()


def main():
    folder = HERE / 'shibuki_audit'
    proposal = json.loads((folder / 'prepared_run_complete03/proposal.json').read_text('utf8'))
    source = ROOT / 'out/ver_buki_riko/sprite_reaudit_20261106_v1/shibuki_riko.bin'
    assert file_hash(source) == proposal['baseline_sha256']
    expected = proposal['files']['PL02_U.ARC']
    original = read_disc(source, ('PL02_U.ARC',))[0]['PL02_U.ARC']
    candidate = (ROOT / expected['path']).read_bytes()
    assert sha(original) == expected['before'] and sha(candidate) == expected['after']
    assert len(original) == len(candidate)
    layout = lambda data: [(e['type'], e['offset'], e['size']) for e in psx_arc(data)]
    assert layout(original) == layout(candidate)
    for e in psx_arc(original):
        if int(e['type'], 16) not in (2, 3):
            a, b = e['offset'], e['offset'] + e['size']
            assert original[a:b] == candidate[a:b]
    old, new = Archive(original), Archive(candidate)
    changed_raw, raw_count = [], 0
    for bank_index, bank in enumerate(new.banks):
        assert len(bank['frames']) == len(old.banks[bank_index]['frames'])
        for f, before in zip(bank['frames'], old.banks[bank_index]['frames']):
            a = decode_stream(new.g, f['offset'], f['limit'], f['tile_count'] * 128).data
            b = decode_stream(old.g, before['offset'], before['limit'], before['tile_count'] * 128).data
            raw_count += 1
            if a != b:
                changed_raw.append([bank_index, f['index']])
                assert bank_index == 0 and 3 <= f['index'] <= 32
                assert f['tile_count'] <= 32
    target_count = preserved_count = barrel_count = 0
    for ref in range(237):
        if not 3 <= ref <= 32:
            for pb in (0, 5, 6, 7, 8):
                a = composition_frame(new.c, pb, ref)['parts']
                b = composition_frame(old.c, pb, ref)['parts']
                # Records can move inside the fixed bank when target records grow.
                semantic = lambda parts: [{k: v for k, v in p.items() if k != 'record_offset'} for p in parts]
                assert semantic(a) == semantic(b), ('non-target composition', pb, ref)
        for form, mask, palette_start in (('before', 15, 16), ('after', 0, 0)):
            try:
                image = new.composite(ref, mask)[0]
                before_image = old.composite(ref, mask)[0]
            except (ValueError, IndexError):
                # This archive retains original incomplete/unreachable references.
                assert ref == 105 or ref in range(175, 183)
                try:
                    old.composite(ref, mask)
                except (ValueError, IndexError):
                    pass
                else:
                    raise AssertionError(('new failure', ref, mask))
                continue
            if 3 <= ref <= 32:
                registration = folder / ('run_registered02' if ref % 2 else 'shot_registered05')
                pixels = np.array(Image.open(registration / form / f'{ref:03}_indices.png'))
                target = new.rgba(pixels, palette_start)
                assert image.tobytes() == target.tobytes(), (ref, form)
                target_count += 1
                if ref % 2 == 0:
                    barrel = np.array(Image.open(folder / 'shot_inputs01/before' / f'{ref:03}_barrel_indices.png')) > 0
                    assert np.array_equal(np.array(image)[barrel], np.array(before_image)[barrel])
                    barrel_count += 1
            else:
                assert image.tobytes() == before_image.tobytes(), (ref, form)
                preserved_count += 1
    assert target_count == 60 and barrel_count == 30
    report = {
        'passed': True, 'candidate_sha256': sha(candidate),
        'source_bin_sha256': file_hash(source), 'all_raw_references': raw_count,
        'changed_raw': changed_raw, 'exact_registered_targets': target_count,
        'preserved_non_targets': preserved_count, 'original_barrel_RGBA_checks': barrel_count,
        'other_entries_audio_palettes_exact': True, 'fixed_archive_layout': True,
        'independent_of_packer': True, 'runtime_gameplay_verified': False,
    }
    (HERE / 'shibuki_run_independent.json').write_text(json.dumps(report, indent=2) + '\n', 'utf8')
    print(json.dumps(report))


if __name__ == '__main__':
    main()
