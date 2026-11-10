"""표시가 같은 중첩 픽셀만 복제해 압축 경계의 몇 바이트를 줄인다."""
import sys,json,random
from pathlib import Path
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[4];sys.path[:0]=[str(ROOT),str(ROOT/'work/tools')]
from scripts.discover_inputs import psx_arc,sha256
from src.psx_player import graphics_bank,decode_stream,indexed_atlas
from src.psx_paired_layout import pack_variant_pair
from src.psx_tile_layout import remap_tiles,fill_redundant_pixels
from psx_compress_cost import encoded_cost
d=Path(__file__).parent;a=d/'production08';arc=(ROOT/'out/ver_buki_riko/shibuki_dash_20261026T113618370649Z/modified.arc').read_bytes();e=next(e for e in psx_arc(arc) if int(e['type'],16)==2);gfx=arc[e['offset']:e['offset']+e['size']];bank=graphics_bank(gfx,0,allow_bank_aliases=True)
records=json.loads((a/'packing.json').read_text());layouts=[]
for i,record in enumerate(records):
    n=record['frame'];desc=bank['frames'][n];dec=decode_stream(gfx,desc['offset'],desc['limit'],desc['tile_count']*128);normal=np.array(Image.open(a/f'run_{n:03d}.png'));shot=np.array(Image.open(a/f'shoot_{n:03d}.png'));candidates=[record]
    for folder in ():
        p=d/folder/f'geometry_{n:03d}.json'
        if p.exists():candidates.append(json.loads(p.read_text()))
    valid=[]
    for r in candidates:
        writable={int(k) for k in r['mapping']}
        try:raw,rp,sp,*_=pack_variant_pair(dec.data,desc['tile_count'],normal,shot,r['common_rects'],r['variant_run_rects'],r['variant_shot_rects'],writable)
        except ValueError:continue
        if sha256(raw)!=r['raw_sha256']:continue
        mapping={int(k):v for k,v in r['mapping'].items()};flips={int(k):v for k,v in r['flips'].items()};shifts={int(k):v for k,v in r['shifts'].items()}
        packed=remap_tiles(raw,desc['tile_count'],mapping,flips,shifts)
        convert=lambda parts:[(mapping[t],x-shifts.get(t,(0,0))[0],y-shifts.get(t,(0,0))[1],flips.get(t,0)) for t,x,y in parts]
        assignments={n:convert(rp),n+1:convert(sp)};targets={n:normal,n+1:shot}
        valid.append((encoded_cost(packed),r,packed,assignments,targets,writable))
    best,r,packed,assignments,targets,writable=min(valid,key=lambda q:q[0]);start=best;chosen=[]
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
                            values.append(int(targets[num][py,px]) if 0<=py<80 and 0<=px<96 else 0)
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
                    if not 0<=px<96 or not 0<=py<80:continue
                    key=(tile,x,y);coverage.setdefault((num,py,px),[]).append(key);all_keys.setdefault(key,[]).append((num,py,px))
    def address(key):
        t,x,y=key;return positions[(t//16*16+y)*256+t%16*16+x]
    def value(data,key):
        off,shift=address(key);return (data[off]>>shift)&15
    def put(data,key,v):
        off,shift=address(key);data[off]=(data[off]&~(15<<shift))|(v<<shift)
    def differences(data):
        return [[*key,value(data,key)] for key in all_keys if value(data,key)!=value(packed,key)]
    # Explore overlapping-pixel ownership; target raster stays unchanged.
    import math
    eligible=[]
    for key,uses in all_keys.items():
        if key[0] not in writable:continue
        vs={int(targets[num][py,px]) for num,py,px in uses}
        if len(vs)==1 and 0 not in vs:eligible.append((key,vs.pop()))
    current=bytearray(fill_redundant_pixels(packed,desc['tile_count'],assignments,targets,r.get('overlap_fill',[]),writable));best=encoded_cost(bytes(current));cost=best;winner=current.copy()
    for step in range(50000):
        if best<=r['budget']:break
        key,wanted=rng.choice(eligible);trial=current.copy();old=value(trial,key)
        if old:
            if any(not any(k!=key and value(trial,k) for k in coverage[loc]) for loc in all_keys[key]):continue
            put(trial,key,0)
        else:put(trial,key,wanted)
        score=encoded_cost(bytes(trial));temp=.2+1.8*(1-(step%10000)/10000)
        if score<=cost or rng.random()<math.exp((cost-score)/temp):current=trial;cost=score
        if score<best:
            best=score;winner=trial.copy();print({'frame':n,'step':step,'bytes':best},flush=True)
        if step%10000==9999:current=winner.copy();cost=best
    current=winner
    chosen=differences(current)
    assert bytes(current)==fill_redundant_pixels(packed,desc['tile_count'],assignments,targets,chosen,writable)
    r.update(encoded_bytes=best,fits=best<=r['budget'],overlap_fill=chosen);records[i]=r
    layouts.append({'frame':n,'fits':True,'mode':'variant','rects':r['common_rects'],'run_rects':r['variant_run_rects'],'shot_rects':r['variant_shot_rects']})
    print({'frame':n,'start':start,'final':best,'budget':r['budget'],'fill_pixels':len(chosen),'fits':r['fits']},flush=True)
(a/'packing.json').write_text(json.dumps(records,indent=2));(d/'layout_final.json').write_text(json.dumps(layouts,indent=2))
