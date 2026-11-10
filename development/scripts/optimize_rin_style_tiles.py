"""그림을 보존하는 타일 순서 탐색. 슬롯 주소·크기·효과 타일은 변경하지 않는다."""
import argparse,itertools,json,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.assemble_rin_style_revision import DEST,PARENT
from scripts.build_rin_idle import entry,sha
from src.psx_player import graphics_bank,composition_frame,compose_indices
from src.psx_compress import encode_stream

def tile_slices(count,tile):
    band=tile//16;first=band*16;width=min(16,count-first)*8;base=first*128
    return [slice(base+y*width+(tile%16)*8,base+y*width+(tile%16+1)*8) for y in range(16)]

def permute(raw,count,order):
    if sorted(order)!=list(range(count)):raise ValueError('Tile map must be bijective')
    out=bytearray(raw)
    for target,source in enumerate(order):
        for a,b in zip(tile_slices(count,target),tile_slices(count,source)):out[a]=raw[b]
    return bytes(out)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--bank',type=int,required=True);ap.add_argument('--frame',type=int,required=True);args=ap.parse_args()
    r=json.loads((DEST/'verification.json').read_text());arc=(PARENT/'modified.arc').read_bytes();_,g=entry(arc,2);parts=(DEST/'composition_entry.bin').read_bytes();bank=graphics_bank(g,args.bank);f=bank['frames'][args.frame];refs=[q['index'] for q in bank['frames'] if q['offset']==f['offset']];raw=(DEST/f'stream_{f["offset"]:06x}.bin').read_bytes();count=f['tile_count'];selected=set(r['body_frames'][str(args.bank)]);pb=0 if args.bank==0 else 5
    fixed=set(range(0,count,16))
    for n in refs:
        if n not in selected:fixed.update(p['tile'] for p in composition_frame(parts,pb,n)['parts'])
    movable=sorted(set(range(count))-fixed);identity=list(range(count));best_order=identity;best=len(encode_stream(raw));initial=best;cache={tuple(identity):best};trials=0
    def score(order):
        nonlocal trials
        key=tuple(order)
        if key not in cache:cache[key]=len(encode_stream(permute(raw,count,order)));trials+=1
        return cache[key]
    data={t:b''.join(raw[s] for s in tile_slices(count,t)) for t in movable}
    seeds=[]
    for key in (lambda t:data[t],lambda t:data[t][::-1],lambda t:(sum(v!=0 for v in data[t]),data[t])):
        for reverse in (False,True):
            order=identity.copy()
            for pos,t in zip(movable,sorted(movable,key=key,reverse=reverse)):order[pos]=t
            seeds.append(order)
    for order in seeds:
        value=score(order)
        if value<best:best=value;best_order=order
    for step in range(4):
        current=best;winner=best_order
        for x,y in itertools.combinations(movable,2):
            order=best_order.copy();order[x],order[y]=order[y],order[x];value=score(order)
            if value<current:current=value;winner=order
        if current>=best:break
        best,best_order=current,winner
        print(json.dumps({'frame':args.frame,'step':step,'bytes':best,'budget':f['limit']-f['offset'],'trials':trials}),flush=True)
        if best<=f['limit']-f['offset']:break
    packed=permute(raw,count,best_order);mapping={old:new for new,old in enumerate(best_order)};updated=bytearray(parts)
    for n in refs:
        for p in composition_frame(parts,pb,n)['parts']:updated[p['record_offset']+1]=mapping[p['tile']]
    for n in refs:
        before=compose_indices(raw,count,composition_frame(parts,pb,n));after=compose_indices(packed,count,composition_frame(updated,pb,n))
        if before[:3]!=after[:3]:raise ValueError('Permutation changed displayed pixels')
    report={'bank':args.bank,'frames':refs,'offset':f['offset'],'source_raw_sha256':sha(raw),'source_parts_sha256':sha(parts),'initial_bytes':initial,'encoded_bytes':best,'budget':f['limit']-f['offset'],'order':best_order,'fixed_tiles':sorted(fixed),'trials':trials,'display_pixels_identical':True}
    (DEST/f'tile_order_bank{args.bank}_{args.frame}.json').write_text(json.dumps(report,indent=2)+'\n','utf-8');print(json.dumps(report))

if __name__=='__main__':main()
