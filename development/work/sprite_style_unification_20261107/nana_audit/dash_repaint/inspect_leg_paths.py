from pathlib import Path
import sys,json
import numpy as np
from PIL import Image,ImageDraw
D=Path(__file__).resolve().parent;ROOT=D.parents[3];sys.path[:0]=[str(D),str(D.parent/'native_restore')]
from preview_restore import Archive
from prepare_next_guides import body_path
def main():
 p=json.loads((D/'inputs.json').read_text('utf8'));a=Archive((ROOT/p['parent_arc']).read_bytes());out=D/'leg_path_review';out.mkdir(exist_ok=True)
 for n in (67,69,71,75,77,79,81,83,93,94):
  sheet=Image.new('RGB',(1360,600),(185,197,207));draw=ImageDraw.Draw(sheet)
  for k,ar in enumerate((np.array(Image.open(body_path(n))),np.array(Image.open(D/'fourth_contacts_probe_v2'/f'fourth_{n:03}.png')))):
   im=a.rgba(ar,16 if k else 0).crop((132,152,200,184)).resize((680,320),Image.Resampling.NEAREST);sheet.paste(im,(k*680,200),im);draw.text((k*680+3,180),str(n)+['base','fourth'][k],fill='black')
   for x in range(-28,41,2):
    xx=k*680+(x+28)*10;draw.line((xx,200,xx,520),fill=(155,170,180));draw.text((xx,525),str(x),fill='black')
   for y in range(-8,25,2):
    yy=200+(y+8)*10;draw.line((k*680,yy,k*680+680,yy),fill=(155,170,180));draw.text((k*680+2,yy+2),str(y),fill='black')
  sheet.save(out/f'ref{n}.png')
if __name__=='__main__':main()
