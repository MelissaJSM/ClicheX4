"""대상32 안의 대체2참조 atlas 공유를 조사한다. ARC는 쓰지 않는다."""
from pathlib import Path
import sys,json,struct,argparse,itertools
import numpy as np
from PIL import Image
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write,crop
from probe_air_body_capacity import put
from pack_run_patterns import candidates
from src.psx_compress import encode_stream

def pack_pair(refs,target):
    raw=bytes(4096);used=set();headcache=[];parts={b:{}for b in(0,5,6,7,8)}
    for n in refs:
        ar=target[n][5];found=next((r for im,r in headcache if np.array_equal(im,ar)),None)
        if found is None:
            y,x=np.nonzero(ar);need(len(x)>0 and x.max()-x.min()<16 and y.max()-y.min()<16,'Head tile limit')
            tile=10+len(headcache);found=struct.pack('<BBbb',0,tile,int(x.min()-160),int(y.min()-160));raw=put(raw,found,ar);headcache.append((ar,found));used.add(tile)
        parts[5][n]=found
    order=[(n,b)for n in refs for b in(7,8)];images=[crop(target[n][b])for n,b in order];bodykeys=[]
    for bank in(0,6):
        left,right=(target[n][bank]for n in refs);same=(left==right)&(left>0);common=np.where(same,left,0).astype(np.uint8);delta=[np.where(same,0,v).astype(np.uint8)for v in(left,right)]
        for name,ar in(('common',common),('left',delta[0]),('right',delta[1])):
            if ar.any():bodykeys.append((bank,name));images.append(crop(ar))
    opts=candidates(raw,images,set(range(1,32))-used);size,nr,rr,mode=opts[0]
    def enc(rs):return b''.join(struct.pack('<BBbb',fl,t,x-80,y-80)for t,x,y,fl in rs)
    for (n,b),rs in zip(order,rr):parts[b][n]=enc(rs)
    pieces={k:enc(rs)for k,rs in zip(bodykeys,rr[len(order):])}
    for b in(0,6):
        parts[b][refs[0]]=pieces.get((b,'left'),b'')+pieces.get((b,'common'),b'')
        parts[b][refs[1]]=pieces.get((b,'common'),b'')+pieces.get((b,'right'),b'')
    return {'refs':list(refs),'bytes':size,'raw':nr.hex(),'parts':{str(b):{str(n):v.hex()for n,v in p.items()}for b,p in parts.items()},'mode':mode}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--output',required=True);ap.add_argument('--nearest',type=int,default=3);ap.add_argument('--refs',default='');z=ap.parse_args();out=H/z.output;need(not out.exists(),'Fresh output');out.mkdir()
    d=H/'base_run_complete_targets01';target={n:{b:np.array(Image.open(d/f'{n:03}_bank{b}_indices.png'))for b in(0,5,6,7,8)}for n in range(1,33)}
    pairset=set();scores=[]
    for i,j in itertools.combinations(range(1,33),2):
        mismatch=sum(int(np.count_nonzero(target[i][b]!=target[j][b]))for b in(0,5,6,7,8));scores.append((mismatch,i,j))
    for n in range(1,33):
        nearest=sorted(v for v in scores if n in v[1:])[:z.nearest]
        pairset.update((v[1],v[2])for v in nearest)
    pairset.update((n,n+2)for n in range(1,31))
    pairset={p for p in pairset if p!=(p[0]//2*2+1,p[0]//2*2+2) and p[1]!=p[0]+1 or p[0]%2==0}
    if z.refs:pairset={tuple(map(int,v.split(',')))for v in z.refs.split(';')}
    reports=[]
    for refs in sorted(pairset):
        try:r=pack_pair(refs,target);r['passed']=True
        except ValueError as e:r={'refs':list(refs),'passed':False,'error':str(e)}
        reports.append(r);write(out/'result.json',{'analysis_only':True,'resource_written':False,'target_lock_sha256':sha((d/'LOCK.json').read_bytes()),'pairs':reports})
        print(json.dumps({k:v for k,v in r.items()if k not in('raw','parts')}),flush=True)

if __name__=='__main__':main()
