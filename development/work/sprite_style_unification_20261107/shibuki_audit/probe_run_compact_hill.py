"""변환 완료 타일 두 개의 저장 순서만 바꾸는 무손실 국소 탐색."""
from pathlib import Path
import sys,json,struct,argparse,itertools
import numpy as np
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,write,sha
from src.psx_player import indexed_atlas
from src.psx_compress import encode_stream
from probe_run_compact_flip import packed
from probe_run_occluded_tile_union import decode_parts,render

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--output',required=True);ap.add_argument('--refs',required=True);ap.add_argument('--steps',type=int,default=2);z=ap.parse_args();out=H/z.output;need(not out.exists(),'Fresh output');out.mkdir();wanted=set(map(int,z.refs.split(',')))
    a=json.loads((H/'base_run_compact_flip01/result.json').read_text('utf8'));b=json.loads((H/'base_run_alpha_compact_flip01/result.json').read_text('utf8'));chosen=[min((v,w),key=lambda t:t['after'])for v,w in zip(a['groups'],b['groups'])];chosen[0]=json.loads((H/'base_run_idle_alias02/result.json').read_text('utf8'))['shot2'];results=[]
    for v in chosen:
        n=v['refs'][0]
        if n not in wanted:continue
        count=v['count'];raw=bytes.fromhex(v['raw']);at=np.frombuffer(indexed_atlas(raw,count)[0],np.uint8).reshape(-1,256);tiles=[at[t//16*16:t//16*16+16,t%16*16:t%16*16+16].copy()for t in range(count)];parts={(int(b),int(f)):decode_parts(h)for b,fs in v['parts'].items()for f,h in fs.items()};heads={r[1]for(b,f),rr in parts.items()if b==5 for r in rr};move=sorted(set(range(count))-{0,16}-heads);order=list(range(count));initial=len(encode_stream(raw));best=initial;trials=0;history=[];cache={tuple(order):best}
        for step in range(z.steps):
            winner=None;cost=best
            for x,y in itertools.combinations(move,2):
                if np.array_equal(tiles[order[x]],tiles[order[y]]):continue
                oo=order.copy();oo[x],oo[y]=oo[y],oo[x];k=tuple(oo)
                if k not in cache:cache[k]=len(encode_stream(packed([tiles[i]for i in oo],count)));trials+=1
                if cache[k]<cost:cost=cache[k];winner=oo
            if winner is None:break
            best=cost;order=winner;history.append(best)
            print(json.dumps({'refs':v['refs'],'step':step,'initial':initial,'bytes':best,'saved':initial-best,'trials':trials}),flush=True)
        mapping={old:new for new,old in enumerate(order)};nt=[tiles[i]for i in order];np_={k:[[fl,mapping[t],x,y]for fl,t,x,y in rr]for k,rr in parts.items()}
        expanded=tiles+[np.zeros((16,16),np.uint8)for _ in range(32-count)];newexp=nt+[np.zeros((16,16),np.uint8)for _ in range(32-count)]
        for k in parts:need(np.array_equal(render(expanded,parts[k]),render(newexp,np_[k])),'Hill display differs')
        proof={'refs':v['refs'],'count':count,'before':initial,'after':best,'saved':initial-best,'trials':trials,'history':history,'order':order,'raw':packed(nt,count).hex(),'parts':{str(b):{str(f):b''.join(struct.pack('<BBbb',*r)for r in rr).hex()for(bb,f),rr in np_.items()if bb==b}for b in(0,5,6,7,8)},'exact_layers':len(parts)};results.append(proof);write(out/'result.json',{'analysis_only':True,'resource_written':False,'groups':results,'saved':sum(v['saved']for v in results)})
        print(json.dumps({'finished_refs':v['refs'],'saved':initial-best,'after':best}),flush=True)
if __name__=='__main__':main()
