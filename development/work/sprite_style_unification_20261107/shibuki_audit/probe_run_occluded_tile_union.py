"""선택된 새 그림의 겹침 뒤 동일 표시를 보장하는 타일 합집합 시험.

기존 불투명 픽셀은 고정한다. 빈 texel에는 모든 소비 조립에서 뒤의
불투명 파츠에 가려지거나 목표와 같은 색인인 경우에만 값을 허용한다.
합친 뒤 모든 실제 목표층을 다시 합성한다. 게임 ARC는 작성하지 않는다.
"""
from pathlib import Path
import sys,json,struct,argparse,itertools
import numpy as np
from PIL import Image
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import sha,need,write
from src.psx_player import indexed_atlas
from src.psx_compress import encode_stream

def tiles_of(raw):
    at=np.frombuffer(indexed_atlas(raw,32)[0],np.uint8).reshape(32,256)
    return [at[t//16*16:t//16*16+16,t%16*16:t%16*16+16].copy()for t in range(32)]
def raw_of(tiles):
    at=np.zeros((32,256),np.uint8)
    for t,v in enumerate(tiles):at[t//16*16:t//16*16+16,t%16*16:t%16*16+16]=v
    return (at[:,::2]|(at[:,1::2]<<4)).tobytes()
def decode_parts(h):return [list(struct.unpack_from('<BBbb',bytes.fromhex(h),i))for i in range(0,len(h)//2,4)]
def render(tiles,parts):
    out=np.zeros((384,384),np.uint8)
    for fl,t,x,y in parts:
        need(not fl&0x3f,'Unsupported flags');v=tiles[t]
        if fl&64:v=v[:,::-1]
        if fl&128:v=v[::-1]
        dst=out[y+160:y+176,x+160:x+176];dst[v>0]=v[v>0]
    return out
def constraints(tiles,allparts,targets):
    allowed=[np.full((16,16),65535,np.uint16)for _ in range(32)];used=set()
    for k,parts in allparts.items():
        need(np.array_equal(render(tiles,parts),targets[k]),'Initial target differs')
        cover=np.zeros((384,384),bool)
        for fl,t,x,y in reversed(parts):
            used.add(t);v=tiles[t];mx=np.zeros((16,16),np.uint16)
            for sy in range(16):
                for sx in range(16):
                    wx=x+160+(15-sx if fl&64 else sx);wy=y+160+(15-sy if fl&128 else sy)
                    if v[sy,sx]:bits=1<<int(v[sy,sx])
                    elif cover[wy,wx]:bits=65535
                    else:bits=1|(1<<int(targets[k][wy,wx]))
                    mx[sy,sx]=bits
                    if v[sy,sx]:cover[wy,wx]=True
            allowed[t]&=mx
    for t in(0,16):allowed[t][:,0]&=1
    return allowed,used
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--output',required=True);ap.add_argument('--source',default='base_run_complete_pack05/progress.json');ap.add_argument('--refs',default='');z=ap.parse_args();out=H/z.output;need(not out.exists(),'Fresh output');out.mkdir();src=H/z.source;q=json.loads(src.read_text('utf8'));rows=[];wanted=set(map(int,z.refs.split(',')))if z.refs else None
    for gr in q['groups']:
        refs=gr['refs'];n=refs[0]
        if wanted and n not in wanted:continue
        raw=bytes.fromhex(q['raws'][str(n)]);tiles=tiles_of(raw);parts={(b,f):decode_parts(q['parts'][str(b)][str(f)])for b in(0,5,6,7,8)for f in refs};target={k:np.array(Image.open(H/f'base_run_complete_targets01/{k[1]:03}_bank{k[0]}_indices.png'))for k in parts};before=len(encode_stream(raw));merges=[]
        for step in range(32):
            masks,used=constraints(tiles,parts,target);best=None
            for a,b in itertools.combinations(sorted(used-{0}),2):
                # Preserve the pinned head bank's tile address and page edge.
                if b in(10,11,12,13,14,15):a,b=b,a
                if a in(0,16)or b in(10,11,12,13,14,15):continue
                for flip in(False,True):
                    vb=tiles[b][:,::-1]if flip else tiles[b];mb=masks[b][:,::-1]if flip else masks[b]
                    common=masks[a]&mb
                    if not np.all(common):continue
                    merged=np.where(tiles[a]>0,tiles[a],vb).astype(np.uint8)
                    bits=np.left_shift(np.uint16(1),merged.astype(np.uint16))
                    if not np.all(common&bits):continue
                    tt=[v.copy()for v in tiles];tt[a]=merged;tt[b][:]=0;newraw=raw_of(tt);cost=len(encode_stream(newraw));saved=len(encode_stream(raw_of(tiles)))-cost
                    if saved<=0:continue
                    if best is None or saved>best[0]:best=(saved,cost,a,b,flip,tt)
            if best is None:break
            saved,cost,a,b,flip,tiles=best
            for rr in parts.values():
                for r in rr:
                    if r[1]==b:r[1]=a;r[0]^=64 if flip else 0
            for k,rr in parts.items():need(np.array_equal(render(tiles,rr),target[k]),'Merged display differs')
            merges.append({'from_tile':b,'to_tile':a,'flip_x':flip,'saved':saved,'bytes':cost})
        result=raw_of(tiles);row={'refs':refs,'before':before,'after':len(encode_stream(result)),'saved':before-len(encode_stream(result)),'merges':merges,'raw':result.hex(),'parts':{str(b):{str(f):b''.join(struct.pack('<BBbb',*r)for r in parts[b,f]).hex()for f in refs}for b in(0,5,6,7,8)},'exact_layers':len(parts)};rows.append(row)
        write(out/'result.json',{'analysis_only':True,'resource_written':False,'source_sha256':sha(src.read_bytes()),'groups':rows,'saved':sum(r['saved']for r in rows)})
        print(json.dumps({k:v for k,v in row.items()if k not in('raw','parts')}),flush=True)
if __name__=='__main__':main()
