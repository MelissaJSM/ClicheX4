import json,sys
from pathlib import Path
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[4];sys.path[:0]=[str(ROOT),str(ROOT/'work/tools')]
from scripts.discover_inputs import psx_arc,sha256
from src.psx_player import graphics_bank,decode_stream
from src.psx_paired_layout import pack_variant_pair
from src.psx_tile_layout import remap_tiles
from src.psx_compress import encode_stream
from scripts.solve_paired_cover import paired_cover
d=Path(__file__).parent;a=d/'production05';old=json.loads((d/'production04/packing.json').read_text());art=json.loads((a/'art.json').read_text());plan=json.loads((d/'plan.json').read_text());arc=(ROOT/'out/ver_buki_riko/shibuki_standing_20261026T093104097708Z/modified.arc').read_bytes();e=next(e for e in psx_arc(arc) if int(e['type'],16)==2);gfx=arc[e['offset']:e['offset']+e['size']];bank=graphics_bank(gfx,0,allow_bank_aliases=True);layouts=[];packing=[]
for r in old:
 n=r['frame'];dx=next(q['body_dx'] for q in art['frames'] if q['frame']==n);desc=bank['frames'][n];dec=decode_stream(gfx,desc['offset'],desc['limit'],desc['tile_count']*128);normal=np.array(Image.open(a/f'run_{n:03d}.png'));shot=np.array(Image.open(a/f'shoot_{n:03d}.png'));w={int(k) for k in r['mapping']}
 l={'frame':n,'mode':'variant','fits':True,'rects':[[x+dx,y] for x,y in r['common_rects']],'run_rects':[[x+dx,y] for x,y in r['variant_run_rects']],'shot_rects':r['variant_shot_rects']}
 try:raw,*_=pack_variant_pair(dec.data,desc['tile_count'],normal,shot,l['rects'],l['run_rects'],l['shot_rects'],w)
 except ValueError:
  q=next(q for q in plan['paired_frames'] if q['frames'][0]==n);counts=[len(q[k]) for k in ('common_base_tiles','nonshoot_only_tiles','shoot_only_tiles')];l={**paired_cover(normal,shot,counts,12),'frame':n,'mode':'variant'};assert l['fits'];raw,*_=pack_variant_pair(dec.data,desc['tile_count'],normal,shot,l['rects'],l['run_rects'],l['shot_rects'],w)
 try:modified=remap_tiles(raw,desc['tile_count'],{int(k):v for k,v in r['mapping'].items()},{int(k):v for k,v in r['flips'].items()},{int(k):v for k,v in r['shifts'].items()})
 except ValueError:r.update(mapping={str(t):t for t in w},flips={},shifts={});modified=raw
 size=len(encode_stream(modified));r.update(encoded_bytes=size,fits=size<=r['budget'],common_rects=l['rects'],variant_run_rects=l['run_rects'],variant_shot_rects=l['shot_rects'],raw_sha256=sha256(raw));packing.append(r);layouts.append(l);print({'frame':n,'shift':dx,'bytes':size,'budget':r['budget'],'fits':r['fits']},flush=True)
(a/'packing.json').write_text(json.dumps(packing,indent=2));(d/'layout05.json').write_text(json.dumps(layouts,indent=2))
