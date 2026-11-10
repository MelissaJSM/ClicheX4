from pathlib import Path
P=Path(__file__).parent
exec((P/'fit_probe.py').read_text(encoding='utf-8').split('run_slots=')[0])
import hashlib,shutil
U=P/'upper_body_repair';Q=P/'stride_revision';recipe=json.loads((U/'recipe.json').read_text());reg=recipe['body_standard']['head_world_positions'];guide=json.loads((Q/'kinematic_guide.json').read_text())
def index(im):
 a=np.array(im.convert('RGBA'));m=a[:,:,3]>=128;rgb=a[:,:,:3].astype(np.int32);ix=np.zeros(m.shape,dtype=np.uint8);ix[m]=np.argmin(((rgb[m,None]-colors[None])**2).sum(2),1)+1;return ix
def paste(w,a,x,y):
 h,ww=a.shape;sub=w[y:y+h,x:x+ww];m=a!=0;sub[m]=a[m]
def world(n):
 a=np.array(Image.open(U/f'frame_{n:03d}.png'));b=geometry[n][1];w=np.zeros((128,128),dtype=np.uint8);w[64+b[1]:64+b[3],64+b[0]:64+b[2]]=a;return w
im=Image.open(Q/'generated_stride_guided.png').convert('RGBA');legs=[];lr=[]
for i in range(14):
 s=0 if i==13 else i;cell=im.crop((round(s%4*im.width/4),round(s//4*im.height/4),round((s%4+1)*im.width/4),round((s//4+1)*im.height/4)));a=np.array(cell);yy,xx=np.nonzero(a[:,:,3]>=128);crop=a[yy.min():yy.max()+1,xx.min():xx.max()+1];scale=.11;h,w=[math.ceil(v*scale) for v in crop.shape[:2]];xs=np.minimum(((np.arange(w)+.5)/scale).astype(int),crop.shape[1]-1);ys=np.minimum(((np.arange(h)+.5)/scale).astype(int),crop.shape[0]-1);ix=index(Image.fromarray(crop[ys[:,None],xs[None,:]]));py,px=np.nonzero(np.isin(ix[:3],[9,11,13]));pivot=round(float(px.mean()));yy,xx=np.nonzero(ix);low=int(yy.max());foot=float(xx[yy>=low-1].mean())-pivot;legs.append((ix,pivot));lr.append({'phase':i,'source_cell':s,'scale':scale,'size':[w,h],'pivot_x':pivot,'foot_x':round(foot,2),'foot_y':low});save_image(ix.tobytes(),(w,h),words,Q/f'leg_{i:02d}.png')
print('LEGS',json.dumps(lr))
shade=np.arange(16,dtype=np.uint8);shade[15]=12;shade[12]=7;shade[7]=3;shade[13]=11;shade[11]=9
# Measured sole tracks determine joint registration; the limb pixels are not stretched.
target_x=[-9,-14,-8,-4,0,4,9,12,12,2,2,4,1,-5]
hip_dx=[round(x-r['foot_x']) for x,r in zip(target_x,lr)]
print('HIP_DX',hip_dx)
old_dy={r['frame']:r['whole_pose_dy'] for r in recipe['upper_body_motion']['records']}
new_reg={int(k):v for k,v in reg.items()};records=[];worlds={};frames={};fail=[]
for i,n in enumerate(range(7,21)):
 far_i=(i+7)%14;near,npx=legs[i];far,fpx=legs[far_i]
 if 1<=i%7<=4:
  supporting=i if i<7 else far_i;dy=23-2-lr[supporting]['foot_y']
 else:dy=0
 body=world(n);body[64+8+old_dy[n]:]=0;shift=dy-old_dy[n];shifted=np.zeros_like(body)
 if shift>=0:shifted[shift:]=body[:128-shift]
 else:shifted[:128+shift]=body[-shift:]
 w=np.zeros((128,128),dtype=np.uint8);nx=-2+hip_dx[i];fx=1+hip_dx[far_i]
 paste(w,shade[far],64+fx-fpx,64+2+dy);paste(w,near,64+nx-npx,64+2+dy);paste(w,shifted,0,0)
 size,b,safe=geometry[n];bad=np.argwhere((w!=0)&~safe)
 if len(bad):fail.append({'frame':n,'pixels':[[int(x-64),int(y-64)] for y,x in bad]})
 worlds[n]=w;new_reg[n]=[reg[str(n)][0],reg[str(n)][1]+shift];a=w[64+b[1]:64+b[3],64+b[0]:64+b[2]];frames[n]=(a.tobytes(),size);save_image(*frames[n],words,Q/f'frame_{n:03d}.png')
 records.append({'frame':n,'near_phase':i,'far_phase':far_i,'near_hip':[nx,2+dy],'far_hip':[fx,2+dy],'whole_body_dy':dy,'near_foot':[round(nx+lr[i]['foot_x'],2),2+dy+lr[i]['foot_y']],'far_foot':[round(fx+lr[far_i]['foot_x'],2),2+dy+lr[far_i]['foot_y']]})
print('FAIL',json.dumps(fail))
for n in range(3,35):
 if n not in worlds:shutil.copyfile(U/f'frame_{n:03d}.png',Q/f'frame_{n:03d}.png');frames[n]=read_indexed_png(Q/f'frame_{n:03d}.png',words)
if not fail:
 _,checks=patch_frames(arc,gmeta,gfx,parts,frames,pal);print('COMPRESSION',max(c['encoded_bytes'] for c in checks['compression']))
recipe['frames']={str(n):{'file':f'frame_{n:03d}.png','sha256':hashlib.sha256((Q/f'frame_{n:03d}.png').read_bytes()).hexdigest()} for n in range(3,35)};recipe['body_standard']['head_world_positions']={str(k):v for k,v in new_reg.items()};recipe['gait']={'phase_assignment':records,'leg_samples':lr,'cycle_ticks':32,'offset_ticks':16,'unique_phases':14,'source_scale':.11,'joint_dx':hip_dx,'target_plant_speed':2,'plant_phases':[1,2,3,4],'target_foot_x':target_x};recipe['previous_motion_set']='work/ver_buki_riko/scale_frames/20261023T200215925304Z/motion_set.json';recipe['source_art']={'generated_stride_guided.png':hashlib.sha256((Q/'generated_stride_guided.png').read_bytes()).hexdigest(),'../upper_body_repair/recipe.json':hashlib.sha256((U/'recipe.json').read_bytes()).hexdigest()};recipe.pop('upper_body_motion',None);recipe['upper_body_source']='Retained upper-body artwork from previous motion, translated with pelvis as one body.'
(Q/'recipe.json').write_text(json.dumps(recipe,indent=2,ensure_ascii=False),encoding='utf-8')
board=Image.new('RGBA',(7*256,2*304),(42,45,54,255));d=ImageDraw.Draw(board)
for k,(n,w) in enumerate(worlds.items()):
 a=w[24:96,32:96];m=a!=0;rgba=np.zeros((72,64,4),dtype=np.uint8);rgba[m,:3]=colors[a[m]-1];rgba[m,3]=255;board.alpha_composite(Image.fromarray(rgba).resize((256,288),Image.Resampling.NEAREST),(k%7*256,k//7*304+16));d.text((k%7*256+3,k//7*304),str(n),fill='white')
board.save(Q/'stride_review.png')
