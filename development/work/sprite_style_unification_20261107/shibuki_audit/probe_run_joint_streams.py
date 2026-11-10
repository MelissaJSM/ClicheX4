"""서로 다른 두 이동/사격쌍을 하나의 32타일 raw로 무손실 공동 패킹."""
from pathlib import Path
import sys,json,struct,itertools,argparse,time
import numpy as np
from PIL import Image
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write,crop
from pack_run_patterns import candidates
from probe_air_body_capacity import put
PARTS=(0,5,6,7,8)

def pack(target,refs):
    raw=bytes(4096);used=set();heads=[];records={b:{}for b in PARTS}
    for n in refs:
        ar=target[n][5];r=next((r for v,r in heads if np.array_equal(ar,v)),None)
        if r is None:
            y,x=np.nonzero(ar);need(len(x)and x.max()-x.min()<16 and y.max()-y.min()<16,'Head overflow');t=10+len(heads);need(t<16,'Head count overflow');r=struct.pack('<BBbb',0,t,int(x.min()-160),int(y.min()-160));raw=put(raw,r,ar);heads.append((ar,r));used.add(t)
        records[5][n]=r
    direct=[(n,b)for n in refs for b in(7,8)];images=[crop(target[n][b])for n,b in direct];extras=[]
    for n in refs[::2]:
        for b in(0,6):
            left,right=target[n][b],target[n+1][b];same=(left==right)&(left>0)
            for name,ar in(('common',np.where(same,left,0)),('left',np.where(same,0,left)),('right',np.where(same,0,right))):
                if ar.any():extras.append((n,b,name));images.append(crop(ar.astype(np.uint8)))
    choices=candidates(raw,images,set(range(1,32))-used);size,nr,rr,mode=choices[0]
    def enc(v):return b''.join(struct.pack('<BBbb',fl,t,x-80,y-80)for t,x,y,fl in v)
    for(n,b),parts in zip(direct,rr):records[b][n]=enc(parts)
    pieces={k:enc(v)for k,v in zip(extras,rr[len(direct):])}
    for n in refs[::2]:
        for b in(0,6):records[b][n]=pieces.get((n,b,'left'),b'')+pieces.get((n,b,'common'),b'');records[b][n+1]=pieces.get((n,b,'common'),b'')+pieces.get((n,b,'right'),b'')
    need(all(0<len(r)//4<=24 for bank in records.values()for r in bank.values()),'Bad record count')
    return nr,records,{'refs':refs,'bytes':size,'mode':mode,'head_tiles':sorted(used),'parts':{str(b):{str(n):len(r)//4 for n,r in v.items()}for b,v in records.items()}}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--output',required=True);ap.add_argument('--max',type=int,default=120);z=ap.parse_args();out=H/z.output;need(not out.exists(),'Fresh output');out.mkdir();d=H/'base_run_complete_targets01';target={n:{b:np.array(Image.open(d/f'{n:03}_bank{b}_indices.png'))for b in PARTS}for n in range(1,33)}
    old=json.loads((H/'base_run_complete_pack04/progress.json').read_text('utf8'));scores={g['refs'][0]:g['new']for g in old['compressed_group_sizes']};pairs=sorted(itertools.combinations(range(1,33,2),2),key=lambda v:(scores[v[0]]+scores[v[1]],v));rows=[];success=[]
    for left,right in pairs[:z.max]:
        refs=[left,left+1,right,right+1]
        try:
            raw,records,proof=pack(target,refs);proof['old_bytes']=scores[left]+scores[right];proof['saved']=proof['old_bytes']-proof['bytes'];proof['passed']=True
            (out/f'{left:03}_{right:03}.bin').write_bytes(raw);write(out/f'{left:03}_{right:03}.json',{'proof':proof,'records':{str(b):{str(n):r.hex()for n,r in v.items()}for b,v in records.items()},'raw_sha256':sha(raw)});success.append(proof);print(json.dumps(proof),flush=True)
        except ValueError as ex:proof={'refs':refs,'passed':False,'reason':str(ex)}
        rows.append(proof);write(out/'report.json',{'attempts':rows,'successes':success,'target_lock_sha256':sha((d/'LOCK.json').read_bytes()),'resource_written':False})
    print(json.dumps({'attempts':len(rows),'successes':len(success)}),flush=True)
if __name__=='__main__':main()
