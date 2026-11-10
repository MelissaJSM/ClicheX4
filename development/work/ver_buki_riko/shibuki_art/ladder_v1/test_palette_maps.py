"""몸 크기·알파·얼굴·외곽을 고정한 채 의상 내부 근접 팔레트 명암만 정리."""
import json,sys,shutil
from pathlib import Path
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[4];sys.path[:0]=[str(ROOT),str(ROOT/'work/tools')]
from scripts.discover_inputs import psx_arc,sha256
from scripts.extract_zero import save_image
from src.psx_player import graphics_bank,decode_stream
from psx_variant_search import VariantSearch
from psx_compress_cost import encoded_cost
d=Path(__file__).parent;a=d/'production04';packing=json.loads((a/'packing.json').read_text());r=next(r for r in packing if r['frame']==154);art=json.loads((a/'art.json').read_text());pal=art['palette_words'];rgb=np.array([[(w&31)*255//31,((w>>5)&31)*255//31,((w>>10)&31)*255//31] for w in pal],np.int32)
arc=(ROOT/'out/ver_buki_riko/shibuki_hurt_20261026T141724356492Z/modified.arc').read_bytes();e=next(e for e in psx_arc(arc) if int(e['type'],16)==2);g=arc[e['offset']:e['offset']+e['size']];desc=graphics_bank(g,0,allow_bank_aliases=True)['frames'][154];dec=decode_stream(g,desc['offset'],desc['limit'],desc['tile_count']*128);target=np.array(Image.open(a/'frame_154.png'));before=target.copy();changes=[]
def cost(t):
 search=VariantSearch(dec.data,desc['tile_count'],t,t,r['writable']);raw,packed=search.pack(r['rects'],[],[],{int(k):v for k,v in r['mapping'].items()},{int(k):v for k,v in r['flips'].items()},{int(k):v for k,v in r['shifts'].items()});return encoded_cost(packed),sha256(raw)

for pairs in [[],[(6,5)],[(2,15)],[(11,10)],[(6,5),(2,15)],[(6,5),(11,10)],[(6,5),(8,14)]]:
 t=before.copy()
 for old,new in pairs:t[before==old]=new
 print(pairs,cost(t)[0],int((t!=before).sum()))
