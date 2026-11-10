"""Pack detailed movement targets while preserving all other decoded displays."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[3];W=ROOT/'work/sprite_style_unification_20261107'
sys.path.insert(0,str(ROOT));sys.path.insert(0,str(W/'zero_audit'))
import pack_riko_cloth as engine
from lossless_stream_pack import repack
P=W/'riko/prepared_movement_clothes_v1/PL01_U.ARC';PSHA='df73f6a50dc13c9b5c00b8cc60ab474e7b725011ea896f94712013f7fe411e7a'
ART=W/'riko/rising_clothes15/targets01';OUT=W/'riko/prepared_rising_clothes_v1'
assert not OUT.exists();arc=P.read_bytes();assert engine.native.sha(arc)==PSHA
reg=json.loads((ART/'registration.json').read_text('utf8'));assert reg['source_sha256']==PSHA
masters={}
for r in reg['frames']:
    p=ROOT/r['target'];assert engine.native.sha(p.read_bytes())==r['target_sha256'];masters[r['bank'],r['ref']]=np.array(Image.open(p))
assert set(masters)=={(1,n)for n in list(range(133,145))+[146,156,158]}
targets={k:v.copy()for k,v in masters.items()};keys={k:(k[1],0,0)for k in masters}
for b,n in list(keys):
    bank=engine.native.graphics_bank(engine.native.entry(arc,2),b);offset=bank['frames'][n]['offset']
    for f in bank['frames']:
        if f['offset']!=offset or(b,f['index'])in targets:continue
        k=(b,f['index']);keys[k]=(None,0,0);targets[k]=engine.native.render(arc,b,b*5,k[1])[0].copy()
engine.PARENT=P;engine.PARENT_SHA=PSHA;engine.OUT=OUT;engine.KEYS=keys;engine.CACHE=W/'riko/rising_pack_cache'
def expected(data):
    engine.native.need(engine.native.sha(data)==PSHA,'Wrong parent')
    return{k:v.copy()for k,v in targets.items()}
engine.get_targets=expected;original=engine.pack_frame
def pack(c,b,n,raw,count,target):
    if(b,n)not in masters:return raw,engine.records(c,b*5,n),dict(type='preserved_shared_support')
    return original(c,b,n,raw,count,target)
engine.pack_frame=pack;engine.native.packer.repack_raw=repack
out,proof=engine.build(arc,targets);again,_=engine.build(arc,targets);assert out==again
proof.pop('heads_preserved_pixels_per_reference',None)
OUT.mkdir();(OUT/'PL01_U.ARC').write_bytes(out);engine.KEYS={k:keys[k]for k in masters};engine.boards(arc,out)
report=dict(source_arc=str(P.relative_to(ROOT)),source_arc_sha256=PSHA,resource=str((OUT/'PL01_U.ARC').relative_to(ROOT)),after_sha256=engine.native.sha(out),target_references=[f'b{b}_{n:03}'for b,n in sorted(masters)],shared_support_refs=[f'b{b}_{n:03}'for b,n in keys if(b,n)not in masters],artwork=str(ART.relative_to(ROOT)),registration=reg,verification=proof,reproducible=True,runtime_verified=False,full_art_unification_complete=False)
(OUT/'proposal.json').write_text(json.dumps(report,indent=2)+'\n','utf8')
print(json.dumps({'after_sha256':report['after_sha256'],'targets':report['target_references'],'counts':proof['counts'],'layouts':proof['layouts']}))
