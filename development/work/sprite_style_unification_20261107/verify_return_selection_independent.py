"""귀환158과 선택창 사본의 실제 표시를 원화/작성 패커와 독립적으로 대조."""
from pathlib import Path
import json
import sys
import numpy as np
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from scripts.c01_audio_build import read_disc
from scripts.export_x_consistency import Archive
from scripts.build_sprite_style_album import selection_image
from scripts.build_sprite_style_unification import check_selection
from scripts.build_sprite_consistency import check_resource
from src.psx_disc import file_hash

HERE = Path(__file__).resolve().parent
FOLDER = HERE / 'shibuki_audit/prepared_return158_01'


def main():
    proposal = json.loads((FOLDER / 'proposal.json').read_text('utf8'))
    source = ROOT / 'out/ver_buki_riko/sprite_reaudit_20261106_v1/shibuki_riko.bin'
    assert file_hash(source) == proposal['baseline_sha256']
    assets = read_disc(source, ('PL00_U.ARC', 'ST0E_U1.ARC', 'COL0E_U1.ARC'))[0]
    changed = assets.copy()
    for name, record in proposal['files'].items():
        p = ROOT / record['path']
        assert file_hash(p) == record['after']
        changed[name] = p.read_bytes()
    check_resource('PL00_U.ARC', assets['PL00_U.ARC'], changed['PL00_U.ARC'])
    check_selection(assets['ST0E_U1.ARC'], changed['ST0E_U1.ARC'])
    frame = {'bank': 2, 'ref': 21}
    old_ui, new_ui = selection_image(assets, frame), selection_image(changed, frame)
    old, new = Archive(assets['PL00_U.ARC']), Archive(changed['PL00_U.ARC'])
    old_body, new_body = old.composite(158, 0)[0], new.composite(158, 0)[0]
    a, b = old_ui.getbbox(), old_body.getbbox()
    dx, dy = a[0] - b[0], a[1] - b[1]
    moved = lambda im: np.roll(np.roll(np.array(im), dy, axis=0), dx, axis=1)
    assert np.array_equal(np.array(old_ui), moved(old_body)), 'Original UI origin mapping failed'
    assert np.array_equal(np.array(new_ui), moved(new_body)), 'New UI copy differs from actual gameplay body'
    unchanged = 0
    for ref in range(237):
        for mask in (0, 15):
            if ref == 158:
                continue
            try:
                a, b = old.composite(ref, mask)[0], new.composite(ref, mask)[0]
            except ValueError:
                assert ref == 105 or ref in range(175, 183)
                continue
            assert a.tobytes() == b.tobytes(), (ref, mask)
            unchanged += 1
    report = {'passed': True, 'PL00_sha256': file_hash(FOLDER/'PL00_U.ARC'),
              'selection_sha256': file_hash(FOLDER/'ST0E_U1.ARC'),
              'gameplay_to_selection_translation': [dx, dy], 'original_and_new_copies_pixel_exact': True,
              'unchanged_gameplay_form_references': unchanged, 'selection_non_targets_and_geometry_exact': True,
              'only_PL00_ref158_and_selection_bank2_ref21': True, 'runtime_verified': False}
    (HERE/'return158_independent.json').write_text(json.dumps(report, indent=2)+'\n', 'utf8')
    print(json.dumps(report))


if __name__ == '__main__':
    main()
