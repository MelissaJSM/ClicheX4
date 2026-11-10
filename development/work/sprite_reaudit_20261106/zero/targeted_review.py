import json
from pathlib import Path
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
FRAMES = {
    'riko': ['b0_147', 'b0_038', 'b1_054', 'b1_001', 'b1_003', 'b1_005', 'b0_164', 'b0_174', 'b1_148', 'b1_163'],
    'rin': ['b0_147', 'b0_039', 'b1_054', 'b1_001', 'b1_004', 'b1_005', 'b0_095', 'b0_174', 'b1_148', 'b1_163'],
}
for char, frames in FRAMES.items():
    baseline = ROOT / 'out/sprite_consistency_20261105' / char
    revpath = ROOT / 'out/sprite_consistency_20261105/revised' / char / 'mapping.json'
    rev = json.loads(revpath.read_text('utf-8'))['frames'] if revpath.exists() else {}
    scale = 5
    box = (112, 100, 208, 196)
    cell = (480, 510)
    board = Image.new('RGB', (cell[0]*5, cell[1]*2), '#27303d')
    d = ImageDraw.Draw(board)
    for i, key in enumerate(frames):
        path = ROOT / rev['normal:'+key] if 'normal:'+key in rev else baseline/'normal/native'/(key+'.png')
        im = Image.open(path).convert('RGBA')
        bounds = im.getbbox()
        assert bounds is None or (bounds[0]>=box[0] and bounds[1]>=box[1] and bounds[2]<=box[2] and bounds[3]<=box[3]), (char,key,bounds)
        crop = im.crop(box).resize((480, 480), Image.Resampling.NEAREST)
        x, y = (i%5)*cell[0], (i//5)*cell[1]
        board.paste(crop, (x,y+30), crop)
        d.text((x+8,y+8), char+' '+key+' | 5x, fixed origin', fill='white')
    board.save(OUT/char/'targeted_5x.png')
