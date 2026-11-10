import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent.parent/'dash_v1'))
from fit_dash import *
import shutil
from scripts.build_riko_idle import patch_frames,check_motion_scale
from scripts.discover_inputs import sha256
D=Path(__file__).resolve().parent;old=D.parent/'dash_v1';base=D.parent/'scale_consistency/walk_design_basis'
recipe=json.loads((old/'recipe.json').read_text('utf8'))
worlds={int(k):w.copy() for k,w in np.load(old/'final_worlds.npz').items()};records=json.loads((old/'final_registration.json').read_text('utf8'))
worlds[45]=np.load(D/'worlds_probe.npz')['45'];records['45']=json.loads((D/'fit_registration.json').read_text('utf8'))['45']
im=Image.open(D/'generated_fit.png');sourcelist=[]
for i in range(3):
 cell=im.crop((round(i*im.width/3),0,round((i+1)*im.width/3),im.height));s,hl=normalize(cell,240/im.width,chosen_phase if i else .5,head_registration_y=1);h,w=s.shape
 if i==0:
  safe=geometry[46][2];choices=[]
  for phase in (.5,.25,.75,.125,.875,.375,.625):
   s,hl=normalize(cell,240/im.width,phase,head_registration_y=1);h,w=s.shape;tx,ty=-22-hl[0],24-h
   for x in range(tx-6,tx+7):
    for y in range(ty-5,ty+5):
     bad=int(((s!=0)&~safe[64+y:64+y+h,64+x:64+x+w]).sum());hb=int((hm&~safe[64+y+hl[1]:64+y+hl[1]+19,64+x+hl[0]:64+x+hl[0]+23]).sum())
     choices.append((1000*bad+100000*hb+abs(x-tx)*3+abs(y+h-24)*15+abs(phase-.5),bad,x,y,s,hl,phase))
  _,bad,x,y,s,hl,chosen_phase=min(choices,key=lambda q:q[0]);h,w=s.shape;headpos=[x+hl[0],y+hl[1]]
  records['46']={'frame':46,'source':'generated_fit.png','scale':240/im.width,'phase':chosen_phase,'origin':[x,y],'head_world':headpos,'head_registration_y':1,'outside':bad}
 else:x,y=headpos[0]-hl[0],headpos[1]-hl[1]
 world=np.zeros((128,128),dtype=np.uint8);world[64+y:64+y+h,64+x:64+x+w]=s;sourcelist.append(world)
worlds[46]=sourcelist[0];cape_records=[]
for i,n in ((1,47),(2,48)):
 w=worlds[46].copy();w[58:74,71:96]=sourcelist[i][58:74,71:96];worlds[n]=w;records[str(n)]={**records['46'],'frame':n}
 cape_records.append({'frame':n,'changed_pixels':int((w!=worlds[46]).sum()),'body_outside_cape_exact':True,'cape_world_rectangle':[7,-6,32,10]})
records['52']={**records['51'],'frame':52,'head_world':[records['51']['head_world'][0]-1,records['51']['head_world'][1]]}
checks=[];frames={}
for n,world in sorted(worlds.items()):
 size,b,safe=geometry[n];outside=int(((world!=0)&~safe).sum());groups=component(world!=0)
 print(n,'outside',outside,'components',[len(g) for g in groups])
 if outside or len(groups)!=1:
  print('bad',[[int(x-64),int(y-64)] for y,x in np.argwhere((world!=0)&~safe)]);raise ValueError('Unfitted compact pose')
 canvas=world[64+b[1]:64+b[3],64+b[0]:64+b[2]];frames[n]=(canvas.tobytes(),size);save_image(*frames[n],words,D/f'frame_{n:03}.png');path=D/f'frame_{n:03}.png'
 recipe['frames'][str(n)]={'file':path.name,'sha256':sha256(path.read_bytes())};recipe['body_standard']['head_world_positions'][str(n)]=records[str(n)]['head_world']
 yy,xx=np.nonzero(world);checks.append({'frame':n,'outside_pixels':outside,'components':len(groups),'opaque_pixels':len(xx),'opaque_bounds':[int(xx.min()-64),int(yy.min()-64),int(xx.max()+1-64),int(yy.max()+1-64)],'head_world':records[str(n)]['head_world']})
for key,r in recipe['frames'].items():
 if int(key) in worlds:continue
 src=base/r['file'];dest=D/r['file'];shutil.copyfile(src,dest);frames[int(key)]=read_indexed_png(dest,words)
 if sha256(dest.read_bytes())!=r['sha256']:raise ValueError('Existing approved frame changed')
reference=read_indexed_png(ROOT/'out/ver_buki_riko/riko_pilot_20261023T082720987715Z/riko_idle147_indexed.png',words)
scale_check=check_motion_scale(recipe,frames,gfx,parts,reference);_,compression=patch_frames(arc,gmeta,gfx,parts,frames,pal)
recipe['dash_production']['rejected_predecessor_sha256']='f93eb92c25f0985279150f7b9a75f06741a48e1010dd4d80579800fa63d1f6d1'
recipe['dash_production']['revision']='Compact torso with bent knees; no horizontal body stretching'
(D/'recipe.json').write_text(json.dumps(recipe,indent=2),encoding='utf8');(D/'design_checks.json').write_text(json.dumps({'frames':checks,'cape_variations':cape_records,'scale_check':scale_check,'compression':compression['compression'],'registration':records},indent=2),encoding='utf8');np.savez(D/'final_worlds.npz',**{str(n):w for n,w in worlds.items()})
board=Image.new('RGBA',(5*320,2*340),(40,43,55,255));draw=ImageDraw.Draw(board)
for i,n in enumerate(range(44,53)):
 board.alpha_composite(rgba(worlds[n][24:104,24:104]).resize((320,320),Image.Resampling.NEAREST),(i%5*320,i//5*340+20));draw.text((i%5*320+4,i//5*340+4),str(n),fill='white')
board.save(D/'dash_sheet_4x.png')
print(json.dumps({'frames':checks,'cape':cape_records,'new_compression':[r for r in compression['compression'] if min(r['frames'])>=44]}))
