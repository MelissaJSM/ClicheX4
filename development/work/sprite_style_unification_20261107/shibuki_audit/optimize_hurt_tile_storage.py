"""시부키 피격 후보의 전체 타일 순서만 무손실 재배치한다."""
import itertools,sys
from pathlib import Path
import numpy as np
from src.psx_compress import encode_stream
from src.psx_player import indexed_atlas
from scripts.optimize_rin_style_tiles import permute,tile_slices
from native_pose_pack import need,sha
sys.path.insert(0,str(Path(__file__).resolve().parents[3]/'work/tools'))
from psx_compress_cost import encoded_cost

def optimize(raw,fixed,steps=2):
    fixed=set(fixed)|{0,16};move=sorted(set(range(32))-fixed)
    data={n:b''.join(raw[s]for s in tile_slices(32,n))for n in range(32)}
    at=np.frombuffer(indexed_atlas(raw,32)[0],np.uint8).reshape(32,256);boxes={}
    for n in range(32):
        y,x=np.nonzero(at[n//16*16:n//16*16+16,n%16*16:n%16*16+16]);boxes[n]=(0,0,0)if not len(x)else(int(y.max()+1),int(x.max()+1),len(x))
    identity=list(range(32));order=identity;best=len(encode_stream(raw));initial=best;cache={tuple(identity):best}
    def score(seq):
        key=tuple(seq)
        if key not in cache:cache[key]=encoded_cost(permute(raw,32,seq))
        return cache[key]
    keys=[lambda n:boxes[n],lambda n:(boxes[n][1],boxes[n][0]),lambda n:(boxes[n][2],boxes[n][0]),lambda n:data[n],lambda n:data[n][::-1],lambda n:(boxes[n][0],data[n])]
    for key in keys:
        for reverse in(False,True):
            seq=identity.copy()
            for p,n in zip(move,sorted(move,key=key,reverse=reverse)):seq[p]=n
            size=score(seq)
            if size<best:best,order=size,seq
    progression=[best]
    for _ in range(steps):
        value,winner=best,order
        for x,y in itertools.combinations(move,2):
            if data[order[x]]==data[order[y]]:continue
            seq=order.copy();seq[x],seq[y]=seq[y],seq[x];size=score(seq)
            if size<value:value,winner=size,seq
        if value>=best:break
        best,order=value,winner;progression.append(best)
    result=permute(raw,32,order);mapping={old:new for new,old in enumerate(order)}
    need(len(encode_stream(result))==best,'Native encoder cost differs')
    need(all(mapping[t]==t for t in fixed),'Fixed original tile moved')
    need(sorted(b''.join(result[s]for s in tile_slices(32,n))for n in range(32))==sorted(data.values()),'Tile bytes changed')
    return result,mapping,{'before':initial,'after':best,'saved':initial-best,'order':order,'fixed_tiles':sorted(fixed),'trials':len(cache),'progression':progression,'source_raw_sha256':sha(raw),'output_raw_sha256':sha(result),'all_tile_bytes_preserved':True}
