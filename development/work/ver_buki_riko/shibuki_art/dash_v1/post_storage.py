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
d=Path(__file__).parent;a=d/'production05';arc=(ROOT/'out/ver_buki_riko/shibuki_air_20261026T104016307897Z/modified.arc').read_bytes();e=next(e for e in psx_arc(arc) if int(e['type'],16)==2);gfx=arc[e['offset']:e['offset']+e['size']];bank=graphics_bank(gfx,0,allow_bank_aliases=True)
records=json.loads((a/'packing.json').read_text());layouts=[]
for r in records:
    if r['fits']:continue
    n=r['frame'];desc=bank['frames'][n];dec=decode_stream(gfx,desc['offset'],desc['limit'],desc['tile_count']*128)
    normal=np.array(Image.open(a/f'run_{n:03d}.png'));shot=np.array(Image.open(a/f'shoot_{n:03d}.png'));w=sorted(int(t) for t in r['mapping'])
    raw,rp,sp,*_=pack_variant_pair(dec.data,desc['tile_count'],normal,shot,r['common_rects'],r['variant_run_rects'],r['variant_shot_rects'],w)
    assert sha256(raw)==r['raw_sha256']
    m={int(k):v for k,v in r['mapping'].items()};f={int(k):v for k,v in r['flips'].items()};s={int(k):v for k,v in r['shifts'].items()}
    packed=remap_tiles(raw,desc['tile_count'],m,f,s)
    convert=lambda parts:[(m[t],x-s.get(t,(0,0))[0],y-s.get(t,(0,0))[1],f.get(t,0)) for t,x,y in parts]
    assignments={n:convert(rp),n+1:convert(sp)};targets={n:normal,n+1:shot}
    packed=fill_redundant_pixels(packed,desc['tile_count'],assignments,targets,r.get('overlap_fill',[]),set(w))
    atlas,pos,_=indexed_atlas(packed,desc['tile_count']);atlas=np.frombuffer(atlas,np.uint8).reshape(-1,256);tiles={t:atlas[t//16*16:t//16*16+16,t%16*16:t%16*16+16].copy() for t in w}
    offsets={t:np.array([[pos[(t//16*16+y)*256+t%16*16+x][0] for x in range(0,16,2)] for y in range(16)]) for t in w}
    base=np.frombuffer(packed,np.uint8).copy();original_flags={t:{flag for rows in assignments.values() for tile,x,y,flag in rows if tile==t} for t in w}
    def cost(mapping,flips,shifts):
        dest=base.copy()
        for t in w:
            tile=tiles[t];yy,xx=np.nonzero(tile);dx,dy=shifts.get(t,(0,0));flag=flips.get(t,0);out=mapping[t]
            if len(xx) and (xx.min()+dx<0 or xx.max()+dx>15 or yy.min()+dy<0 or yy.max()+dy>15):return 100000
            moved=np.zeros_like(tile);moved[yy+dy,xx+dx]=tile[yy,xx]
            if flag&64:moved=moved[:,::-1]
            if flag&128:moved=moved[::-1,:]
            # First-map flags remain relevant to the GPU's final part orientation.
            final_flags={v^flag for v in original_flags[t]}
            if out%16==0 and (moved[:,0].any() or any(v&64 for v in final_flags)):return 100000
            if (out//16)%16==0 and any(v&128 for v in final_flags) and moved[0].any():return 100000
            dest[offsets[out]]=moved[:,::2]|(moved[:,1::2]<<4)
        return encoded_cost(dest.tobytes())
    mapping={t:t for t in w};flips={};shifts={};best=cost(mapping,flips,shifts);assert best==r['encoded_bytes'];rng=random.Random(492+n)
    choices={}
    for t,tile in tiles.items():
        yy,xx=np.nonzero(tile)
        choices[t]=[(dx,dy) for dx in range(-int(xx.min()),16-int(xx.max())) for dy in range(-int(yy.min()),16-int(yy.max()))] if len(xx) else [(0,0)]
    import itertools,math
    for sweep in range(6):
        if best<=r['budget']:break
        candidates=[]
        for u,v in itertools.combinations(w,2):
            nm=dict(mapping);nm[u],nm[v]=nm[v],nm[u];candidates.append((nm,dict(flips),dict(shifts)))
        for t in w:
            for flip in (64,128,192):candidates.append((dict(mapping),{**flips,t:flips.get(t,0)^flip},dict(shifts)))
            for xy in choices[t]:candidates.append((dict(mapping),dict(flips),{**shifts,t:xy}))
        rng.shuffle(candidates);improved=False
        for nm,nf,ns in candidates:
            value=cost(nm,nf,ns)
            if value<best:best,mapping,flips,shifts=value,nm,nf,ns;improved=True
            if best<=r['budget']:break
        print({'frame':n,'post_sweep':sweep,'bytes':best,'budget':r['budget']},flush=True)
        if not improved:break
    current=best;cm,cf,cs=dict(mapping),dict(flips),dict(shifts)
    for step in range(20000):
        if best<=r['budget']:break
        nm,nf,ns=dict(cm),dict(cf),dict(cs);kind=rng.randrange(3)
        if kind==0:
            u,v=rng.sample(w,2);nm[u],nm[v]=nm[v],nm[u]
        elif kind==1:
            t=rng.choice(w);nf[t]=nf.get(t,0)^rng.choice((64,128,192))
        else:
            t=rng.choice(w);ns[t]=rng.choice(choices[t])
        value=cost(nm,nf,ns);temp=.3+2*(1-step/20000)
        if value<=current or rng.random()<math.exp((current-value)/temp):current,cm,cf,cs=value,nm,nf,ns
        if value<best:best,mapping,flips,shifts=value,nm,nf,ns
    r.update(post_mapping=mapping,post_flips=flips,post_shifts=shifts,encoded_bytes=best,fits=best<=r['budget'])
    (a/'packing.json').write_text(json.dumps(records,indent=2));print({'frame':n,'final':best,'fits':r['fits']},flush=True)
