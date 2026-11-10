from pathlib import Path
import json,struct
import numpy as np
from PIL import Image
P=Path(__file__).parent;root=P.parents[3]
pal=(root/'out/ver_buki_riko/riko_pilot_20261023T082720987715Z/candidate_palette.bin').read_bytes();words=struct.unpack('<16H',pal)
colors=np.array([[(w&31)*255//31,((w>>5)&31)*255//31,((w>>10)&31)*255//31] for w in words[1:]],dtype=np.int32)
im=Image.open(P/'generated_compact_v1.png').convert('RGBA');a=np.array(im)
xs=((np.arange(192)+.5)*im.width/192).astype(int);ys=((np.arange(72)+.5)*im.height/72).astype(int)
sample=a[ys[:,None],xs[None,:]];mask=sample[:,:,3]>=128;idx=np.zeros((72,192),dtype=np.uint8);idx[mask]=np.argmin(((sample[:,:,:3][mask].astype(np.int32)[:,None]-colors[None])**2).sum(2),axis=1)+1
for cell,(kind,key,roi) in enumerate([('run',1,(18,20,31,34)),('run',7,(18,20,31,34)),('jump',2,(18,32,33,51))]):
 orig=Image.open(P/f'probe_{kind}_{key:02d}.png');b=np.array(orig);h,w=b.shape;x0,y0,x1,y1=roi
 b[y0:y1,x0:x1]=idx[64-h+y0:64-h+y1,cell*64+12+x0:cell*64+12+x1]
 changed=Image.fromarray(b);changed.putpalette(orig.getpalette());changed.info['transparency']=0;changed.save(P/f'compact_{kind}_{key:02d}.png')
 print(kind,key,'roi',roi)

orig=Image.open(P/"probe_run_10.png");b=np.array(orig);h,w=b.shape
b[20:34,18:32]=idx[64-h+20:64-h+34,12+18:12+32]
changed=Image.fromarray(b);changed.putpalette(orig.getpalette());changed.info["transparency"]=0;changed.save(P/"compact_run_10.png")

orig=Image.open(P/"probe_run_00.png");b=np.array(orig);h,w=b.shape
b[20:34,18:34]=idx[64-h+20:64-h+34,12+18:12+34]
changed=Image.fromarray(b);changed.putpalette(orig.getpalette());changed.info["transparency"]=0;changed.save(P/"compact_run_00.png")
