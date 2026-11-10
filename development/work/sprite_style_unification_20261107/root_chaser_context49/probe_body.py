from pathlib import Path
import gzip, hashlib, json, struct
import numpy as np
from PIL import Image, ImageDraw

O=Path(__file__).resolve().parent
ROOT=O.parents[2]
P=ROOT/'work/overhaul_20261105/runtime/riko_chaser_fresh_state/SLUS_005.61.000'
b=P.read_bytes(); assert hashlib.sha256(b).hexdigest()=='d392bf6b3d9421512b867985b3f0b44bd0958dc0d3f2a4eda7e1d33f4f2274d7'
s=gzip.decompress(b); r=s[442:442+2097152]
v=np.frombuffer(s,dtype='<u2',count=524288,offset=2569183).reshape(512,1024)
cp=struct.unpack_from('<I',r,0x173a30+0x3c)[0]&0x1fffff
assert cp==0x1ba31c
def draw(n,bx,by,clut=0x784a):
    h=struct.unpack_from('<I',r,cp+n*4)[0]
    ps=[struct.unpack_from('<BBbb',r,cp+(h>>16)*4+i*4) for i in range(h&65535)]
    a=np.zeros((128,128,4),np.uint8)
    for fl,t,x,y in ps:
        row=clut+((fl>>2)&3)
        words=v[row>>6,(row&63)*16:(row&63)*16+16]
        pal=np.array([[((int(w)>>z)&31)*255//31 for z in (0,5,10)]+[255 if i else 0] for i,w in enumerate(words)],np.uint8)
        xx=bx+(t%16)*4; yy=by+(t//16)*16
        tile=v[yy:yy+16,xx:xx+4]
        ix=np.stack([(tile>>z)&15 for z in (0,4,8,12)],axis=2).reshape(16,16)
        q=pal[ix]
        if fl&64:q=q[:,::-1]
        if fl&128:q=q[::-1]
        dst=a[64+y:80+y,64+x:80+x];mask=q[:,:,3]>0;dst[mask]=q[mask]
    return Image.fromarray(a)

if __name__=='__main__':
    out=Image.new('RGB',(1024,800),'#26313f');d=ImageDraw.Draw(out)
    for i,(x,y) in enumerate([(384,0),(448,0),(512,0),(576,0),(640,0),(704,0),(768,0),(832,0),(384,256),(448,256),(512,256),(576,256)]):
        q=draw(0,x,y).resize((256,256),Image.Resampling.NEAREST)
        dx,dy=(i%4)*256,(i//4)*266
        out.paste(q,(dx,dy+10),q);d.text((dx+4,dy),f'VRAM {x},{y}',fill='white')
    out.save(O/'body_pages_probe.png')
    print(json.dumps({'state_sha256':hashlib.sha256(b).hexdigest(),'body_parts':hex(cp),'image':'body_pages_probe.png'}))
