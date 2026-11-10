import json,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT))
from PIL import Image,ImageDraw,ImageFont
from scripts.prepare_riko_ui import entry
from scripts.extract_zero import save_image
from src.psx_ui_atlas import aliased_composition,local_composition
from src.psx_static_effect import compose_static
a=(ROOT/'out/ver_rin_nana/nana_run_20261029T062150916963Z/modified.arc').read_bytes();g=entry(a,0x10007)[96*128:];p=struct.pack('<I',4)+entry(a,0x12);pal=entry(a,0x11)
d=Path(__file__).parent;board=Image.new('RGB',(22*68,16*84),'#222630');draw=ImageDraw.Draw(board)
for row in range(16):
 for col,n in enumerate(range(13,35)):
  c=aliased_composition(p,0,n);px,size,_,_=compose_static(g,local_composition(c));words=struct.unpack_from('<16H',pal,row*32);im=save_image(px,size,words,d/'menu_inspect_tmp.png').convert('RGBA').resize((size[0]*3,size[1]*3),Image.Resampling.NEAREST)
  if im.width>64:continue
  board.paste(im,(col*68,row*84+22),im);draw.text((col*68,row*84),f'{n}/p{row}',fill='white')
board.save(d/'menu_icons_inventory.png')
