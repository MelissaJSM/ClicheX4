from pathlib import Path
import sys,json
import numpy as np
from PIL import Image
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from scripts.export_x_consistency import Archive
a=Archive((H/'prepared_ultimate_lowhp01/PL02_U.ARC').read_bytes())
def tip(q):
    y,x=np.nonzero(q);xmin=x.min();return [int(xmin),float(y[x<=xmin+1].mean()),int(y.min()),int(y.max())]
for n in range(56,67,2):
    for form,mask in(('before',15),('after',0)):
        q=np.array(Image.open(H/'ultimate_wall_shots_native02'/form/f'{n:03}_authored.png'))[142:161,128:147]
        was=np.array(a.composite(n,mask)[0])[142:161,128:147,3]
        print(n,form,tip(q),tip(was))
