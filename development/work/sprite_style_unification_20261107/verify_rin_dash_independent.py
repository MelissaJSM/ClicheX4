"""작성기와 별개로 린 대시 7참조의 원화/비대상/공유 상태를 확인한다."""
from pathlib import Path
import hashlib, json, sys
import numpy as np
from PIL import Image
W = Path(__file__).resolve().parent
ROOT = W.parents[1]
sys.path.insert(0, str(ROOT))
from scripts.overhaul_sprites_audit import render
from scripts.prepare_riko_ui import entry
from scripts.discover_inputs import psx_arc
from src.psx_player import graphics_bank, decode_stream, composition_frame
sha = lambda b: hashlib.sha256(b).hexdigest()
D = W / 'zero_audit/rin_extension'
p = json.loads((D/'prepared_dash_v2/proposal.json').read_text('utf8'))
old, new = (ROOT/p['source_arc']).read_bytes(), (ROOT/p['resource']).read_bytes()
assert sha(old) == p['source_arc_sha256'] and sha(new) == p['after_sha256']
assert len(old) == len(new)
assert [(e['type'],e['offset'],e['size']) for e in psx_arc(old)] == [(e['type'],e['offset'],e['size']) for e in psx_arc(new)]
for e in psx_arc(old):
    if int(e['type'],16) not in (2,3):
        assert old[e['offset']:e['offset']+e['size']] == new[e['offset']:e['offset']+e['size']]
mp=ROOT/p['art_manifest']; assert sha(mp.read_bytes())==p['art_manifest_sha256']
manifest=json.loads(mp.read_text('utf8')); art={}
for r in manifest['inputs']:
    path=ROOT/r['path']; assert sha(path.read_bytes())==r['sha256']
    if path.name.startswith('b0_') and path.name.endswith('_indices.png'):
        art[int(path.name.split('_')[1])] = np.array(Image.open(path))
targets={n:art[{47:46,48:46,52:51}.get(n,n)] for n in p['references']}
counts={'raw':0,'display':0,'target_exact':0,'other_raw_exact':0,'other_display_exact':0,'other_parts_exact':0}
g,ng,c,nc=entry(old,2),entry(new,2),entry(old,3),entry(new,3)
semantic=lambda cp:[(v['flags'],v['tile'],v['x'],v['y']) for v in cp['parts']]
for bank in (0,1):
    for a,b in zip(graphics_bank(g,bank)['frames'],graphics_bank(ng,bank)['frames']):
        n=a['index']; selected=bank==0 and n in targets
        ar=decode_stream(g,a['offset'],a['limit'],a['tile_count']*128).data
        br=decode_stream(ng,b['offset'],b['limit'],b['tile_count']*128).data
        assert a['tile_count']==b['tile_count']<=32
        counts['raw']+=1
        if not selected:
            assert ar==br;counts['other_raw_exact']+=1
            assert semantic(composition_frame(c,bank*5,n))==semantic(composition_frame(nc,bank*5,n))
            counts['other_parts_exact']+=1
        if bank==1 and 42<=n<=49:continue
        before,after=render(old,bank,bank*5,n)[0],render(new,bank,bank*5,n)[0]
        assert np.array_equal(after,targets[n] if selected else before),(bank,n)
        counts['display']+=1;counts['target_exact' if selected else 'other_display_exact']+=1
for refs in ((46,47,48),(51,52)):
    bank=graphics_bank(ng,0)
    assert len({bank['frames'][n]['offset'] for n in refs})==1
assert counts=={'raw':444,'display':436,'target_exact':7,'other_raw_exact':437,'other_display_exact':429,'other_parts_exact':437}
report={'passed':True,'candidate_sha256':sha(new),'counts':counts,'palette_audio_other_entries_exact':True,
        'source_art_exact':True,'independent_of_packer':True,'gameplay_runtime_verified':False}
(W/'rin_dash_independent.json').write_text(json.dumps(report,indent=2)+'\n','utf8')
print(json.dumps(report))
