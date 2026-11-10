from pathlib import Path
import sys,json
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[4];D=Path(__file__).parent;N=D.parent
sys.path[:0]=[str(ROOT),str(N/'native_restore')]
from preview_restore import Archive,digest,write
a=Archive((N/'native_restore/nova_sync_v1/PL02_U.ARC').read_bytes());out=D/'skin_closeup_inputs_v1';out.mkdir(exist_ok=False)
page=Image.new('RGBA',(1024,512));records=[]
for i,n in enumerate((39,47)):
    src=D/f'skin_edge_registered_v1/before_{n:03}.png';v=np.array(Image.open(src));box=(148,158,180,186)
    im=a.rgba(v,16).crop(box).resize((512,448),Image.Resampling.NEAREST);page.alpha_composite(im,(i*512,32))
    records.append({'ref':n,'native_world_window':[-12,-2,20,26],'cell_origin':[i*512,32],'scale':16,'input_sha256':digest(src)})
page.save(out/'two_legs.png');write(out/'manifest.json',{'frames':records,'image_sha256':digest(out/'two_legs.png'),'purpose':'same native leg shape and source-authored local skin-edge recoloring; no gamewrite'})
