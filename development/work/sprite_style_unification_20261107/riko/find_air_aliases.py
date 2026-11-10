"""동일한 실제 본체만 찾아 새 의상 키의 공유 범위를 기록한다."""
from pathlib import Path
import sys,json,hashlib
import numpy as np
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT))
from scripts.overhaul_sprites_audit import render
from scripts.prepare_riko_ui import entry
from src.psx_player import graphics_bank
W=ROOT/'work/sprite_style_unification_20261107'
arc=(W/'zero_audit/riko_restore/prepared_cloth_v1/PL01_U.ARC').read_bytes()
def cropped(a):
    yy,xx=np.nonzero(a)
    if not len(xx):return b'',(0,0),(0,0)
    box=(int(xx.min()),int(yy.min()),int(xx.max())+1,int(yy.max())+1)
    crop=a[box[1]:box[3],box[0]:box[2]]
    return crop.tobytes(),crop.shape,box[:2]
keys={n:cropped(render(arc,0,0,n)[0]) for n in (21,39,49,229)}
rows=[]
for b in (0,1):
    bank=graphics_bank(entry(arc,2),b)
    for f in bank['frames']:
        n=f['index']
        if b==1 and 42<=n<=49:continue
        data,shape,origin=cropped(render(arc,b,b*5,n)[0])
        for master,(pixels,size,anchor) in keys.items():
            if data==pixels and shape==size:
                rows.append({'bank':b,'ref':n,'master':master,'translation':[origin[0]-anchor[0],origin[1]-anchor[1]]})
out=W/'riko/air_wall_cloth01/aliases.json'
out.write_text(json.dumps({'source_sha256':hashlib.sha256(arc).hexdigest(),'matches':rows},indent=2)+'\n','utf8')
print(json.dumps(rows))
