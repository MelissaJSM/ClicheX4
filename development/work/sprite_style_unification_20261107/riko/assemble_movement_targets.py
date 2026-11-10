"""Collect individually reviewed movement artwork without replacing locked idle/run keys."""
from pathlib import Path
import json, hashlib
from PIL import Image
ROOT=Path(__file__).resolve().parents[3]
D=Path(__file__).resolve().parent/'movement_clothes14'
OUT=D/'targets01'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
frames=[];sources=[]
for page in [2,3,4,5]:
    folder=D/f'page{page}'/'registered01'
    info=json.loads((D/f'page{page}'/'inputs.json').read_text('utf8'))
    reg=json.loads((folder/'registration.json').read_text('utf8'))
    assert reg['source_sha256']=='03fa9ef5b662a71963f1b4e2be5a00fb7f18202e834e33f595a2b6b672c1d6a3'
    sources.append(reg)
    allowed=info.get('apply_only_refs',[r['ref']for r in info['frames']])
    for r in reg['frames']:
        if r['ref']not in allowed:continue
        p=ROOT/r['target'];assert sha(p)==r['target_sha256']
        assert Image.open(p).size==(384,384)
        frames.append(dict(r))
assert sorted(r['ref']for r in frames)==[3,4,7,9,10,11,12,13,15,16,17,18,19,20]
contact=json.loads((D/'contacts_probe01/registration.json').read_text('utf8'))
assert contact['source_sha256']==sources[0]['source_sha256']
aligned={r['ref']:r for r in contact['frames']}
for r in frames:
    q=aligned[r['ref']]
    assert q['source_sha256']==r['target_sha256']
    assert q['original_sole_y']==q['new_sole_y']
    r.update(q)
assert not OUT.exists();OUT.mkdir()
for r in frames:
    p=ROOT/r['target'];dst=OUT/p.name;dst.write_bytes(p.read_bytes());r['target']=str(dst.relative_to(ROOT));r['target_sha256']=sha(dst)
(OUT/'registration.json').write_text(json.dumps(dict(source_sha256=sources[0]['source_sha256'],sources=sources,contacts=contact,frames=frames,locked_unchanged=[5,6,8,14,147],runtime_verified=False),indent=2)+'\n','utf8')
print(OUT)
