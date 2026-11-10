"""공유 사격 타일의 무손실 배치 후보와 압축 여유를 조사한다."""
import json,sys,itertools,random,math
from pathlib import Path
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.discover_inputs import psx_arc
from src.psx_player import graphics_bank,decode_stream,indexed_atlas
from src.psx_paired_layout import pack_pair,pack_joint_pair
from src.psx_compress import encode_stream
from src.psx_tile_layout import remap_tiles

def remap(raw,count,mapping,flips):
    try:return remap_tiles(raw,count,mapping,flips)
    except ValueError:return None

def main():
    d=ROOT/'work/ver_buki_riko/shibuki_art/unified_idle_run_v4/paired'
    arc=(ROOT/'out/ver_buki_riko/shibuki_idle_20261026T064845428866Z/modified.arc').read_bytes()
    e=next(e for e in psx_arc(arc) if int(e['type'],16)==2);gfx=arc[e['offset']:e['offset']+e['size']]
    bank=graphics_bank(gfx,0,allow_bank_aliases=True)
    plan=json.loads((ROOT/'work/ver_buki_riko/shibuki_run_plan/20261026T044831801392Z/plan.json').read_text())
    pairs=json.loads((d/'pairs.json').read_text());results=[]
    previous=json.loads((d/'packing.json').read_text()) if (d/'packing.json').exists() else []
    for p in sorted(pairs['frames'],key=lambda p:p['run']):
        n=p['run'];desc=bank['frames'][n];dec=decode_stream(gfx,desc['offset'],desc['limit'],desc['tile_count']*128)
        pair=next(p for p in plan['paired_frames'] if p['frames'][0]==n)
        writable=sorted(set(pair['common_base_tiles']+pair['nonshoot_only_tiles']+pair['shoot_only_tiles']))
        layers=[np.array(Image.open(d/f'{s}_{n:03d}.png')) for s in ('run','common','shoot_body','gun')]
        prior=next((p for p in previous if p['frame']==n),None)
        if prior and prior['fits']:
            rects=prior.get('common_rects',p['common_rects'])
            if prior.get('joint_unique_rects'):
                packed,*_=pack_joint_pair(dec.data,desc['tile_count'],layers[0],np.array(Image.open(d/f'shoot_{n:03d}.png')),rects,prior['joint_unique_rects'],writable)
            else:packed,*_=pack_pair(dec.data,desc['tile_count'],*layers,rects,p['run_arm_rect'],p['gun_rect'],writable)
            packed=remap_tiles(packed,desc['tile_count'],{int(k):v for k,v in prior['mapping'].items()},
                              {int(k):v for k,v in prior['flips'].items()},{int(k):v for k,v in prior.get('shifts',{}).items()})
            if len(encode_stream(packed))!=prior['encoded_bytes'] or prior['encoded_bytes']>dec.end-dec.start:raise ValueError('Stored solution changed')
            results.append(prior);print(json.dumps({'frame':n,'stored_solution_verified':True}),flush=True);continue
        if prior and 'common_rects' in prior:p['common_rects']=prior['common_rects'];override_rects=p['common_rects']
        raw,*_=pack_pair(dec.data,desc['tile_count'],*layers,p['common_rects'],p['run_arm_rect'],p['gun_rect'],writable)
        budget=dec.end-dec.start;initial=len(encode_stream(raw));best=initial;mapping={t:t for t in writable};flips={};shifts={}
        prior=next((p for p in previous if p['frame']==n),None)
        if prior:
            mapping={int(k):v for k,v in prior['mapping'].items()};flips={int(k):v for k,v in prior['flips'].items()};shifts={int(k):v for k,v in prior.get('shifts',{}).items()}
            for t,dest in mapping.items():
                if dest%16==0:flips[t]=flips.get(t,0)&128
            candidate=remap_tiles(raw,desc['tile_count'],mapping,flips,shifts);best=len(encode_stream(candidate))
        atlas,_,_=indexed_atlas(raw,desc['tile_count']);movements={}
        for t in writable:
            coords=[(x,y) for y in range(16) for x in range(16) if atlas[(t//16*16+y)*256+t%16*16+x]]
            if not coords:continue
            xs,ys=zip(*coords);movements[t]=[(x,y) for x in range(-min(xs),16-max(xs)) for y in range(-min(ys),16-max(ys))]
        for sweep in range(4):
            if best<=budget:break
            improved=False
            for t,options in movements.items():
                for xy in options:
                    s={**shifts,t:list(xy)}
                    try:packed=remap_tiles(raw,desc['tile_count'],mapping,flips,s)
                    except ValueError:continue
                    size=len(encode_stream(packed))
                    if size<best:best,shifts=size,s;improved=True
                    if best<=budget:break
                if best<=budget:break
            print(json.dumps({'frame':n,'translation_sweep':sweep,'best':best,'budget':budget}),flush=True)
            if not improved:break
        if best>budget:
            for order in itertools.permutations(range(len(p['common_rects']))):
                rects=[p['common_rects'][i] for i in order]
                candidate,*_=pack_pair(dec.data,desc['tile_count'],*layers,rects,p['run_arm_rect'],p['gun_rect'],writable)
                try:packed=remap_tiles(candidate,desc['tile_count'],mapping,flips,shifts)
                except ValueError:continue
                size=len(encode_stream(packed))
                if size<best:
                    best=size;best_order=list(order)
                    print(json.dumps({'frame':n,'order':order,'best':best,'budget':budget}),flush=True)
                if best<=budget:break
        if best>budget and shifts:
            rng=random.Random(n+best+203);cm,cf,cs=dict(mapping),dict(flips),dict(shifts);current=best
            for step in range(2200):
                m,f,s=dict(cm),dict(cf),dict(cs);kind=rng.randrange(3)
                if kind==0:
                    a,b=rng.sample(writable,2);m[a],m[b]=m[b],m[a]
                elif kind==1:
                    a=rng.choice(writable);f[a]=f.get(a,0)^rng.choice((64,128,192))
                else:
                    a=rng.choice(list(movements));s[a]=list(rng.choice(movements[a]))
                try:packed=remap_tiles(raw,desc['tile_count'],m,f,s)
                except ValueError:continue
                size=len(encode_stream(packed));temperature=1+3*(1-step/2200)
                if size<=current or rng.random()<math.exp((current-size)/temperature):current,cm,cf,cs=size,m,f,s
                if size<best:
                    best,mapping,flips,shifts=size,dict(m),dict(f),dict(s)
                    print(json.dumps({'frame':n,'joint_search':step,'best':best,'budget':budget}),flush=True)
                if best<=budget:break
        if best>budget:
            current_rects=[list(r) for r in p['common_rects']]
            for sweep in range(3):
                improved=False
                for i in range(len(current_rects)):
                    base_rect=list(current_rects[i])
                    for dx,dy in itertools.product(range(-3,4),repeat=2):
                        rects=[list(r) for r in current_rects];rects[i]=[base_rect[0]+dx,base_rect[1]+dy]
                        try:
                            candidate,*_=pack_pair(dec.data,desc['tile_count'],*layers,rects,p['run_arm_rect'],p['gun_rect'],writable)
                            packed=remap_tiles(candidate,desc['tile_count'],mapping,flips,shifts)
                        except ValueError:continue
                        size=len(encode_stream(packed))
                        if size<best:
                            best=size;current_rects=rects;improved=True
                            print(json.dumps({'frame':n,'repartition':sweep,'best':best,'budget':budget}),flush=True)
                        if best<=budget:break
                    if best<=budget:break
                if not improved or best<=budget:break
            if current_rects!=p['common_rects']:override_rects=current_rects
        if shifts:
            results.append({'frame':n,'initial':initial,'encoded_bytes':best,'budget':budget,'fits':best<=budget,'mapping':mapping,'flips':flips,'shifts':shifts})
            if 'best_order' in locals():results[-1]['common_order']=best_order;del best_order
            if 'override_rects' in locals():results[-1]['common_rects']=override_rects;del override_rects
            (d/'packing.json').write_text(json.dumps(results+[p for p in previous if p['frame']>n],indent=2));print(json.dumps(results[-1]),flush=True)
            continue
        # Deterministic hill climbing only changes storage, not displayed art.
        seen={};rng=random.Random(n)
        for attempt in range(5):
            if best<=budget:break
            improved=True
            while improved and best>budget:
                improved=False;candidates=[]
                for a,b in itertools.combinations(writable,2):
                    m=dict(mapping);m[a],m[b]=m[b],m[a];candidates.append((m,dict(flips)))
                for a in writable:
                    for bit in (64,128,192):
                        f=dict(flips);f[a]=f.get(a,0)^bit;candidates.append((dict(mapping),f))
                rng.shuffle(candidates)
                for m,f in candidates:
                    key=tuple(m.items()),tuple(sorted(f.items()))
                    if key in seen:continue
                    packed=remap(raw,desc['tile_count'],m,f)
                    if packed is None:continue
                    size=len(encode_stream(packed));seen[key]=size
                    if size<best:
                        best,mapping,flips=size,m,f;improved=True
                        if best<=budget:break
                print(json.dumps({'frame':n,'initial':initial,'best':best,'budget':budget,'tries':len(seen)}),flush=True)
            if best>budget:
                # Escape a local minimum; retain only improving paths in the final record.
                break
        current=best;cm,cf=dict(mapping),dict(flips)
        for attempt in range(1600):
            if best<=budget:break
            m,f=dict(cm),dict(cf)
            if rng.random()<.7:
                a,b=rng.sample(writable,2);m[a],m[b]=m[b],m[a]
            else:
                a=rng.choice(writable);f[a]=f.get(a,0)^rng.choice((64,128,192))
            packed=remap(raw,desc['tile_count'],m,f)
            if packed is None:continue
            size=len(encode_stream(packed));temperature=1+5*(1-attempt/1600)
            if size<=current or rng.random()<math.exp((current-size)/temperature):current,cm,cf=size,m,f
            if size<best:
                best,mapping,flips=size,dict(m),dict(f)
                print(json.dumps({'frame':n,'anneal':attempt,'best':best,'budget':budget}),flush=True)
        results.append({'frame':n,'initial':initial,'encoded_bytes':best,'budget':budget,'fits':best<=budget,
                        'mapping':mapping,'flips':flips})
        (d/'packing.json').write_text(json.dumps(results,indent=2))
        print(json.dumps(results[-1]),flush=True)

if __name__=='__main__':main()
