"""공통 낙봉파 몸체와 두 망토 변형을 공유 타일로 등록한다."""
from pathlib import Path
import json,sys,struct
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[3];W=ROOT/'work/sprite_style_unification_20261107';Z=W/'zero_audit'
sys.path.insert(0,str(ROOT));sys.path.insert(0,str(Z))
import pack_riko_cloth as engine
from src.psx_player import indexed_atlas
P=W/'riko/prepared_ceremony_v2/PL01_U.ARC';PSHA='590ed75799910795db7f237688bbd10ef3a282a7d12910956d798f497e67f818'
D=W/'riko/burst_cape_variants01/native02';OUT=W/'riko/prepared_burst_variants_v1'
assert not OUT.exists();arc=P.read_bytes();assert engine.native.sha(arc)==PSHA
reg=json.loads((D/'registration.json').read_text('utf8'));targets={}
for r in reg['frames']:
    p=ROOT/r['target'];assert engine.native.sha(p.read_bytes())==r['sha256']
    targets[1,r['ref']]=np.array(Image.open(p))
targets[1,184]=targets[1,182].copy();targets[1,183]=engine.native.render(arc,1,5,183)[0]
g,c=engine.native.entry(arc,2),engine.native.entry(arc,3);bank=engine.native.graphics_bank(g,1)
coords=list(dict.fromkeys((p['x']+160,p['y']+160) for p in engine.native.composition_frame(c,5,183)['parts']))
assert len(coords)==7
packed={};records={};details=[]
for group in ((182,183),(184,185)):
    f=bank['frames'][group[0]];count=f['tile_count'];raw=engine.native.decode_stream(g,f['offset'],f['limit'],count*128).data
    assert bank['frames'][group[1]]['offset']==f['offset']
    _,locations,_=indexed_atlas(raw,count);out=bytearray(raw);tiles={};next_tile=1
    from scipy.optimize import linear_sum_assignment
    patterns=list(dict.fromkeys(targets[1,n][y:y+16,x:x+16].tobytes() for n in group for x,y in coords))
    available=list(range(1,16))
    previous=np.frombuffer(indexed_atlas(raw,count)[0],np.uint8).reshape(-1,256)
    costs=np.array([[np.count_nonzero(np.frombuffer(pattern,np.uint8).reshape(16,16)!=previous[:16,t*16:(t+1)*16]) for t in available] for pattern in patterns])
    rows,cols=linear_sum_assignment(costs)
    chosen={patterns[r]:available[col] for r,col in zip(rows,cols)}
    for n in group:
        rec=[]
        for x,y in coords:
            pixels=targets[1,n][y:y+16,x:x+16];key=pixels.tobytes()
            if key not in tiles:
                assert next_tile<16
                tile=chosen[key];next_tile+=1;tiles[key]=tile
                for yy in range(16):
                    for xx in range(16):
                        pos,shift=locations[yy*256+tile*16+xx]
                        out[pos]=(out[pos]&~(15<<shift))|(int(pixels[yy,xx])<<shift)
            rec.append((tiles[key],x,y))
        count_parts=len(engine.native.composition_frame(c,5,n)['parts'])
        while len(rec)<count_parts:rec.append(rec[-1])
        records[n]=b''.join(bytes([0,t,(x-160)&255,(y-160)&255])for t,x,y in rec)
    for n in group:packed[n]=bytes(out)
    details.append({'refs':group,'tiles_used':next_tile-1,'original_tile_count':count,'hidden_cleanup':False,'original_shared_raw_preserved':True})
engine.PARENT=P;engine.PARENT_SHA=PSHA;engine.OUT=OUT
engine.KEYS={k:(k[1],0,0) for k in targets}
def expected(data):
    engine.native.need(engine.native.sha(data)==PSHA,'Wrong parent')
    return {k:v.copy()for k,v in targets.items()}
def pack(c,b,n,raw,count,target):
    assert b==1 and n in packed
    return packed[n],records[n],{'type':'shared_native_body_and_cape_tiles'}
engine.get_targets=expected;engine.pack_frame=pack
original_repack=engine.native.packer.repack_raw
def checked_repack(g,b,raws):
    from src.psx_compress import encode_stream
    if b==1:
        bank=engine.native.graphics_bank(g,b);seen={};before={}
        for f in bank['frames']:
            d=engine.native.decode_stream(g,f['offset'],f['limit'],f['tile_count']*128)
            raw=raws.get(f['index'],d.data);key=(f['offset'],engine.native.sha(raw))
            if key not in seen:seen[key]=len(encode_stream(raw)) if raw!=d.data else d.end-f['offset']
            before[f['offset']]=d.end-f['offset']
        budget=bank['end']-bank['base']-4*len(bank['frames'])
        print(json.dumps({'capacity':budget,'old_bytes':sum(before.values()),'new_bytes':sum(seen.values()),'excess':sum(seen.values())-budget}),flush=True)
    return original_repack(g,b,raws)
engine.native.packer.repack_raw=checked_repack
out,proof=engine.build(arc,targets);again,_=engine.build(arc,targets);assert out==again
assert np.array_equal(engine.native.render(out,1,5,183)[0],targets[1,183])
OUT.mkdir();(OUT/'PL01_U.ARC').write_bytes(out);engine.boards(arc,out)
report={'source_arc':str(P.relative_to(ROOT)),'source_arc_sha256':PSHA,'resource':str((OUT/'PL01_U.ARC').relative_to(ROOT)),
    'after_sha256':engine.native.sha(out),'new_art_refs':[182,184,185],'support_ref_183_display_exact':True,
    'verification':proof,'shared_groups':details,'reproducible':True,'cumulative_ref_count':80,
    'static_sync_pending':True,'not_ready_for_disc':True,'gameplay_runtime_verified':False}
(OUT/'proposal.json').write_text(json.dumps(report,indent=2)+'\n','utf8')
print(json.dumps({'after_sha256':report['after_sha256'],'counts':proof['counts'],'layouts':proof['layouts']}))
