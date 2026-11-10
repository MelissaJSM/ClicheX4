"""Pack local boot material detail, preserving silhouettes, contacts and shared effects."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[3];W=ROOT/'work/sprite_style_unification_20261107'
sys.path.insert(0,str(ROOT));sys.path.insert(0,str(W/'zero_audit'))
import pack_riko_cloth as engine
from lossless_stream_pack import repack
P=W/'riko/prepared_ground_boots_v4/PL01_U.ARC';PSHA='540658ec80aa24415d1df97e37dac0c1a28898907cc8778ba5fa037224e87eb2'
ART=W/'riko/ground_remaining22/targets02';OUT=W/'riko/prepared_ground_boots_v13'
assert not OUT.exists();arc=P.read_bytes();assert engine.native.sha(arc)==PSHA
reg=json.loads((ART/'registration.json').read_text('utf8'));assert reg['source_sha256']==PSHA
masters={}
for r in reg['frames']:
    p=ROOT/r['target'];assert engine.native.sha(p.read_bytes())==r['target_sha256'];masters[r['bank'],r['ref']]=np.array(Image.open(p))
assert set(masters)=={(0,n)for n in (83,85,87,89,105,107,109,130,131,132,155,156,158,160,162)} | {(1,n)for n in (87,91,93,95,96,98,99,101,103,105,107,130,131)}
targets={k:v.copy()for k,v in masters.items()};keys={(r["bank"],r["ref"]):(r["art_key"][1],*r["native_translation"])for r in reg["frames"]}
for b,n in list(keys):
    bank=engine.native.graphics_bank(engine.native.entry(arc,2),b);offset=bank['frames'][n]['offset']
    for f in bank['frames']:
        if f['offset']!=offset or(b,f['index'])in targets:continue
        k=(b,f['index']);keys[k]=(None,0,0);targets[k]=engine.native.render(arc,b,b*5,k[1])[0].copy()
engine.PARENT=P;engine.PARENT_SHA=PSHA;engine.OUT=OUT;engine.KEYS=keys;engine.CACHE=W/'riko/ground_boots_pack_cache'
def expected(data):
    engine.native.need(engine.native.sha(data)==PSHA,'Wrong parent')
    return{k:v.copy()for k,v in targets.items()}
engine.get_targets=expected;original=engine.pack_frame
layout=json.loads((W/'riko/boot_stream_layout.json').read_text('utf8'))
assert layout['parent_sha256']==PSHA

def pack(c,b,n,raw,count,target):
    if b==1 and n in layout['proof']['frames']:
        assert engine.native.sha(raw)==layout['proof']['raw_before_sha256']
        return bytes.fromhex(layout['raw']),bytes.fromhex(layout['records'][str(n)]),layout['proof']
    if(b,n)not in masters:return raw,engine.records(c,b*5,n),dict(type='preserved_shared_support')
    return original(c,b,n,raw,count,target)
engine.pack_frame=pack;engine.native.packer.repack_raw=repack
out,proof=engine.build(arc,targets);again,_=engine.build(arc,targets);assert out==again
proof.pop('heads_preserved_pixels_per_reference',None)
OUT.mkdir();(OUT/'PL01_U.ARC').write_bytes(out);engine.KEYS={k:keys[k]for k in masters};engine.boards(arc,out)
report=dict(source_arc=str(P.relative_to(ROOT)),source_arc_sha256=PSHA,resource=str((OUT/'PL01_U.ARC').relative_to(ROOT)),after_sha256=engine.native.sha(out),target_references=[f'b{b}_{n:03}'for b,n in sorted(masters)],shared_support_refs=[f'b{b}_{n:03}'for b,n in keys if(b,n)not in masters],artwork=str(ART.relative_to(ROOT)),registration=reg,verification=proof,reproducible=True,runtime_verified=False,full_art_unification_complete=False)
(OUT/'proposal.json').write_text(json.dumps(report,indent=2)+'\n','utf8')
print(json.dumps({'after_sha256':report['after_sha256'],'targets':report['target_references'],'counts':proof['counts'],'layouts':proof['layouts']}))
