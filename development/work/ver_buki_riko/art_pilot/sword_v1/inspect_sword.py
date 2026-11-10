from pathlib import Path
import sys,json,struct
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT))
from scripts.repack_zero import read_inputs
from src.psx_player import graphics_bank,composition_frame,decode_stream,compose_indices
from src.psx_frame_edit import frame_coverage
from scripts.discover_inputs import psx_arc
D=Path(__file__).parent
E=ROOT/'work/ver_buki_riko/zero_extract/20261023T062408235550Z'
profile,project,arc,gmeta,gfx,parts,zero_pal=read_inputs(E)
bank=graphics_bank(gfx,0)
pal=struct.unpack('<16H',(ROOT/'out/ver_buki_riko/riko_pilot_20261023T082720987715Z/candidate_palette.bin').read_bytes())
epal=struct.unpack_from('<16H',(E/'palette_bank.bin').read_bytes(),3*32)
old=ROOT/'work/ver_buki_riko/art_pilot/air_slash_v1'
recipe=json.loads((old/'recipe.json').read_text('utf8'))
def rgba(a,palette=pal):
 colors=np.array([[(w&31)*255//31,((w>>5)&31)*255//31,((w>>10)&31)*255//31,255 if i else 0] for i,w in enumerate(palette)],dtype=np.uint8)
 return Image.fromarray(colors[a])
def original(n):
 f=bank['frames'][n];c=composition_frame(parts,0,n);raw=decode_stream(gfx,f['offset'],f['limit'],f['tile_count']*128).data
 data,size,b,_=compose_indices(raw,f['tile_count'],c);cov,_,_=frame_coverage(raw,f['tile_count'],c)
 safe=np.array([bool(x) for x in cov]).reshape(size[1],size[0])
 for p in c['parts']:
  if p['tile']%16==0:safe[p['y']-b[1]:p['y']-b[1]+16,p['x']-b[0]]=False
 return np.frombuffer(data,np.uint8).reshape(size[1],size[0]),b,safe
if __name__=='__main__':
 keys=[(61,None),(62,None),(63,64),(65,66),(67,68),(77,78),(81,80),(82,None),(83,84),(85,86),(87,88),(89,90),(91,92),(99,100),(105,106),(107,108),(109,110),(111,112),(117,118),(125,126),(130,None),(131,None),(133,None),(213,214),(215,216),(217,218),(219,220),(221,222),(223,224),(225,226),(227,228),(229,228),(230,231),(232,233),(234,235),(236,237),(238,239),(240,241),(242,243),(244,245),(246,245)]
 for group in range(4):
  subset=keys[group*12:(group+1)*12];board=Image.new('RGBA',(4*480,((len(subset)+3)//4)*390),(35,40,50));draw=ImageDraw.Draw(board)
  for i,(n,e) in enumerate(subset):
   a,b,safe=original(n);r=np.array(Image.open(old/recipe['frames'][str(n)]['file']));cell=Image.new('RGBA',(120,96),(35,40,50))
   s=np.zeros((*safe.shape,4),np.uint8);s[safe]=[52,58,68,255];cell.alpha_composite(Image.fromarray(s),(60+b[0],48+b[1]));cell.alpha_composite(rgba(r),(60+b[0],48+b[1]))
   if e:
    ea,eb,_=original(e);cell.alpha_composite(rgba(ea,epal),(60+eb[0],48+eb[1]))
   cell=cell.resize((480,384),Image.Resampling.NEAREST);board.alpha_composite(cell,(i%4*480,i//4*390+6));draw.text((i%4*480+4,i//4*390+6),f'{n}/{e} bounds{b}',fill='yellow')
  board.save(D/f'body_effect_{group}.png')
 print(json.dumps({'palette':pal,'effect_palette':epal,'body_keys':keys}))
