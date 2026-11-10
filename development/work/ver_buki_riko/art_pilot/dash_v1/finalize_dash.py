from fit_dash import *
import hashlib,shutil
from scripts.build_riko_idle import patch_frames
from src.psx_frame_edit import edit_frame_set
from src.psx_player import compose_indices
base=ROOT/'work/ver_buki_riko/art_pilot/scale_consistency/walk_design_basis'
old=np.load(D/'worlds_edit.npz');worlds={n:old[str(n)].copy() for n in (44,45)}
records={r['frame']:r for r in json.loads((D/'fit_edit.json').read_text()) if r['frame'] in (44,45)}
im=Image.open(D/'generated_fit.png');scale=1/7.2
for i,n in enumerate((46,49,50,51)):
 cell=im.crop((i%2*im.width//2,i//2*im.height//2,(i%2+1)*im.width//2,(i//2+1)*im.height//2));safe=geometry[n][2];choices=[]
 for phase in (.5,.25,.75,.125,.875,.375,.625):
  s,hl=normalize(cell,scale,phase,head_registration_x=1 if n==50 else 0);h,w=s.shape
  target={46:(-26,-12),49:(-11,-18),50:(-9,-24),51:(-14,-22)}[n];tx,ty=target[0]-hl[0],24-h
  for x in range(tx-6,tx+7):
   for y in range(ty-3,ty+5):
    bad=int(((s!=0)&~safe[64+y:64+y+h,64+x:64+x+w]).sum());headbad=int((hm&~safe[64+y+hl[1]:64+y+hl[1]+19,64+x+hl[0]:64+x+hl[0]+23]).sum())
    cost=bad*1000+headbad*100000+abs(x-tx)*3+abs(y+h-24)*15+abs(phase-.5)
    choices.append((cost,bad,x,y,phase,s,hl))
 _,bad,x,y,phase,s,hl=min(choices,key=lambda q:q[0]);h,w=s.shape;world=np.zeros((128,128),dtype=np.uint8);world[64+y:64+y+h,64+x:64+x+w]=s;worlds[n]=world
 records[n]={'frame':n,'source':'generated_fit.png','source_scale':scale,'phase':phase,'origin':[x,y],'head_world':[x+hl[0],y+hl[1]],'size':[w,h],'outside':bad,'components':[len(g) for g in component(world!=0)],'bad_world':[[int(xx-64),int(yy-64)] for yy,xx in np.argwhere((world!=0)&~safe)]}
print(json.dumps(records));np.savez(D/'worlds_final_probe.npz',**{str(n):w for n,w in worlds.items()});(D/'final_registration.json').write_text(json.dumps(records,indent=2),encoding='utf8')
board=Image.new('RGBA',(3*384,2*340),(40,43,55,255));draw=ImageDraw.Draw(board)
for i,(n,w) in enumerate(worlds.items()):
 board.alpha_composite(rgba(w[24:104,16:112]).resize((384,320),Image.Resampling.NEAREST),(i%3*384,i//3*340+20));draw.text((i%3*384+4,i//3*340+4),str(n),fill='white')
board.save(D/'final_probe.png')
