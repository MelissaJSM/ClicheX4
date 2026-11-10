from storage_common import *
import random
from concurrent.futures import ProcessPoolExecutor,as_completed
a=Path(__file__).parent/'production03'
def run(n):
    art,q,r,desc,packed,assignments,targets,writable=load(a,n)
    best=encoded_cost(packed);start=best;chosen=[]
    atlas,positions,_=indexed_atlas(packed,desc['tile_count']);options=[]
    for t in writable:
        for y in range(16):
            for x in range(16):
                idx=(t//16*16+y)*256+t%16*16+x
                if atlas[idx]:continue
                values=[]
                for num,parts in assignments.items():
                    for tile,left,top,flag in parts:
                        if tile==t:
                            px=left+(15-x if flag&64 else x);py=top+(15-y if flag&128 else y)
                            values.append(int(targets[num][py,px]) if 0<=py<160 and 0<=px<160 else 0)
                if not values or len(set(values))!=1 or not values[0]:continue
                change=[t,x,y,values[0]]
                try:fill_redundant_pixels(packed,desc['tile_count'],assignments,targets,[change],writable)
                except ValueError:continue
                off,shift=positions[idx];options.append((change,off,shift))
    current=bytearray(packed);rng=random.Random(2900+n)
    coverage={};all_keys={}
    for num,parts in assignments.items():
        for tile,left,top,flag in parts:
            for y in range(16):
                for x in range(16):
                    px=left+(15-x if flag&64 else x);py=top+(15-y if flag&128 else y)
                    if not 0<=px<160 or not 0<=py<160:continue
                    key=(tile,x,y);coverage.setdefault((num,py,px),[]).append(key);all_keys.setdefault(key,[]).append((num,py,px))
    def address(key):
        t,x,y=key;return positions[(t//16*16+y)*256+t%16*16+x]
    def value(data,key):
        off,shift=address(key);return (data[off]>>shift)&15
    def put(data,key,v):
        off,shift=address(key);data[off]=(data[off]&~(15<<shift))|(v<<shift)
    def differences(data):
        return [[*key,value(data,key)] for key in all_keys if value(data,key)!=value(packed,key)]
    for step in range(120):
        if best<=r['budget']:break
        scores=[]
        for key,uses in all_keys.items():
            if key[0] not in writable:continue
            vs={int(targets[num][py,px]) for num,py,px in uses}
            if len(vs)!=1 or 0 in vs:continue
            wanted=vs.pop();owners=set()
            for location in uses:
                owners.update(k for k in coverage[location] if value(current,k))
            owners.discard(key)
            if not owners or any(k[0] not in writable for k in owners):continue
            trial=current.copy()
            for k in owners:put(trial,k,0)
            put(trial,key,wanted);cost=encoded_cost(bytes(trial))
            if cost>best:continue
            scores.append((cost,rng.random(),trial))
        accepted=False
        for cost,_,trial in sorted(scores,key=lambda q:q[:2]):
            changes=differences(trial)
            try:proof=fill_redundant_pixels(packed,desc['tile_count'],assignments,targets,changes,writable)
            except ValueError:continue
            assert proof==bytes(trial)
            current=trial;best=cost;accepted=True;break
        if not accepted:break
    chosen=differences(current)
    assert bytes(current)==fill_redundant_pixels(packed,desc['tile_count'],assignments,targets,chosen,writable)
    r.update(encoded_bytes=best,fits=best<=r['budget'],overlap_fill=chosen);(a/f'packing_{n:03}.json').write_text(json.dumps(r,indent=2))
    return {'frame':n,'start':start,'final':best,'budget':r['budget'],'fill_pixels':len(chosen),'fits':r['fits']}
if __name__=='__main__':
 ns=list(map(int,sys.argv[1:]))
 if not ns:ns=[q['frame'] for q in json.loads((a/'art.json').read_text())['groups'] if q['kind'] not in ('effect',) and not json.loads((a/f"packing_{q['frame']:03}.json").read_text())['fits']]
 with ProcessPoolExecutor(max_workers=3) as pool:
  jobs={pool.submit(run,n):n for n in ns}
  for f in as_completed(jobs):
   try:print(f.result(),flush=True)
   except Exception as e:print({'frame':jobs[f],'error':repr(e)},flush=True)
