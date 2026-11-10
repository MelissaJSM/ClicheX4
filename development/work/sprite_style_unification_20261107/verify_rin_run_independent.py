"""린 이동 후보를 작성기의 패킹 함수 없이 실제 ARC와 원화로 대조한다."""
import hashlib
import json
from pathlib import Path
import sys
import numpy as np
from PIL import Image
W = Path(__file__).resolve().parent
ROOT = W.parents[1]
sys.path.insert(0, str(ROOT))
from scripts.c01_audio_build import read_disc
from scripts.overhaul_sprites_audit import render
from scripts.prepare_riko_ui import entry
from scripts.discover_inputs import psx_arc
from src.psx_disc import file_hash
from src.psx_player import graphics_bank, decode_stream, composition_frame

sha = lambda b: hashlib.sha256(b).hexdigest()
D = W / 'zero_audit/rin_extension'
p = json.loads((D / 'prepared_run_v1/proposal.json').read_text('utf8'))
source = ROOT / p['source_bin']
assert file_hash(source) == p['source_bin_sha256']
old = read_disc(source, ('PL01_U.ARC',))[0]['PL01_U.ARC']
new = (ROOT / p['resource']).read_bytes()
assert sha(old) == p['source_arc_sha256'] and sha(new) == p['after_sha256']
assert len(old) == len(new)
layout = lambda b: [(e['type'], e['offset'], e['size']) for e in psx_arc(b)]
assert layout(old) == layout(new)
for e in psx_arc(old):
    if int(e['type'], 16) not in (2, 3):
        s, n = e['offset'], e['size']
        assert old[s:s+n] == new[s:s+n]
manifest_path = ROOT / p['art_manifest']
assert file_hash(manifest_path) == p['art_manifest_sha256']
manifest = json.loads(manifest_path.read_text('utf8'))
targets = {}
for f in manifest['frames']:
    path = ROOT / f['path']
    assert file_hash(path) == f['sha256']
    targets[f['ref']] = np.array(Image.open(path))
assert sorted(targets) == p['references']
raw_count = display_count = preserved = 0
g, ng, c, nc = entry(old, 2), entry(new, 2), entry(old, 3), entry(new, 3)
for bank in (0, 1):
    a, b = graphics_bank(g, bank), graphics_bank(ng, bank)
    assert len(a['frames']) == len(b['frames'])
    for af, bf in zip(a['frames'], b['frames']):
        ref = af['index']
        selected = bank == 0 and ref in targets
        ar = decode_stream(g, af['offset'], af['limit'], af['tile_count']*128).data
        br = decode_stream(ng, bf['offset'], bf['limit'], bf['tile_count']*128).data
        assert bf['tile_count'] <= 32
        raw_count += 1
        if not selected:
            assert ar == br
            semantic = lambda parts: [(v['flags'], v['tile'], v['x'], v['y']) for v in parts]
            assert semantic(composition_frame(c, bank*5, ref)['parts']) == semantic(composition_frame(nc, bank*5, ref)['parts'])
        if bank == 1 and 42 <= ref <= 49:
            assert not selected
            continue
        before, after = render(old, bank, bank*5, ref)[0], render(new, bank, bank*5, ref)[0]
        assert np.array_equal(after, targets[ref] if selected else before), (bank, ref)
        display_count += 1
        preserved += not selected
report = {'passed': True, 'candidate_sha256': sha(new), 'raw_references': raw_count,
          'display_references': display_count, 'exact_new_art_targets': len(targets),
          'preserved_display_references': preserved, 'palette_audio_other_entries_exact': True,
          'independent_of_packer': True, 'runtime_gameplay_verified': False}
(W / 'rin_run_independent.json').write_text(json.dumps(report, indent=2)+'\n', 'utf8')
print(json.dumps(report))
