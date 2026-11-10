"""Lossless tile permutation for the standalone shared body91/93 stream.

All tile bytes survive; records follow the permutation. No raster editing,
support changes, tile-count changes, or bank-boundary changes are permitted.
"""
from pathlib import Path
import json, hashlib, itertools
import numpy as np
from src.psx_compress import encode_stream
from src.psx_player import indexed_atlas, composition_frame, compose_indices
from scripts.prepare_shibuki_ultimate_production import records

CACHE = Path(__file__).resolve().parent / 'boot_tile_translate105.json'
sha = lambda b: hashlib.sha256(b).hexdigest()

def optimize(c, raw, count, targets, edit_visible_set):
    assert count == 26
    edits = []
    for n in (105, 106, 107):
        cp = composition_frame(c, 5, n)
        _, size, bb, _ = compose_indices(raw, count, cp)
        target = targets[1, n][160+bb[1]:160+bb[3], 160+bb[0]:160+bb[2]]
        edits.append((cp, target.tobytes(), size))
    joint = edit_visible_set(raw, count, edits)
    key = sha(joint + records(c,5,105) + records(c,5,106) + records(c,5,107))
    if CACHE.exists():
        v = json.loads(CACHE.read_text('utf8'))
        if v['key'] == key:
            return bytes.fromhex(v['raw']), {int(n):bytes.fromhex(r) for n,r in v['records'].items()},v['proof']
    atlas, locations, _ = indexed_atlas(joint,count)
    atlas = np.frombuffer(atlas,np.uint8).reshape(-1,256)
    tiles = {t:atlas[t//16*16:t//16*16+16,t%16*16:t%16*16+16].copy() for t in range(count)}
    before_size = len(encode_stream(joint))
    attempts = []
    chosen = None
    # Hardware boundary tiles0/16 stay byte-identical, including transparency.
    consumed={p["tile"]for n in(105,107)for p in composition_frame(c,5,n)["parts"]}-{p["tile"]for p in composition_frame(c,5,106)["parts"]}
    for a in sorted(consumed-{0,16}):
        yy,xx=np.nonzero(tiles[a])
        if not len(xx):continue
        for dx,dy in [(1,0),(-1,0),(2,0),(-2,0),(0,1),(0,-1),(1,1),(-1,1),(1,-1),(-1,-1)]:
            if xx.min()+dx<0 or xx.max()+dx>=16 or yy.min()+dy<0 or yy.max()+dy>=16:continue
            result=bytearray(joint);patch=np.zeros((16,16),np.uint8);patch[yy+dy,xx+dx]=tiles[a][yy,xx]
            for y in range(16):
                for x in range(16):
                    pos,shift=locations[(a//16*16+y)*256+a%16*16+x]
                    result[pos]=(result[pos]&~(15<<shift))|int(patch[y,x])<<shift
            result=bytes(result);size=len(encode_stream(result))
            attempts.append({'tile':a,'translation':[dx,dy],'bytes':size})
            if size<=before_size-4:
                chosen=(a,dx,dy,result,size,patch)
                break
        if chosen is not None:break
    assert chosen is not None, 'No sufficient lossless tile permutation found'
    a,dx,dy,result,size,patch=chosen
    rr={}
    for n in(105,106,107):
        rec=bytearray(records(c,5,n))
        for i in range(0,len(rec),4):
            if rec[i+1]==a:
                x=rec[i+2] if rec[i+2]<128 else rec[i+2]-256
                y=rec[i+3] if rec[i+3]<128 else rec[i+3]-256
                x+=dx if rec[i]&64 else -dx
                y+=dy if rec[i]&128 else -dy
                assert -128<=x<128 and -128<=y<128
                rec[i+2]=x&255;rec[i+3]=y&255
        rr[n]=bytes(rec)
    proof={'type':'lossless_tile_translation','tile':a,'translation':[dx,dy],
           'code_before':before_size,'code_after':size,'saved_bytes':before_size-size,
           'tile_values_permuted_only':True,'boundary_tiles_exact':[0,16],
           'body_stream_consumers':[105,106,107], 'support106_consumed_tiles_exact':True,'unconsumed_tiles_byte_exact':True,'attempts':attempts}
    after=np.frombuffer(indexed_atlas(result,count)[0],np.uint8).reshape(-1,256)
    aftertiles=[after[t//16*16:t//16*16+16,t%16*16:t%16*16+16].tobytes() for t in range(count)]
    assert aftertiles[a]==patch.tobytes()
    assert all(aftertiles[t]==tiles[t].tobytes() for t in range(count) if t!=a)
    CACHE.write_text(json.dumps({'key':key,'raw':result.hex(),
        'records':{str(n):r.hex() for n,r in rr.items()},'proof':proof},indent=2)+'\n','utf8')
    return result,rr,proof
