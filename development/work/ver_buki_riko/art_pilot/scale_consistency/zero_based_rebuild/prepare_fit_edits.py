from pathlib import Path
from PIL import Image
import json
P=Path(__file__).parent
r=json.loads((P/'recipe.json').read_text())
ROOT=P.resolve().parents[4]
from sys import path
path.insert(0,str(ROOT))
from scripts.repack_zero import read_inputs
from src.psx_player import composition_frame,graphics_bank,decode_stream
from src.psx_frame_edit import frame_coverage
_,_,_,_,gfx,parts,_=read_inputs(ROOT/'work/ver_buki_riko/zero_extract/20261023T062408235550Z')
bank=graphics_bank(gfx,0);sheet=Image.new('RGBA',(128,72))
for i,n in enumerate([9,17]):
    f=bank['frames'][n];raw=decode_stream(gfx,f['offset'],f['limit'],f['tile_count']*128).data
    _,_,b=frame_coverage(raw,f['tile_count'],composition_frame(parts,0,n))
    sheet.alpha_composite(Image.open(P/f'frame_{n:03d}.png').convert('RGBA'),(i*64+32+b[0],40+b[1]))
sheet.resize((1024,576),Image.Resampling.NEAREST).save(P/'fit_edit_reference.png')
