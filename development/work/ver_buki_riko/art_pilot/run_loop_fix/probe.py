from pathlib import Path
import sys,json,struct
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT))
import numpy as np
from PIL import Image,ImageDraw
from scripts.repack_zero import read_inputs
from scripts.extract_zero import save_image
from src.psx_player import graphics_bank,composition_frame,decode_stream
from src.psx_frame_edit import frame_coverage
P=Path(__file__).parent;B=ROOT/'out/ver_buki_riko/riko_motion_20261023T140114425399Z'
_,_,_,_,gfx,parts,_=read_inputs(ROOT/'work/ver_buki_riko/zero_extract/20261023T062408235550Z')
bank=graphics_bank(gfx,0)
ref=ROOT/'out/ver_buki_riko/riko_pilot_20261023T082720987715Z/riko_idle147_indexed.png'
words=struct.unpack('<16H',ref.with_name('candidate_palette.bin').read_bytes());colors=np.array([[(w&31)*255//31,((w>>5)&31)*255//31,((w>>10)&31)*255//31] for w in words[1:]],dtype=int)
world={};geometry={}
for n in range(7,21):
 f=bank['frames'][n];c=composition_frame(parts,0,n);raw=decode_stream(gfx,f['offset'],f['limit'],f['tile_count']*128).data
 cov,size,b=frame_coverage(raw,f['tile_count'],c);safe=np.array([len(q)==1 for q in cov]).reshape(size[1],size[0])
 for part in c['parts']:
  if part['tile']%16==0:safe[part['y']-b[1]:part['y']-b[1]+16,part['x']-b[0]]=False
 geometry[n]=(size,b,safe)
 w=np.zeros((72,96),dtype=np.uint8);w[40+b[1]:40+b[3],48+b[0]:48+b[2]]=np.array(Image.open(B/f'frame_{n:03d}.png'));world[n]=w
after={n:a.copy() for n,a in world.items()}
for n,anchor,cell,name,px,dx in [(12,11,0,'midswing_v1.png',.5,1),(13,14,0,'precontact_v1.png',0,1),(19,18,1,'midswing_v1.png',.5,1),(20,7,1,'precontact_v1.png',.5,2)]:
 im=Image.open(P/name).convert('RGBA');a=np.array(im);xs=((np.arange(128)+px)*im.width/128).astype(int);ys=((np.arange(72)+.5)*im.height/72).astype(int);a=a[ys[:,None],xs[None,:]][:,cell*64:(cell+1)*64]
 visible=a[:,:,3]>=128;idx=np.zeros((72,64),dtype=np.uint8);idx[visible]=np.argmin(((a[:,:,:3][visible].astype(int)[:,None]-colors[None])**2).sum(2),axis=1)+1
 w=world[anchor].copy();w[48:64,32:48]=idx[48:64,16-dx:32-dx]
 size,b,safe=geometry[n];canvas=w[40+b[1]:40+b[3],48+b[0]:48+b[2]]
 print(n,'outside',np.argwhere((canvas!=0)&~safe).tolist(),'front bottom',int(np.nonzero(w[:,32:48])[0].max())-40)
 after[n]=w;save_image(canvas.tobytes(),size,words,P/f'probe_{n:03d}.png')
board=Image.new('RGBA',(256*6,320*2),(42,45,54,255));draw=ImageDraw.Draw(board)
for row,seq in enumerate(([11,12,13,14,15,16],[18,19,20,7,8,9])):
 for j,n in enumerate(seq):
  a=after[n][:,16:80];visible=a!=0;rgb=np.zeros((*a.shape,4),dtype=np.uint8);rgb[visible,:3]=colors[a[visible]-1];rgb[visible,3]=255
  im=Image.fromarray(rgb);board.alpha_composite(im.resize((256,288),Image.Resampling.NEAREST),(j*256,32+row*320));draw.text((j*256+4,row*320+4),str(n),fill='white')
board.save(P/'probe_boundaries.png')
