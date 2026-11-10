import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent.parent/'dash_v1'))
from fit_dash import *
D=Path(__file__).resolve().parent
old=np.load(D.parent/'dash_v2/final_worlds.npz')['46']
im=Image.open(D/'generated_cape.png'); worlds={}; board=Image.new('RGBA',(1200,400),(40,43,55,255))
for i in range(3):
 cell=im.crop((round(i*im.width/3),0,round((i+1)*im.width/3),im.height))
 s,hl=normalize(cell,240/im.width,.5,head_registration_y=1)
 x,y=-22-hl[0],-13-hl[1];h,w=s.shape
 world=np.zeros((128,128),dtype=np.uint8);world[64+y:64+y+h,64+x:64+x+w]=s;worlds[str(46+i)]=world
 board.alpha_composite(rgba(world[38:102,32:96]).resize((400,400),Image.Resampling.NEAREST),(i*400,0))
 print(46+i,im.size,(x,y),(w,h))
np.savez(D/'source_worlds.npz',**worlds);board.save(D/'normalized_review.png')
