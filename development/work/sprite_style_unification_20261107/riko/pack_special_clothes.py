"""벽7 자세의 새 의상/부츠를 같은 파일과 기존 타일 버퍼에 등록한다."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[3];W=ROOT/'work/sprite_style_unification_20261107'
sys.path.insert(0,str(ROOT));sys.path.insert(0,str(W/'zero_audit'))
import pack_riko_cloth as engine
from lossless_stream_pack import repack
P=W/'riko/prepared_dash_clothes_v1/PL01_U.ARC';PSHA='93844db97721cc95c89ece5a81eb48d9135f1e0f2c5aafb172d2890b11bff1b5'
ART=W/'riko/special_clothes13/targets01';OUT=W/'riko/prepared_special_clothes_v1'
assert not OUT.exists();arc=P.read_bytes();assert engine.native.sha(arc)==PSHA
reg=json.loads((ART/'registration.json').read_text('utf8'));assert reg['source_sha256']==PSHA
masters={}
for r in reg['frames']:
    p=ROOT/r['target'];assert engine.native.sha(p.read_bytes())==r['target_sha256'];masters[r['bank'],r['ref']]=np.array(Image.open(p))
assert set(masters)=={(1,n)for n in [50,51,53,57,108,110,112,114,116,119,122,125,128,129]}
targets={k:v.copy()for k,v in masters.items()};keys={k:(k[1],0,0)for k in masters}
for b,n in list(keys):
    bank=engine.native.graphics_bank(engine.native.entry(arc,2),b);offset=bank['frames'][n]['offset']
    for f in bank['frames']:
        if f['offset']!=offset or(b,f['index'])in targets:continue
        k=(b,f['index']);keys[k]=(None,0,0);targets[k]=engine.native.render(arc,b,b*5,k[1])[0].copy()
engine.PARENT=P;engine.PARENT_SHA=PSHA;engine.OUT=OUT;engine.KEYS=keys;engine.CACHE=W/'riko/special_pack_cache'
def expected(data):
    engine.native.need(engine.native.sha(data)==PSHA,'Wrong parent')
    return{k:v.copy()for k,v in targets.items()}
engine.get_targets=expected;original=engine.pack_frame
g,c=engine.native.entry(arc,2),engine.native.entry(arc,3)
f=engine.native.graphics_bank(g,1)['frames'][128]
assert f['tile_count']==24
shared_raw=engine.native.decode_stream(g,f['offset'],f['limit'],24*128).data
protected_tiles=set()
for n in [130,131]:
    protected_tiles.update(p['tile']for p in engine.native.composition_frame(c,5,n)['parts'])
free_tiles=set(range(24))-protected_tiles
assert free_tiles=={2,3,4,6,7,8,9,10,11,12,15}
assert np.array_equal(masters[1,128],masters[1,129])
shared_new,shared_parts=engine.motion.identical(shared_raw,24,masters[1,128],free_tiles,10)
while len(shared_parts)<10:shared_parts.append(shared_parts[-1])
shared_records=b''.join(bytes([0,t,(x-160)&255,(y-160)&255])for t,x,y in shared_parts)
# The complete original 130/131 tile set remains byte-identical in the new shared atlas.
old_atlas=np.frombuffer(engine.native.indexed_atlas(shared_raw,24)[0],np.uint8).reshape(-1,256)
new_atlas=np.frombuffer(engine.native.indexed_atlas(shared_new,24)[0],np.uint8).reshape(-1,256)
for tile in protected_tiles:
    y,x=tile//16*16,tile%16*16
    assert np.array_equal(old_atlas[y:y+16,x:x+16],new_atlas[y:y+16,x:x+16])
def pack(c,b,n,raw,count,target):
    if b==1 and n in [128,129,130,131]:
        assert count==24 and raw==shared_raw
        rec=shared_records if n in [128,129]else engine.records(c,5,n)
        return shared_new,rec,dict(type='shared_identical_body_private_tiles',body_refs=[128,129],preserved_refs=[130,131],private_tiles=sorted(free_tiles),protected_tiles=sorted(protected_tiles))
    if(b,n)not in masters:return raw,engine.records(c,b*5,n),dict(type='preserved_shared_support')
    return original(c,b,n,raw,count,target)
engine.pack_frame=pack;engine.native.packer.repack_raw=repack
out,proof=engine.build(arc,targets);again,_=engine.build(arc,targets);assert out==again
proof.pop('heads_preserved_pixels_per_reference',None)
OUT.mkdir();(OUT/'PL01_U.ARC').write_bytes(out);engine.KEYS={k:keys[k]for k in masters};engine.boards(arc,out)
report=dict(source_arc=str(P.relative_to(ROOT)),source_arc_sha256=PSHA,resource=str((OUT/'PL01_U.ARC').relative_to(ROOT)),after_sha256=engine.native.sha(out),target_references=[f'b{b}_{n:03}'for b,n in sorted(masters)],shared_support_refs=[f'b{b}_{n:03}'for b,n in keys if(b,n)not in masters],artwork=str(ART.relative_to(ROOT)),registration=reg,verification=proof,reproducible=True,runtime_verified=False,full_art_unification_complete=False)
(OUT/'proposal.json').write_text(json.dumps(report,indent=2)+'\n','utf8')
print(json.dumps({'after_sha256':report['after_sha256'],'targets':report['target_references'],'counts':proof['counts'],'layouts':proof['layouts']}))
