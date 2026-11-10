"""명시한 시험 BIN만 읽기 전용으로 관찰한다. 활성 빌드 포인터는 건드리지 않는다."""
from pathlib import Path
from types import SimpleNamespace
import argparse, json, re, sys, time

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from scripts import observe_sprite_consistency_runtime as observer

p = argparse.ArgumentParser()
p.add_argument('plan', type=Path)
p.add_argument('session', type=Path)
p.add_argument('output', type=Path)
p.add_argument('--ram', type=int, required=True)
p.add_argument('--vram', type=int, required=True)
a = p.parse_args()
plan = json.loads(a.plan.read_text('utf8'))
project = plan['project']
session = a.session.resolve()
observer.need(session.is_relative_to(ROOT/'work'/project/'emulator_sessions'), 'Wrong session path')
record = json.loads((session/'session.local.json').read_text('utf8'))
cue = Path(record['cue'])
observer.need(cue.parent == (ROOT/plan['output']).resolve(), 'Session is not the selected trial')
match = re.match(r'FILE "([^"\r\n]+)" BINARY', cue.read_text('ascii'))
observer.need(match and Path(match[1]).name == match[1], 'Unsupported CUE')
game = cue.parent/match[1]
manifest = json.loads((cue.parent/'manifest.json').read_text('utf8'))
observer.need(observer.file_sha(game) == record['bin_sha256'] == manifest['modified_bin']['sha256'], 'Trial hash differs')
assets, _ = observer.read_assets(game, ['SLUS_005.61', 'LOAD_U.ARC', 'PL00_U.ARC', 'PL01_U.ARC', 'PL02_U.ARC'])
for name, resource in plan['resources'].items():
    if name in assets:
        observer.need(observer.sha(assets[name]) == resource['after'], 'Trial resource differs from frozen plan')
proc = observer.ReadOnlyProcess(record)
active = False
try:
    start = time.monotonic()
    while time.monotonic()-start < 42:
        ram = proc.read(a.ram, 0x200000)
        found = observer.identify(ram, assets)
        active = any(r[4] for r in found)
        if active:
            break
        time.sleep(.25)
finally:
    proc.close()
observer.need(active, 'No authenticated gameplay asset observed within 42 seconds')
observer.load = lambda s, q: (record, game, assets)
observer.main(SimpleNamespace(project=project, session=session, output=a.output,
                              ram_base=a.ram, vram_base=a.vram, seconds=10))
