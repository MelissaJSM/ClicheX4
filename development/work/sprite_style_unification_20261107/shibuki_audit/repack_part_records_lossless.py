"""조립 레코드 순서/내용을 유지하고 공통 접두·접미 바이트만 저장 공유한다."""
import struct
from native_pose_pack import need
from src.psx_player import bank_offsets,composition_frame
from scripts.prepare_shibuki_ultimate_production import records

def find_aligned(haystack,needle):
    return next((i for i in range(0,len(haystack)-len(needle)+1,4)if haystack[i:i+len(needle)]==needle),None)

def repack(c,bank,replacements):
    starts=bank_offsets(c);start=starts[bank];end=starts[bank+1]if bank+1<len(starts)else len(c)
    count=composition_frame(c,bank,0)['bank_frame_count'];rr=[replacements.get(n,records(c,bank,n))for n in range(count)]
    # Header0's data offset also encodes the bank frame count. The first
    # sequence must start exactly at count*4 even if it occurs elsewhere.
    anchor=rr[0];chunks=[]
    for v in sorted(set(rr),key=lambda v:(-len(v),v)):
        if not any(find_aligned(s,v)is not None for s in chunks):chunks.append(v)
    merges=[]
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
        _,i,j,n=best;a,b=chunks[i],chunks[j];merged=a+b[n:];merges.append(n)
        chunks=[x for k,x in enumerate(chunks)if k not in(i,j) and find_aligned(merged,x)is None]+[merged]
    packed=b''.join(sorted(chunks,key=lambda v:(-len(v),v)))
    if not packed.startswith(anchor):
        first=next((x for x in chunks if x.startswith(anchor)),None)
        if first is not None:packed=first+b''.join(x for x in sorted(chunks,key=lambda v:(-len(v),v))if x!=first)
        else:packed=anchor+packed
    need(count*4+len(packed)<=end-start,f'Lossless parts bank {bank} still exceeds by {count*4+len(packed)-(end-start)}')
    out=bytearray(c);out[start+count*4:start+count*4+len(packed)]=packed
    for n,v in enumerate(rr):
        pos=0 if n==0 else find_aligned(packed,v);need(pos is not None,'Missing original record sequence');struct.pack_into('<I',out,start+n*4,((count+pos//4)<<16)|len(v)//4)
    for n,v in enumerate(rr):need(records(out,bank,n)==v,'Reordered semantic record bytes')
    return bytes(out),end-start-count*4-len(packed),{'method':'global_exact_record_suffix_prefix','merged_bytes':sum(merges),'merges':len(merges),'all_record_sequences_exact':True}
