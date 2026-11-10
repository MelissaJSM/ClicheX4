"""이번 통합 수정의 폐기된 중간 BIN 5개만 복원 검증 후 차이 ZIP으로 보관한다."""
import json
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.compact_builds import compact

TARGETS = [
    ('ver_buki_riko', 'pilot01', '5de7d4e4b3e552005a99f542c0af00b4b11438046e80d22359f955b6ad41cfe8'),
    ('ver_buki_riko', 'candidate02', '3344f2a94a3a88beeb2b6906ee8f2c3d28d1400d2478fc77a395d24af0fce275'),
    ('ver_buki_riko', 'candidate03', 'be4468029fe2941a840b9693558cbaccc980b7519e6df2f2af9f66f208506c1e'),
    ('ver_rin_nana', 'candidate02', '610ebea71ad54569f081f03b96a7178cae91e2038f43eaa498412c9dac4773fd'),
    ('ver_rin_nana', 'review03', '1e2089b31543244befe6c4ffc8aae9ac6a532c7e9a82ea20b8781a2fd63eece2'),
]

def main():
    from scripts.overhaul_activate import BUILDS
    for project, (_, expected) in BUILDS.items():
        current = json.loads((ROOT / 'projects' / project / 'current_build.json').read_text('utf8'))
        if current['sha256'] != expected:
            raise ValueError('Final active build not installed')
    results = []
    report = ROOT / 'work/overhaul_20261105/application/intermediate_archives.json'
    if report.exists():
        raise ValueError('Archive receipt already exists')
    for project, suffix, expected in TARGETS:
        stem = 'shibuki_riko' if project == 'ver_buki_riko' else 'rin_nana'
        relative = f'out/{project}/overhaul_20261105_{suffix}/{stem}.bin'
        manifest = json.loads((ROOT / relative).with_name('integration.json').read_text('utf8'))
        if manifest['modified_bin']['sha256'] != expected:
            raise ValueError('Intermediate identity differs')
        result = compact(ROOT, relative, expected)
        results.append(result)
        print(json.dumps(result), flush=True)
        report.write_text(json.dumps(results, indent=2) + '\n', 'utf8')
    print(json.dumps({'count': len(results), 'saved_bytes': sum(r['original_bytes']-r['archive_bytes'] for r in results)}))

if __name__ == '__main__':
    main()
