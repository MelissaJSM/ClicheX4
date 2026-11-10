"""읽기 입력의 타일 전체를 순열 재배치하여 native압축량 조사. 도트 변경 없음."""
from pathlib import Path
import sys,json,argparse,random,itertools
import numpy as np
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
from src.psx_player import indexed_atlas
from src.psx_compress import encode_stream
from scripts.optimize_rin_style_tiles import permute,tile_slices

def optimize(raw,steps=0):
    fixed={0,10,16};move=sorted(set(range(32))-fixed);data={n:b''.join(raw[s]for s in tile_slices(32,n))for n in range(32)}
    at=np.frombuffer(indexed_atlas(raw,32)[0],np.uint8).reshape(32,256)
    boxes={}
    for n in range(32):
        y,x=np.nonzero(at[n//16*16:n//16*16+16,n%16*16:n%16*16+16]);boxes[n]=(0,0,0)if not len(x)else(int(y.max()+1),int(x.max()+1),len(x))
    identity=list(range(32));bestorder=identity;best=len(encode_stream(raw));initial=best;trials=0;cache={tuple(identity):best}
    def score(order):
        nonlocal trials
        key=tuple(order)
        if key not in cache:cache[key]=len(encode_stream(permute(raw,32,order)));trials+=1
        return cache[key]
    seeds=[]
    keys=[lambda n:boxes[n],lambda n:(boxes[n][1],boxes[n][0]),lambda n:(boxes[n][2],boxes[n][0]),lambda n:data[n],lambda n:data[n][::-1],lambda n:(boxes[n][0],data[n])]
    for key in keys:
        for rev in(False,True):
            order=identity.copy()
            for p,n in zip(move,sorted(move,key=key,reverse=rev)):order[p]=n
            seeds.append(order)
    for order in seeds:
        size=score(order)
        if size<best:best,bestorder=size,order
    progression=[best]
    for step in range(steps):
        winner=bestorder;value=best
        for x,y in itertools.combinations(move,2):
            if data[bestorder[x]]==data[bestorder[y]]:continue
            order=bestorder.copy();order[x],order[y]=order[y],order[x];size=score(order)
            if size<value:value,winner=size,order
        if value>=best:break
        best,bestorder=value,winner;progression.append(best)
    result=permute(raw,32,bestorder)
    need(sorted(b''.join(result[s]for s in tile_slices(32,n))for n in range(32))==sorted(data.values()),'Tile multiset changed')
    return result,{old:new for new,old in enumerate(bestorder)},{'before':initial,'after':best,'saved':initial-best,'order':bestorder,'fixed_tiles':sorted(fixed),'trials':trials,'progression':progression,'source_raw_sha256':sha(raw),'output_raw_sha256':sha(result),'all_tile_bytes_preserved':True}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--source',default='base_run_complete_pack04/progress.json');ap.add_argument('--output',required=True);ap.add_argument('--steps',type=int,default=0);ap.add_argument('--refs',default='');z=ap.parse_args();o=H/z.output;need(not o.exists(),'Fresh output required');o.mkdir();q=json.loads((H/z.source).read_text('utf8'));wanted=set(map(int,z.refs.split(',')))if z.refs else None;reports=[];result={}
    for group in q['groups']:
        n=group['refs'][0]
        if wanted is not None and n not in wanted:continue
        raw=bytes.fromhex(q['raws'][str(n)]);new,mapping,proof=optimize(raw,z.steps);proof['refs']=group['refs'];reports.append(proof)
        result[str(n)]={'raw':new.hex(),'mapping':mapping,'refs':group['refs']}
        write(o/'result.json',{'source_sha256':sha((H/z.source).read_bytes()),'groups':result,'reports':reports,'saved_total':sum(v['saved']for v in reports)})
        print(json.dumps({'refs':group['refs'],'before':proof['before'],'after':proof['after'],'saved':proof['saved']}),flush=True)
if __name__=='__main__':main()
