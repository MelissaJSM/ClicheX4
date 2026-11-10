"""고정된 최신 두 제로 준비본을 원래 디코더로 검증한다. BIN은 쓰지 않는다."""
import json
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.append(str(ROOT / 'work/tools/korean_env/Lib/site-packages'))
from scripts.verify_consistency_native import verify

W = ROOT / 'work/sprite_style_unification_20261107'
for mode, proposal in [
    ('br', 'zero_audit/riko_restore/prepared_cloth_v1/proposal.json'),
    ('rn', 'zero_audit/rin_extension/prepared_run_v1/proposal.json'),
]:
    p = json.loads((W / proposal).read_text('utf8'))
    plan = json.loads((W / f'checkpoint_{mode}_components.json').read_text('utf8'))
    parent_hash = plan['resources']['PL01_U.ARC']['before']
    plan['resources'] = {'PL01_U.ARC': {
        'path': p['resource'], 'before': parent_hash, 'after': p['after_sha256']}}
    dest = W / f'zero_{mode}_current_components.json'
    dest.write_text(json.dumps(plan, ensure_ascii=False, indent=2)+'\n', 'utf8')
    verify(dest)
