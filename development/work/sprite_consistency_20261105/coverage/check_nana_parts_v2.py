"""동결된 첫 독립 검사에 GPU 첫열 여백을 적용한 v2를 별도 검증한다."""
from pathlib import Path
import json
import numpy as np

HERE = Path(__file__).resolve().parent
source = HERE / 'check_prepared_independent.py'
code = source.read_text('utf8').split("report={'nana_parts':nana()", 1)[0]
old = "x/nana_parts_fix/proposal.json"
assert code.count(old) == 1
code = code.replace(old, 'x/nana_parts_fix/prepared_v2/proposal.json')
old = "bb==aa+[(0,16,min(x for x,y in pts),min(y for x,y in pts))]"
assert code.count(old) == 1
code = code.replace(old, 'bb==aa+[(0,16,min(x for x,y in pts)-1,min(y for x,y in pts))]')
namespace = {'__file__': str(source), '__name__': 'frozen_audit_v2'}
exec(compile(code, str(source), 'exec'), namespace)
report = namespace['nana']()
cov = namespace['cov']; root = namespace['ROOT']
arc = (root / 'work/sprite_consistency_20261105/x/nana_parts_fix/prepared_v2/PL00_U.ARC').read_bytes()
entries = namespace['es'](arc)
from src.psx_player import indexed_atlas, composition_frame
checks = []
for bank, n in report['changed_raw_refs']:
    raw, f = namespace['raw'](entries, bank, n)
    pixels = np.frombuffer(indexed_atlas(raw, f['tile_count'])[0], np.uint8).reshape(-1, 256)
    part = composition_frame(entries[3], 5, n)['parts'][-1]
    assert part['tile'] == 16 and not part['flip_y'] and not np.any(pixels[16:32, 0])
    checks.append({'frame': n, 'new_tile': 16, 'first_column_all_transparent': True,
                   'part_flip_y': False, 'part_x': part['x'], 'first_opaque_column': 1})
report['new_tile_gpu_left_edge_checks'] = checks
report['actual_gpu_runtime_verified'] = False
cov.write(HERE / 'nana_parts_v2_independent.json', report)
print(json.dumps({'passed': report['passed'], 'UI_frames': report['ui_all_composed_frames'], 'padded_tiles': len(checks)}))
