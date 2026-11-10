"""공용 sound-bank parser를 독립 전수 목록과 대조한다. 읽기 전용."""
import json
import hashlib
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from scripts.discover_inputs import DiscReader
from scripts.overhaul_audio_verify_cpu import banks

def main():
    results = []
    for source in ('us', 'jp', 'ver_buki_riko', 'ver_rin_nana'):
        inv = json.loads((ROOT / 'work/boss_voice_restore_20261105/assets' /
                          (source + '_inventory.json')).read_text('utf8'))
        expected = {(x['path'], x['bank']['slot']): (x['header_sha256'], x['body_sha256'])
                    for x in inv['banks']}
        parsed = {r['record']['path'] for r in inv['archives'] if r['parsed']}
        path = ROOT / inv['path']
        actual = {}
        with path.open('rb') as f:
            d = DiscReader(f, path.stat().st_size)
            for r in d.inspect()['files']:
                if r['path'] not in parsed:
                    continue
                for slot, (h, b, q) in banks(d.read(r['lba'], r['size'])).items():
                    actual[r['path'], slot] = (hashlib.sha256(h).hexdigest(), hashlib.sha256(b).hexdigest())
        assert actual == expected
        results.append({'source': source, 'banks': len(actual),
                        'header_and_body_match_independent_inventory': True})
    report = {'passed': True, 'cases': results, 'source_files_written': False}
    Path(__file__).with_suffix('.json').write_text(json.dumps(report, indent=2), 'utf8')
    print(json.dumps(report))

if __name__ == '__main__':
    main()
