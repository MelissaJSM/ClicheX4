"""얼굴/외곽/크기를 보존하며 고립된 내부 명암 한 도트의 팔레트 선택을 검수한다."""
import sys,json,shutil
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[4];sys.path[:0]=[str(ROOT),str(ROOT/'work/tools')]
from scripts.discover_inputs import psx_arc,sha256
from scripts.extract_zero import save_image
from src.psx_player import graphics_bank,decode_stream
from src.psx_paired_layout import pack_variant_pair
from src.psx_tile_layout import remap_tiles,fill_redundant_pixels
from psx_compress_cost import encoded_cost
d=Path(__file__).parent;source=d/'production05';out=d/'production10';shutil.copytree(source,out)
art=json.loads((out/'art.json').read_text());records=json.loads((out/'packing.json').read_text());pal=art['palette_words'];rgb=np.array([[(w&31)*255//31,((w>>5)&31)*255//31,((w>>10)&31)*255//31] for w in pal])
arc=(ROOT/'out/ver_buki_riko/shibuki_dash_20261026T113618370649Z/modified.arc').read_bytes();e=next(e for e in psx_arc(arc) if int(e['type'],16)==2);gfx=arc[e['offset']:e['offset']+e['size']];bank=graphics_bank(gfx,0,allow_bank_aliases=True);changes=[]
for r in records:
    if r['fits']:continue
    n=r['frame'];normal=np.array(Image.open(out/f'run_{n:03d}.png'));shot=np.array(Image.open(out/f'shoot_{n:03d}.png'));desc=bank['frames'][n];dec=decode_stream(gfx,desc['offset'],desc['limit'],desc['tile_count']*128);w={int(k) for k in r['mapping']}
    m={int(k):v for k,v in r['mapping'].items()};f={int(k):v for k,v in r['flips'].items()};s={int(k):v for k,v in r['shifts'].items()}
    def prepare(a,b):
        raw,rp,sp,*_=pack_variant_pair(dec.data,desc['tile_count'],a,b,r['common_rects'],r['variant_run_rects'],r['variant_shot_rects'],w)
        packed=remap_tiles(raw,desc['tile_count'],m,f,s);convert=lambda rows:[(m[t],x-s.get(t,(0,0))[0],y-s.get(t,(0,0))[1],f.get(t,0)) for t,x,y in rows]
        packed=fill_redundant_pixels(packed,desc['tile_count'],{n:convert(rp),n+1:convert(sp)},{n:a,n+1:b},r.get('overlap_fill',[]),w)
        if r.get('post_mapping'):packed=remap_tiles(packed,desc['tile_count'],{int(k):v for k,v in r['post_mapping'].items()},{int(k):v for k,v in r['post_flips'].items()},{int(k):v for k,v in r['post_shifts'].items()})
        return raw,encoded_cost(packed)
    assert prepare(normal,shot)[1]==r['encoded_bytes']
    eye_y=float(np.median(np.nonzero(normal==7)[0]));a=normal.copy();b=shot.copy();edits=[];cost=r['encoded_bytes']
    for iteration in range(8):
        if cost<=r['budget']:break
        candidates=[]
        for y in range(int(eye_y)+5,57):
            for x in range(1,95):
                old=int(a[y,x]);block=a[y-1:y+2,x-1:x+2]
                if not old or old in (7,15) or b[y,x]!=old or np.count_nonzero(block)==1:continue
                if any((x,y)==q[:2] for q in edits):continue
                counts=np.bincount(block.ravel(),minlength=16)
                for value in range(1,15):
                    if value in (old,7) or counts[value]<3:continue
                    distance=float(np.linalg.norm(rgb[old]-rgb[value]))
                    if distance>125:continue
                    ta=a.copy();tb=b.copy();ta[y,x]=value;tb[y,x]=value
                    try:raw,tc=prepare(ta,tb)
                    except ValueError:continue
                    if tc<cost:candidates.append((tc,distance,x,y,old,value,raw,ta,tb))
        if not candidates:break
        cost,distance,x,y,old,value,raw,a,b=min(candidates,key=lambda q:q[:2]);edits.append((x,y,old,value));print({'iteration':iteration,'cost':cost,'pixel':edits[-1]},flush=True)
    for name in ('run','shoot','common'):
        im=np.array(Image.open(out/f'{name}_{n:03d}.png'))
        for x,y,old,value in edits:
            if im[y,x]==old:im[y,x]=value
        save_image(im.tobytes(),(96,80),pal,out/f'{name}_{n:03d}.png')
    r.update(raw_sha256=sha256(raw),encoded_bytes=cost,fits=cost<=r['budget'])
    changes.append({'frame':n,'pixels':edits,'normal_and_shot_changed_together':True,'alpha_face_boots_unchanged':True})
    print({'frame':n,'cost':cost,'budget':r['budget'],'pixels':edits},flush=True)
art['final_internal_quantization_refinement']=changes;(out/'art.json').write_text(json.dumps(art,indent=2));(out/'packing.json').write_text(json.dumps(records,indent=2));(out/'quantization_changes.json').write_text(json.dumps(changes,indent=2))
print('Final internal shading prepared',flush=True)
