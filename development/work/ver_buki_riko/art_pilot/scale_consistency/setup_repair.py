from pathlib import Path
import json,sys
import numpy as np
from PIL import Image
P=Path(__file__).parent
exec((P/'fit_probe.py').read_text(encoding='utf-8').split('run_slots=')[0])
R=P/'gait_cape_repair';R.mkdir(exist_ok=True)
def rgba(a):
 out=np.zeros((*a.shape,4),dtype=np.uint8);m=a!=0;out[m,:3]=colors[a[m]-1];out[m,3]=255;return Image.fromarray(out)
worlds={}
for n in [7,27,33,34]:
 a=np.array(Image.open(P/f'locked_frame_{n:03d}.png'));b=geometry[n][1];w=np.zeros((128,128),dtype=np.uint8);w[64+b[1]:64+b[3],64+b[0]:64+b[2]]=a;worlds[n]=w
sheet=Image.new('RGBA',(192,72))
for k,n in enumerate([27,33,34]):sheet.alpha_composite(rgba(worlds[n][24:96,32:96]),(k*64,0))
sheet.resize((1536,576),Image.Resampling.NEAREST).save(R/'cape_edit_reference.png')
rgba(worlds[7][24:96,32:96]).resize((512,576),Image.Resampling.NEAREST).save(R/'body_reference.png')
print(R)
