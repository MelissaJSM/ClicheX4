from pathlib import Path
import json,sys
import numpy as np
from PIL import Image, ImageDraw
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT))
from work.ver_buki_riko.art_pilot.ladder_v1.fit_ladder import sample,normalize,front,component,geometry,rgba,pal
from scripts.extract_zero import save_image
D=Path(__file__).parent
im=Image.open(D/'generated_keys.png');scale=float(sys.argv[1]) if len(sys.argv)>1 else .083
board=Image.new('RGBA',(1200,450),(32,36,48));draw=ImageDraw.Draw(board);records=[];keys={}
for i,n in enumerate([251,252,253]):
    cell=im.crop((round(i*im.width/3),0,round((i+1)*im.width/3),im.height))
    a,hp=normalize(sample(cell,scale),front)
    groups=component(a!=0)
    for group in groups[1:]:
        if len(group)>3:raise ValueError(('Detached key',n,[len(g) for g in groups]))
        for y,x in group:a[y,x]=0
    h,w=a.shape;safe=geometry(n)[2];options=[]
    for y in range(-38,0):
        for x in range(-25,5):
            outside=int(np.count_nonzero((a!=0)&~safe[96+y:96+y+h,96+x:96+x+w]))
            options.append((outside*100000+abs(y+h-24)*100+abs(x+hp[0]+11),outside,x,y))
    _,outside,x,y=min(options)
    keys[str(n)]=a;save_image(a.tobytes(),(w,h),pal,D/f'key_{n:03d}.png')
    records.append({'frame':n,'position':[x,y],'head_local':hp,'head_world':[x+hp[0],y+hp[1]],'size':[w,h],'floor':y+h-1,'outside':outside,'body_pixels':int(np.count_nonzero(a))-309,'scale':scale})
    board.alpha_composite(rgba(a).resize((w*7,h*7),Image.Resampling.NEAREST),(400*i+15,40))
    draw.text((400*i+10,10),str(n)+' body '+str(records[-1]['body_pixels'])+' outside '+str(outside),fill='white')
board.save(D/'key_review.png');np.savez(D/'key_pixels.npz',**keys)
(D/'key_registration.json').write_text(json.dumps(records,indent=2),'utf8');print(json.dumps(records))
