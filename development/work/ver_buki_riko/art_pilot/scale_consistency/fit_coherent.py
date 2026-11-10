from pathlib import Path
P=Path(__file__).parent
exec((P/'fit_probe.py').read_text(encoding='utf-8').split('run_slots=')[0])
import hashlib,shutil
C=P/'coherent_walk';Q=P/'stride_revision';recipe=json.loads((Q/'recipe.json').read_text())
head=np.array(Image.open(master))[:19,12:35];im=Image.open(C/'generated_final.png').convert('RGBA');scale=.17
records=[];worlds={};frames={};fails=[];reg=recipe['body_standard']['head_world_positions'].copy()
for i,n in enumerate(range(7,21)):
    cell=im.crop((round(i%4*im.width/4),round(i//4*im.height/4),round((i%4+1)*im.width/4),round((i//4+1)*im.height/4)))
    a=np.array(cell);yy,xx=np.nonzero(a[:,:,3]>=160);a=a[yy.min():yy.max()+1,xx.min():xx.max()+1]
    h,w=[math.ceil(v*scale) for v in a.shape[:2]];xs=np.minimum(((np.arange(w)+.5)/scale).astype(int),a.shape[1]-1);ys=np.minimum(((np.arange(h)+.5)/scale).astype(int),a.shape[0]-1);a=a[ys[:,None],xs[None,:]]
    mask=a[:,:,3]>=160;rgb=a[:,:,:3].astype(np.int32);ix=np.zeros((h,w),dtype=np.uint8);ix[mask]=np.argmin(((rgb[mask,None]-colors[None])**2).sum(2),1)+1
    green=(rgb[:,:,1]>rgb[:,:,0]+8)&(rgb[:,:,1]>rgb[:,:,2]+8)&mask&(np.indices(ix.shape)[0]<h*.38)
    gy,gx=np.nonzero(green);assert len(gx),n
    hc=np.zeros((*head.shape,3),dtype=int);hm=head!=0;hc[hm]=colors[head[hm]-1]
    hg=(hc[:,:,1]>hc[:,:,0]+8)&(hc[:,:,1]>hc[:,:,2]+8)&hm;hgy,hgx=np.nonzero(hg)
    hx=round(float(gx.mean()-hgx.mean()));hy=0
    # Whole generated body is preserved below the collar. No limb assembly,
    # waist cut, per-frame scale, hip offsets or shoulder-only translations.
    sprite=np.zeros((96,96),dtype=np.uint8);sprite[24:24+h,24:24+w]=ix
    sprite[:24+hy+18,:]=0
    sub=sprite[24+hy:24+hy+19,24+hx:24+hx+23];sub[head!=0]=head[head!=0]
    yy,xx=np.nonzero(sprite);x0,y0,x1,y1=int(xx.min()),int(yy.min()),int(xx.max()+1),int(yy.max()+1);sprite=sprite[y0:y1,x0:x1]
    head_local=[24+hx-x0,24+hy-y0];hh,ww=sprite.shape;ideal_x=-12-head_local[0];ideal_y=24-hh
    size,b,safe=geometry[n];choices=[]
    for dx in range(-3,4):
        for dy in range(-1,2):
            x,y=ideal_x+dx,ideal_y+dy;bad=int(np.sum((sprite!=0)&~safe[64+y:64+y+hh,64+x:64+x+ww]));choices.append((100*bad+3*abs(dx)+5*abs(dy),bad,x,y))
    _,bad,x,y=min(choices);world=np.zeros((128,128),dtype=np.uint8);world[64+y:64+y+hh,64+x:64+x+ww]=sprite
    if bad:fails.append({'frame':n,'bad':bad,'pixels':[[int(xx-64),int(yy-64)] for yy,xx in np.argwhere((world!=0)&~safe)]})
    worlds[n]=world;reg[str(n)]=[x+head_local[0],y+head_local[1]];native=world[64+b[1]:64+b[3],64+b[0]:64+b[2]]
    frames[n]=(native.tobytes(),size);save_image(*frames[n],words,C/f'frame_{n:03d}.png')
    records.append({'frame':n,'source_cell':i,'uniform_scale':scale,'head_world':reg[str(n)],'whole_pose_origin':[x,y],'source_size':[w,h],'sprite_size':[ww,hh],'ground_y':y+hh-1,'parts_outside':bad,'separate_hip_translation':False,'waist_composite':False})
for n in range(3,35):
    if n not in worlds:shutil.copyfile(Q/f'frame_{n:03d}.png',C/f'frame_{n:03d}.png');frames[n]=read_indexed_png(C/f'frame_{n:03d}.png',words)
print('FAIL',json.dumps(fails));print('REG',json.dumps(records))
if not fails:
    _,checks=patch_frames(arc,gmeta,gfx,parts,frames,pal);print('COMPRESSION',max(c['encoded_bytes'] for c in checks['compression']))
recipe['frames']={str(n):{'file':f'frame_{n:03d}.png','sha256':hashlib.sha256((C/f'frame_{n:03d}.png').read_bytes()).hexdigest()} for n in range(3,35)}
recipe['body_standard']['head_world_positions']=reg
recipe.pop('gait',None);recipe.pop('upper_body_source',None)
recipe['coherent_body']={'method':'14 whole-body generated poses, uniform sheet scale, canonical head foreground; no waist/hip/arm layer compositing','records':records,'source':'generated_final.png','full_art_quality_approved':False}
recipe['source_art']={'generated_final.png':hashlib.sha256((C/'generated_final.png').read_bytes()).hexdigest(),'pose_guide.json':hashlib.sha256((C/'pose_guide.json').read_bytes()).hexdigest()}
recipe['previous_motion_set']='work/ver_buki_riko/scale_frames/20261023T201425191524Z/motion_set.json'
(C/'recipe.json').write_text(json.dumps(recipe,indent=2,ensure_ascii=False),encoding='utf-8')
board=Image.new('RGBA',(7*256,2*304),(42,45,54,255));draw=ImageDraw.Draw(board);images=[]
for k,(n,world) in enumerate(worlds.items()):
    a=world[24:96,32:96];m=a!=0;rgba=np.zeros((72,64,4),dtype=np.uint8);rgba[m,:3]=colors[a[m]-1];rgba[m,3]=255;tile=Image.fromarray(rgba);canvas=Image.new('RGBA',(256,288),(42,45,54,255));canvas.alpha_composite(tile.resize((256,288),Image.Resampling.NEAREST));images.append(canvas.convert('RGB'))
    board.alpha_composite(canvas,(k%7*256,k//7*304+16));draw.text((k%7*256+3,k//7*304),str(n),fill='white')
board.save(C/'native_review.png')
images[0].save(C/'preview.gif',save_all=True,append_images=images[1:],duration=[round(t/60*1000) for t in recipe['run_ticks']],loop=0,disposal=2)
