"""현재 각 폼을 같은 좌표·배율로 배치한다. 원래 그림은 바꾸지 않는다."""
from pathlib import Path
from PIL import Image,ImageDraw
H=Path(__file__).resolve().parent
GROUPS={'wall':[55,59,63,65], 'dash':[67,71,77,83], 'hurt':[106,110,120,234], 'arrival':[133,135,138,141], 'ladder':[143,144,150,183], 'victory':[156,158,204,207], 'vehicles':[162,166,170,188], 'nova_hover':[213,217,221,229], 'late_special':[99,100,231,232]}
for group,refs in GROUPS.items():
 board=Image.new('RGB',(5*200,4*225),(26,32,43));d=ImageDraw.Draw(board)
 for row,form in enumerate(('base','fourth','ultimate_before','ultimate_after')):
  for col,n in enumerate([0]+refs):
   im=Image.open(H/form/f'{n:03}.png').crop((128,124,192,188)).resize((192,192),Image.Resampling.NEAREST)
   x,y=col*200,row*225;d.text((x+3,y+2),f'{form} / {n}',fill='white');board.paste(im,(x,y+26),im)
 board.save(H/f'matrix_{group}.png')
