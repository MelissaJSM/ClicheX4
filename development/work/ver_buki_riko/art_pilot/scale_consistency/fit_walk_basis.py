from pathlib import Path
P=Path(__file__).parent
exec((P/'fit_probe.py').read_text(encoding='utf-8').split('run_slots=')[0])
import hashlib,shutil
from collections import deque
D=P/'walk_design_basis';B=ROOT/'out/ver_buki_riko/riko_motion_20261023T210015989110Z'
recipe=json.loads((P/'idle_style_match/recipe.json').read_text(encoding='utf-8'))
head=np.array(Image.open(master))[:19,12:35];hm=head!=0
hc=np.zeros((*head.shape,3),dtype=int);hc[hm]=colors[head[hm]-1]
hg=(hc[:,:,1]>hc[:,:,0]+8)&(hc[:,:,1]>hc[:,:,2]+8)&hm;hgy,hgx=np.nonzero(hg)
for n in [0,1,2,5,6,146,147,148]:
    f=bank['frames'][n];c=composition_frame(parts,0,n);raw=decode_stream(gfx,f['offset'],f['limit'],f['tile_count']*128).data;coverage,size,b=frame_coverage(raw,f['tile_count'],c)
    safe=np.array([len(v)==1 for v in coverage]).reshape(size[1],size[0])
    for p in c['parts']:
        if p['tile']%16==0:safe[p['y']-b[1]:p['y']-b[1]+16,p['x']-b[0]]=False
    w=np.zeros((128,128),dtype=bool);w[64+b[1]:64+b[3],64+b[0]:64+b[2]]=safe;geometry[n]=(size,b,w)
def component(a):
    unseen=set(map(tuple,np.argwhere(a)));groups=[]
    while unseen:
        seed=unseen.pop();q=deque([seed]);g=[seed]
        while q:
            y,x=q.popleft()
            for dy,dx in [(-1,-1),(-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0),(1,1)]:
                v=(y+dy,x+dx)
                if v in unseen:unseen.remove(v);q.append(v);g.append(v)
        groups.append(g)
    return sorted(groups,key=len,reverse=True)
def normalize(cell,scale):
    a=np.array(cell.convert('RGBA'));groups=component(a[:,:,3]>=180);keep=np.zeros(a.shape[:2],dtype=bool)
    for y,x in groups[0]:keep[y,x]=True
    a[~keep,3]=0;yy,xx=np.nonzero(keep);a=a[yy.min():yy.max()+1,xx.min():xx.max()+1]
    h,w=[math.ceil(v*scale) for v in a.shape[:2]];xs=np.minimum(((np.arange(w)+.5)/scale).astype(int),a.shape[1]-1);ys=np.minimum(((np.arange(h)+.5)/scale).astype(int),a.shape[0]-1);a=a[ys[:,None],xs[None,:]]
    mask=a[:,:,3]>=180;rgb=a[:,:,:3].astype(np.int32);ix=np.zeros((h,w),dtype=np.uint8);ix[mask]=np.argmin(((rgb[mask,None]-colors[None])**2).sum(2),1)+1
    green=(rgb[:,:,1]>rgb[:,:,0]+8)&(rgb[:,:,1]>rgb[:,:,2]+8)&mask&(np.indices(ix.shape)[0]<h*.45);gy,gx=np.nonzero(green)
    hx=round(float(gx.mean()-hgx.mean()));hy=0
    s=np.zeros((112,112),dtype=np.uint8);s[24:24+h,24:24+w]=ix
    s[:24+18,24+hx-2:24+hx+25]=0;sub=s[24:43,24+hx:24+hx+23];sub[hm]=head[hm]
    yy,xx=np.nonzero(s);x0,y0,x1,y1=int(xx.min()),int(yy.min()),int(xx.max()+1),int(yy.max()+1)
    return s[y0:y1,x0:x1],[24+hx-x0,24-y0]
worlds={};records=[];fail=[];positions=recipe['body_standard']['head_world_positions'].copy()
def register(n,s,hl,group):
    size,b,safe=geometry[n];common=np.logical_and.reduce([geometry[k][2] for k in group]);h,w=s.shape
    target=[-12,-24] if n==147 else positions[str(n)]
    tx,ty=target[0]-hl[0],target[1]-hl[1]
    if n in [147,3,4,34]:ty=24-h
    choices=[]
    for dx in range(-6,7):
        for dy in range(-3,4):
            x,y=tx+dx,ty+dy;bad=int(((s!=0)&~common[64+y:64+y+h,64+x:64+x+w]).sum());cost=bad*100+abs(dx)*3+abs(dy)*5
            head_bad=int((hm&~common[64+y+hl[1]:64+y+hl[1]+19,64+x+hl[0]:64+x+hl[0]+23]).sum());cost+=head_bad*10000
            if n in [147,3,4,34]:cost+=abs(y+h-24)*15
            choices.append((cost,bad,x,y))
    _,bad,x,y=min(choices);world=np.zeros((128,128),dtype=np.uint8);world[64+y:64+y+h,64+x:64+x+w]=s
    rec={'frames':group,'whole_origin':[x,y],'head_world':[x+hl[0],y+hl[1]],'opaque_bottom':y+h-1,'parts_outside':bad,'components':[len(g) for g in component(world!=0)]}
    if bad:rec['outside_pixels']=[[int(xx-64),int(yy-64)] for yy,xx in np.argwhere((world!=0)&~common)];fail.append(rec)
    for k in group:worlds[k]=world.copy();positions[str(k)]=rec['head_world']
    records.append(rec)
s,hl=normalize(Image.open(D/'generated_idle.png'),.060);register(147,s,hl,[147])
im=Image.open(D/'generated_motion.png');groups=[[21],[22,23],[24],[25,26],[27,28,29,30,31,32],[33],[34],[3],[4]]
for i,g in enumerate(groups):
    c=im.crop((round(i%3*im.width/3),round(i//3*im.height/3),round((i%3+1)*im.width/3),round((i//3+1)*im.height/3)))
    s,hl=normalize(c,.148);register(g[0],s,hl,g)
print('CHECKS',json.dumps(records));print('FAIL',json.dumps(fail))
font=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',16)
def rgba(w):
    a=w[20:100,28:100];m=a!=0;r=np.zeros((80,72,4),dtype=np.uint8);r[m,:3]=colors[a[m]-1];r[m,3]=255;return Image.fromarray(r)
for n in range(7,21):
    a=np.array(Image.open(B/f'frame_{n:03d}.png'));b=geometry[n][1];w=np.zeros((128,128),dtype=np.uint8);w[64+b[1]:64+b[3],64+b[0]:64+b[2]]=a;worlds[n]=w
nums=[147,7,11,14,21,22,24,25,27,33,34,3,4];board=Image.new('RGBA',(5*288,3*340),(42,45,54,255));draw=ImageDraw.Draw(board)
for i,n in enumerate(nums):board.alpha_composite(rgba(worlds[n]).resize((288,320),Image.Resampling.NEAREST),(i%5*288,i//5*340+20));draw.text((i%5*288+4,i//5*340),str(n),font=font,fill='white')
board.save(D/'fit_review.png')
np.savez(D/'worlds_probe.npz',**{str(n):w for n,w in worlds.items()})
(D/'fit_registration.json').write_text(json.dumps({'records':records,'failures':fail,'head_positions':positions,'scales':{'idle':.060,'motion':.148}},indent=2),encoding='utf-8')
