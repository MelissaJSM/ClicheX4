from pathlib import Path
import sys,json
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT))
from work.ver_buki_riko.art_pilot.ladder_v1.fit_ladder import sample,normalize,front,component
from work.ver_buki_riko.art_pilot.wall_saber_v1.fit_wall import original,rgba,pal
D=Path(__file__).parent;B=ROOT/'out/ver_buki_riko/riko_bank1_20261025T172453977111Z'
im=Image.open(D/'generated_corrected.png');scale=float(sys.argv[1]) if len(sys.argv)>1 else .095
a=np.array(im);xx=np.flatnonzero(np.any(a[:,:,3]>=220,axis=0));spans=[g for g in np.split(xx,np.where(np.diff(xx)>1)[0]+1) if len(g)>10]
if len(spans)!=5:raise ValueError(('Need five separated sprites',len(spans)))
worlds={};regs=[]
idle=np.array(Image.open(B/'idle_147.png'));w=np.zeros((192,192),np.uint8);w[72:120,72:128]=idle;worlds['0']=w
old=json.loads((D.parent/'beam_in_v2/motion_set.json').read_text())
mask=front!=0
hits=[(x,y) for y in range(idle.shape[0]-18) for x in range(idle.shape[1]-22) if np.array_equal(idle[y:y+19,x:x+23][mask],front[mask])]
if len(hits)!=1:raise ValueError('Idle native head registration is not unique')
regs.append({'frame':0,'head_world':[hits[0][0]-24,hits[0][1]-24],'view':'front','outside':0,'floor':23})
for n,i in [(1,0),(2,0),(3,1),(4,2),(5,3),(6,4)]:
    source=Image.open(D/'generated_gesture.png') if n>=5 else im
    ax=np.array(source);sx=np.flatnonzero(np.any(ax[:,:,3]>=220,axis=0));ranges=[g for g in np.split(sx,np.where(np.diff(sx)>1)[0]+1) if len(g)>10]
    g=ranges[i];cell=source.crop((int(g[0])-2,0,int(g[-1])+3,source.height))
    head=front if n==1 else np.fliplr(front)
    a,hp=normalize(sample(cell,scale),head);a[:hp[1]]=0
    for group in component(a!=0)[1:]:
        if len(group)>3:raise ValueError(('Detached',n,len(group)))
        for y,x in group:a[y,x]=0
    ys,xs=np.nonzero(a);floor=int(ys.max());feet=np.flatnonzero(np.any(a[floor-2:floor+1]!=0,axis=0))
    groups=np.split(feet,np.where(np.diff(feet)>1)[0]+1)
    center=np.mean([(g[0]+g[-1])/2 for g in groups]);x=round(1.25-center);y=23-floor
    if n==1:x+=1  # Avoid this frame's original U=0 seam, still within .5px of idle center.
    w=np.zeros((192,192),np.uint8);w[96+y:96+y+a.shape[0],96+x:96+x+a.shape[1]]=a
    safe=original(n)[2];outside=int(np.count_nonzero((w!=0)&~safe));worlds[str(n)]=w
    regs.append({'frame':n,'head_world':[x+hp[0],y+hp[1]],'view':'front' if n==1 else 'front_mirrored','outside':outside,'floor':23,'foot_center':float(center+x),'height':int(ys.max()-ys.min()+1),'opaque_pixels':int(np.count_nonzero(a)),'scale':scale,'foot_groups':len(groups)})
board=Image.new('RGBA',(7*240,300),(32,36,48));draw=ImageDraw.Draw(board)
for i,(key,w) in enumerate(worlds.items()):
    board.alpha_composite(rgba(w).crop((56,48,136,138)).resize((240,270),Image.Resampling.NEAREST),(i*240,25));draw.text((i*240+5,5),key+' STATIC',fill='white')
board.save(D/'key_review.png');np.savez(D/'key_worlds.npz',**worlds);(D/'key_registration.json').write_text(json.dumps(regs,indent=2),'utf8');print(json.dumps(regs))
