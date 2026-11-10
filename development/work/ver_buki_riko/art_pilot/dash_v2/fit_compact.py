import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent.parent/'dash_v1'))
from fit_dash import *
D=Path(__file__).resolve().parent
im=Image.open(D/'generated_compact.png');worlds={};records={};scale=.105
for i,n in enumerate((44,45,46)):
 cell=im.crop((round(i*im.width/3),0,round((i+1)*im.width/3),im.height));safe=geometry[n][2];choices=[]
 for phase in (.5,.25,.75,.125,.875):
  s,hl=normalize(cell,scale,phase);h,w=s.shape
  target={44:(-17,-21),45:(-22,-17),46:(-22,-13)}[n];tx,ty=target[0]-hl[0],24-h
  for x in range(tx-8,tx+9):
   for y in range(ty-5,ty+5):
    bad=int(((s!=0)&~safe[64+y:64+y+h,64+x:64+x+w]).sum());headbad=int((hm&~safe[64+y+hl[1]:64+y+hl[1]+19,64+x+hl[0]:64+x+hl[0]+23]).sum())
    cost=bad*1000+headbad*100000+abs(x-tx)*3+abs(y+h-24)*15+abs(phase-.5)
    choices.append((cost,bad,x,y,phase,s,hl))
 _,bad,x,y,phase,s,hl=min(choices,key=lambda q:q[0]);h,w=s.shape;world=np.zeros((128,128),dtype=np.uint8);world[64+y:64+y+h,64+x:64+x+w]=s;worlds[n]=world
 records[str(n)]={'frame':n,'source':'generated_compact.png','source_scale':scale,'phase':phase,'origin':[x,y],'head_world':[x+hl[0],y+hl[1]],'size':[w,h],'outside':bad,'components':[len(g) for g in component(world!=0)],'bad_world':[[int(xx-64),int(yy-64)] for yy,xx in np.argwhere((world!=0)&~safe)]}
board=Image.new('RGBA',(3*384,340),(40,43,55,255));draw=ImageDraw.Draw(board)
for i,(n,w) in enumerate(worlds.items()):
 board.alpha_composite(rgba(w[24:104,16:112]).resize((384,320),Image.Resampling.NEAREST),(i*384,20));draw.text((i*384+4,4),str(n),fill='white')
board.save(D/'fit_review.png');np.savez(D/'worlds_probe.npz',**{str(n):w for n,w in worlds.items()});(D/'fit_registration.json').write_text(json.dumps(records,indent=2),encoding='utf8');print(json.dumps(records))
