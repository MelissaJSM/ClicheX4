"""Create local native-pixel masters for the approved Ultimate costume."""
import json, struct, sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.analyze_shibuki_ultimate import D
from scripts.prepare_riko_ui import entry
from scripts.extract_zero import save_image
from src.psx_player import graphics_bank, decode_stream, composition_frame
from src.psx_sprite_batch import canvas_from_parts

GROUPS={'run':list(range(1,33,2)),
 'air_dash':[33,35,37,39,41,43,45,49,55,57,59,65,67,71,77,83],
 'action':[85,88,89,90,97,98,100,101,106,110,120,133,135,137,138,204],
 'back_other':[143,144,145,146,148,151,152,153,154,156,162,174,183,207,217,221]}

def main():
 out=D/'production_art';out.mkdir(exist_ok=False)
 arc=(D/'analysis/parent_PL00_U.ARC').read_bytes();g,c,pal=[entry(arc,k) for k in (2,3,9)]
 bank=graphics_bank(g,0,allow_bank_aliases=True);words=struct.unpack_from('<16H',pal)
 for n in sorted(set(range(237))-{105,*range(175,183)}):
  f=bank['frames'][n];raw=decode_stream(g,f['offset'],f['limit'],f['tile_count']*128).data
  v=canvas_from_parts(raw,f['tile_count'],composition_frame(c,0,n))
  save_image(v.tobytes(),(160,160),words,out/f'base_{n:03}.png')
 for name,frames in GROUPS.items():
  sheet=Image.new('RGB',(1280,1408),'#253546');draw=ImageDraw.Draw(sheet)
  for i,n in enumerate(frames):
   im=Image.open(out/f'base_{n:03}.png').convert('RGBA').crop((32,32,128,128)).resize((320,320),Image.Resampling.NEAREST)
   x=i%4*320;y=i//4*352;sheet.paste(im,(x,y+32),im);draw.text((x+12,y+12),str(n),fill='white')
  sheet.save(out/f'{name}_reference.png')
 (out/'master_groups.json').write_text(json.dumps(GROUPS,indent=2))
 print(out)

if __name__=='__main__':main()
