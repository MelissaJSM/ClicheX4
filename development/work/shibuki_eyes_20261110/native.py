import json,struct,sys
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from src.steam_arc import SteamArc
D=Path(__file__).parent
def decode(r,a=None):
    a=a or SteamArc((D/'before'/r['target']).read_bytes())
    data=a.by_key[tuple(r['texture_key'])].payload
    w,h=r['size'];px=np.zeros((h,w),np.uint8);owner=np.full((h,w),-1,np.int32)
    for flags,t,x,y in struct.iter_unpack('<BBbb',bytes.fromhex(r['record_hex'])):
        tid=(flags&3)*256+t;tx=tid%16*16;ty=tid//16*16+r['yoffset']
        for dy in range(16):
            for dx in range(16):
                pos=20+(ty+(15-dy if flags&128 else dy))*256+tx+(15-dx if flags&64 else dx)
                value=data[pos];xx=x-r['bounds'][0]+dx;yy=y-r['bounds'][1]+dy
                if value: px[yy,xx]=value;owner[yy,xx]=pos
    return px,owner
def world(r):
    px,owner=decode(r);out=np.zeros((160,160),np.uint8)
    x0,y0,x1,y1=[80+q for q in r['bounds']];out[y0:y1,x0:x1]=px
    return out
if __name__=='__main__':
    rs=json.loads((D/'records.json').read_text())
    for kind in ('select','dialogue','pause'):
        r=next(r for r in rs if r['kind']==kind);p,_=decode(r)
        print(kind,r['size'],'warm candidates',[(int(x),int(y),int(p[y,x]))for y,x in np.argwhere(np.isin(p,[9,10,14])) if y<p.shape[0]*.7 and 20<x<p.shape[1]*.85][:100])
    from PIL import Image,ImageDraw
    names=['cliche_br_st0d_0x.arc','cliche_br_hqx_15.arc','cliche_br_hqx_16.arc','cliche_br_hqx_17.arc']
    board=Image.new('RGB',(1200,1000),'#252d40');d=ImageDraw.Draw(board)
    for i,target in enumerate(names):
        for j,f in enumerate((0,3,6,9)):
            r=next(r for r in rs if r['target']==target and r['kind']=='hq' and r['frame']==f);p=world(r)
            a=SteamArc((D/'before'/target).read_bytes());words=struct.unpack_from('<16H',a.by_key[tuple(r['palette_key'])].payload,12+r['row']*32)
            colors=np.array([[(v>>s&31)*255//31 for s in (0,5,10)]+[255 if k else 0]for k,v in enumerate(words)],np.uint8)
            crop=Image.fromarray(colors[p]).crop((60,40,110,75)).resize((300,210),Image.Resampling.NEAREST)
            board.paste(crop,(j*300,i*250+25),crop);d.text((j*300,i*250),target+' '+str(f),fill='white')
            print(target,f,'warm face',[(int(x),int(y),int(p[y,x]))for y,x in np.argwhere(np.isin(p,[9,10,14])) if 47<=y<63 and 70<x<105])
    board.save(D/'hq_faces.png')
