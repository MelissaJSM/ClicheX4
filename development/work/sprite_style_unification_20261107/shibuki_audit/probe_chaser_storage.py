"""새 체이서의 타일 번호/빈 여백/비겹침 파트순서만 무손실 탐색한다."""
from pathlib import Path
import sys,json,struct,itertools
import numpy as np
from PIL import Image
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'work/tools'))
from pack_chaser_base import *
from scripts.optimize_rin_style_tiles import permute,tile_slices
from psx_compress_cost import encoded_cost
from repack_part_records_lossless import find_aligned

def packed_size(c,bank,replacements):
    count=composition_frame(c,bank,0)['bank_frame_count'];rr=[replacements.get(n,records(c,bank,n))for n in range(count)];anchor=rr[0];chunks=[]
    for v in sorted(set(rr),key=lambda v:(-len(v),v)):
        if not any(find_aligned(s,v)is not None for s in chunks):chunks.append(v)
    while len(chunks)>1:
        best=None
        for i,a in enumerate(chunks):
            for j,b in enumerate(chunks):
                if i==j:continue
                overlap=next((n for n in range(min(len(a),len(b)),0,-4)if a[-n:]==b[:n]),0)
                if not overlap:continue
                score=(overlap,-len(a)-len(b),-i,-j)
                if best is None or score>best[0]:best=(score,i,j,overlap)
        if best is None:break
        _,i,j,n=best;merged=chunks[i]+chunks[j][n:];chunks=[x for k,x in enumerate(chunks)if k not in(i,j)and find_aligned(merged,x)is None]+[merged]
    packed=b''.join(sorted(chunks,key=lambda v:(-len(v),v)))
    if not any(v.startswith(anchor)for v in chunks):packed=anchor+packed
    return count*4+len(packed)

def optimize(raw,count,fixed,steps=6):
    move=sorted(set(range(count))-set(fixed));data={t:b''.join(raw[s]for s in tile_slices(count,t))for t in range(count)}
    identity=list(range(count));order=identity;best=encoded_cost(raw);cache={tuple(identity):best}
    def score(seq):
        k=tuple(seq)
        if k not in cache:cache[k]=encoded_cost(permute(raw,count,seq))
        return cache[k]
    for key in(lambda t:data[t],lambda t:data[t][::-1],lambda t:(sum(v!=0 for v in data[t]),data[t])):
        for reverse in(False,True):
            seq=identity.copy()
            for p,t in zip(move,sorted(move,key=key,reverse=reverse)):seq[p]=t
            v=score(seq)
            if v<best:best,order=v,seq
    for _ in range(steps):
        value,winner=best,order
        for x,y in itertools.combinations(move,2):
            seq=order.copy();seq[x],seq[y]=seq[y],seq[x];v=score(seq)
            if v<value:value,winner=v,seq
        if value>=best:break
        best,order=value,winner
    output=permute(raw,count,order);need(len(encode_stream(output))==best,'압축 비용 불일치')
    return output,{old:new for new,old in enumerate(order)},{'order':order,'before':len(encode_stream(raw)),'after':best,'trials':len(cache),'fixed_tiles':list(fixed)}

def make_groups():
    allrr={b:{}for b in PBS};raws={};counts={};report=[]
    for ns in GROUPS:
        n=ns[0];nr,pp=pack_planes(bytes(4096),32,[crop(np.array(Image.open(TD/f'{n:03}_bank{b}_indices.png')))for b in PBS],set(range(1,32))-{16},[24]*5)
        head=pp[1];need(len(head)==2,'두 머리기록');top,low=sorted(head,key=lambda p:p[2])
        if n==166:
            t,x,y,fl=low;need(fl==0 and sum(p[0]==t for ps in pp for p in ps)==1,'머리 단독타일')
            at=np.frombuffer(indexed_atlas(nr,32)[0],np.uint8).reshape(32,256).copy();tile=at[t//16*16:t//16*16+16,t%16*16:t%16*16+16].copy();ny,nx=y-72,x-80
            yy,xx=np.nonzero(tile);need((yy+ny<16).all()and(xx+nx<16).all(),'창내 이동 범위');q=np.zeros((16,16),np.uint8);q[yy+ny,xx+nx]=tile[yy,xx];at[t//16*16:t//16*16+16,t%16*16:t%16*16+16]=q;nr=bytes((at[:,::2]|(at[:,1::2]<<4)).ravel());low=(t,80,72,fl);pp[1]=[top,low]
        count=max(t for ps in pp for t,x,y,fl in ps)+1;nr=resize_tile_storage(nr,32,count)
        order=list(range(count))
        for slot,old in((1,top[0]),(2,low[0])):
            at=order.index(old);order[slot],order[at]=order[at],order[slot]
        nr=permute(nr,count,order);mp={old:new for new,old in enumerate(order)};pp=[[(mp[t],x,y,fl)for t,x,y,fl in ps]for ps in pp]
        nr,mp,opt=optimize(nr,count,(0,1,2));pp=[[(mp[t],x,y,fl)for t,x,y,fl in ps]for ps in pp]
        for ref in ns:
            raws[ref]=nr;counts[ref]=count
            for b,ps in zip(PBS,pp):allrr[b][ref]=b''.join(struct.pack('<BBbb',fl,t,x-80,y-80+DY[ref])for t,x,y,fl in ps)
        report.append({'master':n,'refs':list(ns),'count':count,'compressed':len(encode_stream(nr)),'optimization':opt,'raw_sha256':sha(nr)});print(json.dumps(report[-1]),flush=True)
    return raws,counts,allrr,report

def main():
    d=H/'chaser_storage01';need(not d.exists(),'새 조사 폴더');d.mkdir();a=Archive(P.read_bytes());raws,counts,rr,groups=make_groups();bs=bank_offsets(a.c);capacity=bs[6]-bs[5];initial=packed_size(a.c,5,rr[5]);best=initial;reversed_refs=[]
    for _ in range(4):
        changed=False
        for n in REFS:
            trial=dict(rr[5]);trial[n]=trial[n][4:]+trial[n][:4];v=packed_size(a.c,5,trial)
            if v<best:rr[5]=trial;best=v;changed=True;reversed_refs.append(n)
        if not changed:break
    for n in REFS:(d/f'{n:03}.raw').write_bytes(raws[n])
    try:_,gfx=repack_fixed_global(a,raws,counts)
    except ValueError as ex:gfx={'error':str(ex)}
    write(d/'recipe.json',{'parent_sha256':PARENT,'manifest_sha256':MANIFEST,'groups':groups,'parts':{str(b):{str(n):v.hex()for n,v in q.items()}for b,q in rr.items()},'head_storage':{'before':initial,'after':best,'capacity':capacity,'reversed_refs':reversed_refs},'graphics':gfx,'arc_written':False})
    print(json.dumps({'head':(initial,best,capacity),'reversed_refs':reversed_refs,'graphics':gfx}))
if __name__=='__main__':main()
