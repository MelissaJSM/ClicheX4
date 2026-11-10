"""검증된 고정 슬롯 탐색기를 나나 승리/귀환 작업 경로에 한정해 실행한다."""
import argparse,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts import optimize_nana_arrival as optimizer
import numpy as np
from PIL import Image
from scripts.discover_inputs import psx_arc
from src.psx_player import graphics_bank,decode_stream,composition_frame,indexed_atlas
from src.psx_sprite_batch import pack_original_layout
from src.psx_tile_layout import remap_tiles
from psx_compress_cost import encoded_cost

def original_return_grid(a,art):
 arc=(ROOT/art['parent']/'modified.arc').read_bytes();es={int(e['type'],16):arc[e['offset']:e['offset']+e['size']]for e in psx_arc(arc)};f=graphics_bank(es[2],0,allow_bank_aliases=True)['frames'][158];raw=decode_stream(es[2],f['offset'],f['limit'],f['tile_count']*128).data;q=next(r for r in art['groups']if r['frame']==158)
 raw=pack_original_layout(raw,f['tile_count'],np.array(Image.open(a/'frame_158.png')),composition_frame(es[3],0,158),set(q['writable']));atlas,_,_=indexed_atlas(raw,f['tile_count']);v=np.frombuffer(atlas,np.uint8).reshape(-1,256);w=q['writable'];mapping={t:t for t in w};used=set()
 for edge in[t for t in w if t%16==0]:
  if not v[edge//16*16:edge//16*16+16,edge%16*16].any():continue
  candidate=next((t for t in w if t%16!=0 and t not in used and not v[t//16*16:t//16*16+16,t%16*16].any()),None)
  if candidate is None:raise ValueError('No safe transparent edge column')
  mapping[edge],mapping[candidate]=candidate,edge;used.add(candidate)
 cost=encoded_cost(remap_tiles(raw,f['tile_count'],mapping,{},{}));p=a/'packing_158.json';r=json.loads(p.read_text());r.update(post_mapping={str(k):v for k,v in mapping.items()},post_flips={},post_shifts={},encoded_bytes=cost,fits=cost<=r['budget']);p.write_text(json.dumps(r,indent=2),'utf8');return r
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--art',type=Path,required=True);p.add_argument('--frames',type=int,nargs='*');args=p.parse_args();a=args.art.resolve()
 if not a.is_relative_to(ROOT/'work/ver_rin_nana/nana_art/victory_v1'):raise ValueError('Isolated Nana victory art required')
 art=json.loads((a/'art.json').read_text('utf8'))
 if art['task']!='x_nana'or art['scope']!='base_nana_victory_return_10':raise ValueError('Wrong art scope')
 optimizer.a=a
 for n in args.frames or[r['frame']for r in art['groups']]:
  r=optimizer.run(n)
  if n==158:r=original_return_grid(a,art)
  print(r,flush=True)
