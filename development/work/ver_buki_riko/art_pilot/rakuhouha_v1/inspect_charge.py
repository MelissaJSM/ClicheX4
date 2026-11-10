from pathlib import Path
import sys,json
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT))
import numpy as np
from PIL import Image,ImageDraw
from work.ver_buki_riko.art_pilot.wall_saber_v1.fit_wall import original,rgba,zpal,pal
D=Path(__file__).parent;board=Image.new('RGBA',(5*320,2*400),(32,36,48));dr=ImageDraw.Draw(board)
boxes={177:(13,-5,22,9),178:(3,-35,20,-21),179:(-1,-39,21,-20),180:(4,-35,25,-14),181:(5,-30,23,5)}
for i,n in enumerate(range(177,182)):
 a,b,_=original(n);mask=np.zeros_like(a);x0,y0,x1,y1=boxes[n];mask[y0-b[1]:y1-b[1],x0-b[0]:x1-b[0]]=a[y0-b[1]:y1-b[1],x0-b[0]:x1-b[0]]
 for j,p in enumerate((a,mask)):
  cell=Image.new('RGBA',(80,96));cell.alpha_composite(rgba(p,zpal),(40+b[0],60+b[1]));board.alpha_composite(cell.resize((320,384),Image.Resampling.NEAREST),(i*320,j*400+16));dr.text((i*320+3,j*400+2),str(n)+(' ZERO' if j==0 else ' charge region'),fill='white')
board.save(D/'charge_original_regions.png');(D/'charge_boxes.json').write_text(json.dumps(boxes,indent=2),'utf8')
