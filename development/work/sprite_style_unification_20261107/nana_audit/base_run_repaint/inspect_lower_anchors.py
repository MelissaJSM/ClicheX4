from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[4];sys.path[:0]=[str(ROOT),str(Path(__file__).parent.parent/'native_restore')]
from preview_restore import Archive
from PIL import Image,ImageDraw,ImageFont
import numpy as np
D=Path(__file__).parent
a=Archive((D/'baseline_PL00_U.ARC').read_bytes());out=D/'anchor_inspection';out.mkdir(exist_ok=True)
font=ImageFont.truetype('C:/Windows/Fonts/consola.ttf',12)
for page in range(4):
 board=Image.new('RGB',(1400,4*440),'#bdc8cd');draw=ImageDraw.Draw(board)
 for row,n in enumerate(range(page*8+1,page*8+9,2)):
  for col,(folder,pal) in enumerate([('cycle_registered_v1',0),('fourth_body_scale',16)]):
   ar=np.array(Image.open(D/folder/f'run_{n:03}.png'));im=a.rgba(ar,pal).crop((132,160,192,187)).resize((600,270),Image.Resampling.NEAREST);x=col*700+60;y=row*440+80;board.paste(im,(x,y),im);draw.text((x,y-50),f'{n} {folder}',font=font,fill='black')
   for wx in range(-28,33,4):
    px=x+(wx+28)*10;draw.line((px,y,px,y+270),fill='#828d93');draw.text((px,y-20),str(wx),font=font,fill='black')
   for wy in range(0,28,2):
    py=y+wy*10;draw.line((x,py,x+600,py),fill='#828d93');draw.text((x-25,py),str(wy),font=font,fill='black')
 board.save(out/f'page{page+1}.png')
