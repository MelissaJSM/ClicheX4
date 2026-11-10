"""공통층 분리를 필요한 쌍에만 쓰는 정확표시 저장 후보 조사."""
from pathlib import Path
import sys,json,struct,argparse,itertools
import numpy as np
from PIL import Image
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write,crop
from probe_air_body_capacity import put
from pack_run_patterns import candidates
from scripts.export_x_consistency import Archive
from scripts.prepare_shibuki_ultimate_production import repack_parts
from repack_part_records_lossless import repack as repack_global

def pack_pair(refs,target,common_banks,alpha_common=False):
    raw=bytes(4096);used=set();headcache=[];parts={b:{}for b in(0,5,6,7,8)}
    for n in refs:
        ar=target[n][5];found=next((r for im,r in headcache if np.array_equal(im,ar)),None)
        if found is None:
            y,x=np.nonzero(ar);need(len(x)>0 and x.max()-x.min()<16 and y.max()-y.min()<16,'Head tile limit')
            tile=10+len(headcache);found=struct.pack('<BBbb',0,tile,int(x.min()-160),int(y.min()-160));raw=put(raw,found,ar);headcache.append((ar,found));used.add(tile)
        parts[5][n]=found
    order=[(n,b)for n in refs for b in(0,6,7,8)if b not in common_banks];images=[crop(target[n][b])for n,b in order];bodykeys=[]
    for bank in common_banks:
        left,right=(target[n][bank]for n in refs)
        same=((left>0)&(right>0)) if alpha_common else ((left==right)&(left>0))
        common=np.where(same,left,0).astype(np.uint8)
        delta=[np.where(same,0,left).astype(np.uint8),np.where(same&(left==right),0,right).astype(np.uint8)]
        for name,ar in(('common',common),('left',delta[0]),('right',delta[1])):
            if ar.any():bodykeys.append((bank,name));images.append(crop(ar))
    opts=candidates(raw,images,set(range(1,32))-used);size,nr,rr,mode=opts[0]
    def enc(rs):return b''.join(struct.pack('<BBbb',fl,t,x-80,y-80)for t,x,y,fl in rs)
    for (n,b),rs in zip(order,rr):parts[b][n]=enc(rs)
    pieces={k:enc(rs)for k,rs in zip(bodykeys,rr[len(order):])}
    for b in common_banks:
        parts[b][refs[0]]=pieces.get((b,'left'),b'')+pieces.get((b,'common'),b'')
        parts[b][refs[1]]=pieces.get((b,'common'),b'')+pieces.get((b,'right'),b'')
    return {'refs':list(refs),'bytes':size,'raw':nr.hex(),'parts':{str(b):{str(n):v.hex()for n,v in p.items()}for b,p in parts.items()},'mode':mode,'common_banks':list(common_banks),'alpha_common':alpha_common}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--output',required=True);ap.add_argument('--alpha-common',action='store_true');z=ap.parse_args();out=H/z.output;need(not out.exists(),'Fresh output');out.mkdir();d=H/'base_run_complete_targets01'
    target={n:{b:np.array(Image.open(d/f'{n:03}_bank{b}_indices.png'))for b in(0,5,6,7,8)}for n in range(1,33)};rows=[]
    for n in range(1,33,2):
        opts=[]
        for common in((),(0,),(6,),(0,6)):
            try:r=pack_pair((n,n+1),target,common,z.alpha_common);r['passed']=True
            except ValueError as e:r={'refs':[n,n+1],'passed':False,'common_banks':list(common),'error':str(e)}
            opts.append(r)
        rows.append({'refs':[n,n+1],'options':opts});write(out/'result.json',{'analysis_only':True,'resource_written':False,'target_lock_sha256':sha((d/'LOCK.json').read_bytes()),'groups':rows})
        print(json.dumps({'refs':[n,n+1],'options':[{k:v for k,v in r.items()if k not in('raw','parts')}for r in opts]}),flush=True)

if __name__=='__main__':main()
