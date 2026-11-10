"""사용 타일의 물리 정렬·완전 좌우반전·업로드 정원 축소를 읽기 시험."""
from pathlib import Path
import sys,json,struct,argparse
import numpy as np
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
from src.psx_compress import encode_stream
from src.psx_player import indexed_atlas
from probe_run_occluded_tile_union import tiles_of,render,decode_parts
from PIL import Image

def packed(tiles,count):
    chunks=[]
    for band in range((count+15)//16):
        row=np.concatenate(tiles[band*16:min(count,(band+1)*16)],axis=1)
        chunks.append((row[:,::2]|(row[:,1::2]<<4)).tobytes())
    return b''.join(chunks)
def optimize(raw,parts,flip_steps,min_count=0):
    tt=tiles_of(raw);used={r[1]for rr in parts.values()for r in rr};need(0 not in used,'Used zero sentinel');heads={r[1]for(b,n),rr in parts.items()if b==5 for r in rr};fixed={0}|heads
    shape={}
    for n in used:
        y,x=np.nonzero(tt[n]);shape[n]=(int(y.max()+1),int(x.max()+1),len(x))if len(x)else(0,0,0)
    move=sorted(used-heads);data={t:tt[t].tobytes()for t in move};best=None;trials=0
    keys=[lambda t:shape[t],lambda t:(shape[t][1],shape[t][0]),lambda t:(shape[t][2],shape[t][0]),lambda t:data[t],lambda t:data[t][::-1],lambda t:(shape[t][0],data[t])]
    for count in range(max(max(fixed)+1,len(used)+1,min_count),33):
        slots=sorted(set(range(1,count))-heads)
        for key in keys:
            for rev in(False,True):
                order=sorted(move,key=key,reverse=rev);mapping={h:h for h in heads};chosen=[];available=order.copy()
                for pos in slots:
                    if not available:break
                    old=next((t for t in available if pos%16!=0 or not tt[t][:,0].any()),None)
                    if old is None:continue
                    chosen.append((pos,old));available.remove(old);mapping[old]=pos
                if available:continue
                trial=[np.zeros((16,16),np.uint8)for _ in range(count)]
                for old,new in mapping.items():trial[new]=tt[old].copy()
                size=len(encode_stream(packed(trial,count)));trials+=1
                if best is None or size<best[0]:best=(size,count,trial,mapping,{})
    need(best is not None,'No compact mapping')
    size,count,trial,mapping,flips=best
    for step in range(flip_steps):
        improvement=False
        for old,new in sorted(mapping.items()):
            if old in heads or new%16==0:continue
            candidate=[v.copy()for v in trial];candidate[new]=candidate[new][:,::-1];cost=len(encode_stream(packed(candidate,count)));trials+=1
            if cost<size:trial=candidate;size=cost;flips[old]=not flips.get(old,False);improvement=True
        if not improvement:break
    newparts={}
    for k,rr in parts.items():
        newparts[k]=[[fl^(64 if flips.get(t,False)else 0),mapping[t],x,y]for fl,t,x,y in rr]
    expanded=trial+[np.zeros((16,16),np.uint8)for _ in range(32-count)]
    for k,rr in parts.items():need(np.array_equal(render(tt,rr),render(expanded,newparts[k])),'Compact tile display differs')
    for t in range(0,count,16):need(not trial[t][:,0].any(),'GPU U edge')
    return packed(trial,count),newparts,{'before':len(encode_stream(raw)),'after':size,'saved':len(encode_stream(raw))-size,'count':count,'tile_mapping':mapping,'storage_hflip':flips,'trials':trials,'exact_layers':len(parts)}
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--output',required=True);ap.add_argument('--refs',default='');ap.add_argument('--flip-steps',type=int,default=2);ap.add_argument('--alpha-best',action='store_true');z=ap.parse_args();o=H/z.output;need(not o.exists(),'Fresh output');o.mkdir();source=H/('base_run_alpha_common01/result.json'if z.alpha_best else'base_run_complete_pack05/progress.json');q=json.loads(source.read_text('utf8'));wanted=set(map(int,z.refs.split(',')))if z.refs else None;rows=[]
    for gr in q['groups']:
        refs=gr['refs'];n=refs[0]
        if wanted and n not in wanted:continue
        choice=min((v for v in gr['options']if v['passed']),key=lambda v:v['bytes'])if z.alpha_best else None
        raw=bytes.fromhex(choice['raw']if choice else q['raws'][str(n)]);pp=choice['parts']if choice else q['parts'];parts={(b,f):decode_parts(pp[str(b)][str(f)])for b in(0,5,6,7,8)for f in refs};nr,np_,proof=optimize(raw,parts,z.flip_steps);proof.update(refs=refs,raw=nr.hex(),parts={str(b):{str(f):b''.join(struct.pack('<BBbb',*r)for r in np_[b,f]).hex()for f in refs}for b in(0,5,6,7,8)})
        rows.append(proof);write(o/'result.json',{'analysis_only':True,'resource_written':False,'source_sha256':sha(source.read_bytes()),'groups':rows,'saved':sum(r['saved']for r in rows)})
        print(json.dumps({k:v for k,v in proof.items()if k not in('raw','parts','tile_mapping','storage_hflip')}),flush=True)
if __name__=='__main__':main()
