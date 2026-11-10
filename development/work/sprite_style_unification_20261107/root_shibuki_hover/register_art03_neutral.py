from pathlib import Path
import sys,json,hashlib
import numpy as np
from PIL import Image
from scipy.ndimage import label
D=Path(__file__).resolve().parent;W=D.parent;ROOT=W.parents[1];sys.path[:0]=[str(D),str(ROOT),str(W/'nana_audit/native_restore')]
from register_neutral import quantize
from scripts.export_x_consistency import Archive
from preview_restore import helper
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
src=D/'art03_generated.png';assert sha(src)=='bc4a4b451847205c861b0d665e5439a104efd8fd15d18bc3b336ef4ebf139c60'
p=W/'shibuki_audit/prepared_nova_strike_base01/PL00_U.ARC';assert sha(p)=='36d4d0293abc77052c476e0495f4f4542ca75471c7a149f200e4bdb8f4e1bd4e';a=Archive(p.read_bytes());im=Image.open(src).convert('RGBA');assert im.width==2*im.height
out=D/'registered_neutral03';out.mkdir(exist_ok=False);rows=[];frames=[]
for col,mask in enumerate((8,15)):
    start=0 if mask==8 else 16;form='base_legs'if mask==8 else'fourth';box=(col*im.width//2,0,(col+1)*im.width//2,im.height);pal=np.array([[((int(w)>>s)&31)*255//31 for s in(0,5,10)]for w in a.words[start:start+16]],np.float32)
    cols=[('idle',a.composite(0,mask)[0]),('current229',a.composite(229,mask)[0])]
    for method in('vote','nearest'):
        z=np.zeros((384,384),np.uint8);z[112:208,112:208]=quantize(im.crop(box),pal,method);pic=a.rgba(z,start);Image.fromarray(z).save(out/f'{form}_229_{method}_indices.png');pic.save(out/f'{form}_229_{method}_rgba.png');cols.append((method,pic));frames.append({'ref':229,'mask':mask,'method':method,'bbox':pic.getbbox(),'old_bbox':a.composite(229,mask)[0].getbbox(),'components8':int(label(z>0,np.ones((3,3)))[1]),'body_translation':[0,0],'bbox_rescale':False,'indices_sha256':hashlib.sha256(z.tobytes()).hexdigest()})
    rows.append((form,cols))
helper.grid(rows,out/'comparison.png',5)
(out/'manifest.json').write_text(json.dumps({'source_sha256':sha(src),'parent_sha256':sha(p),'fixed_cell':[96,96],'source_size':list(im.size),'frames':frames,'native_packed':False,'runtime_verified':False},indent=2)+'\n','utf8');print(json.dumps(frames))
