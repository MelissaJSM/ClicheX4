from pathlib import Path
import sys,json,math,hashlib
import numpy as np
from PIL import Image,ImageDraw
P=Path(__file__).parent.parent
exec((P/'fit_probe.py').read_text(encoding='utf-8').split('run_slots=')[0].replace("Path(__file__).resolve().parents[4]","Path(__file__).resolve().parents[5]").replace('P=Path(__file__).parent','P=Path(__file__).parent.parent'))
R=P/'gait_cape_repair'
def indexed(im):
 a=np.array(im.convert('RGBA'));mask=a[:,:,3]>=128;out=np.zeros(mask.shape,dtype=np.uint8);rgb=a[:,:,:3].astype(np.int32);out[mask]=np.argmin(((rgb[mask,None]-colors[None])**2).sum(2),1)+1;return out
def rgba(a):
 out=np.zeros((*a.shape,4),dtype=np.uint8);m=a!=0;out[m,:3]=colors[a[m]-1];out[m,3]=255;return Image.fromarray(out)
def old_world(n):
 a=np.array(Image.open(P/f'locked_frame_{n:03d}.png'));b=geometry[n][1];w=np.zeros((128,128),dtype=np.uint8);w[64+b[1]:64+b[3],64+b[0]:64+b[2]]=a;return w
def paste(dst,src,x,y):
 h,w=src.shape;sub=dst[y:y+h,x:x+w];m=src!=0;sub[m]=src[m]
# All limb artwork uses ONE uniform normalization factor. No per-pose bbox fit.
leg_sheet=Image.open(R/'generated_legs.png').convert('RGBA');leg_sheet_v2=Image.open(R/'generated_legs_v2.png').convert('RGBA').resize(leg_sheet.size,Image.Resampling.NEAREST);legs=[];leg_records=[]
for j in range(12):
 source_j=10 if j==11 else j
 x0=round(source_j%4*leg_sheet.width/4);x1=round((source_j%4+1)*leg_sheet.width/4);y0=round(source_j//4*leg_sheet.height/3);y1=round((source_j//4+1)*leg_sheet.height/3)
 a=np.array((leg_sheet_v2 if j in [9,10] else leg_sheet).crop((x0,y0,x1,y1)));yy,xx=np.nonzero(a[:,:,3]>=128);box=(int(xx.min()),int(yy.min()),int(xx.max()+1),int(yy.max()+1));crop=a[box[1]:box[3],box[0]:box[2]]
 scale=.07;h,w=[math.ceil(v*scale) for v in crop.shape[:2]];xs=np.minimum(((np.arange(w)+.5)/scale).astype(int),crop.shape[1]-1);ys=np.minimum(((np.arange(h)+.5)/scale).astype(int),crop.shape[0]-1);ix=indexed(Image.fromarray(crop[ys[:,None],xs[None,:]]))
 ys0,xs0=np.nonzero(np.isin(ix[:3],[9,11,13]));pivot_x=round(float(xs0.mean()));pivot_y=0
 # Preserve source topology and register the anatomical upper-thigh attachment.
 legs.append((ix,pivot_x,pivot_y));save_image(ix.tobytes(),(w,h),words,R/f'leg_{j:02d}.png')
 yy,xx=np.nonzero(ix);low=yy.max();foot=xx[yy>=low-1];leg_records.append({'phase':j,'source_box':box,'scale':scale,'pivot':[pivot_x,pivot_y],'size':[w,h],'foot':[round(float(foot.mean())-pivot_x,2),int(low)],'lowest_y':int(low)})
print('LEGS',json.dumps(leg_records))
base=old_world(7);body=base.copy();body[72:,:]=0
# Retain the existing central teal skirt flap below the hem, behind the legs.
flap=np.zeros_like(body);flap[72:78,63:66]=base[72:78,63:66]
slots=[(7,),(8,9),(10,),(11,),(12,),(13,),(14,),(15,16),(17,),(18,),(19,),(20,)]
shade=np.arange(16,dtype=np.uint8);shade[15]=12;shade[12]=7;shade[7]=3;shade[13]=11;shade[11]=9
worlds={n:old_world(n) for n in [3,4,*range(21,35)]};reg=json.loads((P/'scale_recipe.json').read_text())['body_standard']['head_world_positions'];reg={int(k):v for k,v in reg.items()};gait=[]
for j,ns in enumerate(slots):
 w=flap.copy();far,fpx,fpy=legs[(j+6)%12];near,npx,npy=legs[j]
 def hip(phase,side):
  dx={1:-2,10:-1,11:2 if side=='near' else 3}.get(phase,0)
  return ((-2 if side=='near' else 1)+dx,3 if phase==11 else 5)
 nx,ny=hip(j,'near');fx,fy=hip((j+6)%12,'far')
 paste(w,shade[far],64+fx-fpx,64+fy-fpy);paste(w,near,64+nx-npx,64+ny-npy);paste(w,body,0,0)
 # Move the WHOLE pose together to the common support baseline; no waist split.
 yy,xx=np.nonzero(w);dy=23-(int(yy.max())-64);shift=np.zeros_like(w)
 if dy>=0:shift[dy:]=w[:128-dy]
 else:shift[:128+dy]=w[-dy:]
 for n in ns:worlds[n]=shift.copy();reg[n]=[reg[7][0],json.loads((P/'scale_recipe.json').read_text())['body_standard']['head_world_positions']['7'][1]+dy]
 gait.append({'slots':ns,'near_phase':j,'far_phase':(j+6)%12,'whole_pose_dy':dy,'far_hip':[fx,fy+dy],'near_hip':[nx,ny+dy],'near_foot':[leg_records[j]['foot'][0]+nx,leg_records[j]['foot'][1]+ny+dy],'far_foot':[leg_records[(j+6)%12]['foot'][0]+fx,leg_records[(j+6)%12]['foot'][1]+fy+dy]})
# Cape replacement is restricted to authored fabric regions, excluding fixed head.
cap=indexed(Image.open(R/'generated_cape.png').resize((192,72),Image.Resampling.NEAREST));cape_records=[]
for cell,ns,roi in [(0,range(27,33),(4,-14,24,2))]:
 tile=cap[:,cell*64:(cell+1)*64]
 x0,y0,x1,y1=roi
 for n in ns:
  w=worlds[n];before=w.copy();w[64+y0:64+y1,64+x0:64+x1]=tile[y0+40:y1+40,x0+32:x1+32]
  # The approved head/collar rectangle is immutable.
  hx,hy=reg[n];approved=np.array(Image.open(master))[:19,12:35];sub=w[64+hy:64+hy+19,64+hx:64+hx+23];sub[approved!=0]=approved[approved!=0]
  cape_records.append({'frame':n,'roi':roi,'changed_pixels':int(np.sum(before!=w))})
frames={n:read_indexed_png(master,words) for n in [5,6]};fail=[]
for n,w in worlds.items():
 size,b,safe=geometry[n];bad=np.argwhere((w!=0)&~safe)
 if len(bad):fail.append({'frame':n,'pixels':[[int(x-64),int(y-64)] for y,x in bad]})
 a=w[64+b[1]:64+b[3],64+b[0]:64+b[2]];frames[n]=(a.tobytes(),size);save_image(*frames[n],words,R/f'frame_{n:03d}.png')
for n in [5,6]:save_image(*frames[n],words,R/f'frame_{n:03d}.png')
print('FAIL',json.dumps(fail))
board=Image.new('RGBA',(6*256,3*304),(42,45,54,255));d=ImageDraw.Draw(board)
for k,n in enumerate([7,8,10,11,12,13,14,15,17,18,19,20,27,33,34]):
 im=rgba(worlds[n][24:96,32:96]);board.alpha_composite(im.resize((256,288),Image.Resampling.NEAREST),(k%6*256,k//6*304+16));d.text((k%6*256+3,k//6*304),str(n),fill='white')
board.save(R/'assembled_board.png')
if not fail:
 _,checks=patch_frames(arc,gmeta,gfx,parts,frames,pal);print('COMPRESSION_MAX',max(c['encoded_bytes'] for c in checks['compression']))
recipe=json.loads((P/'scale_recipe.json').read_text());recipe['frames']={str(n):{'file':f'frame_{n:03d}.png','sha256':hashlib.sha256((R/f'frame_{n:03d}.png').read_bytes()).hexdigest()} for n in sorted(frames)};recipe['body_standard']['head_world_positions']={str(k):v for k,v in reg.items()};recipe['gait']={'leg_samples':leg_records,'phase_assignment':gait,'cycle_ticks':32,'near_far_offset_ticks':16,'whole_body_translation_only':True};recipe['cape_repair']=cape_records;recipe.pop('loop_preservation',None);recipe['source_art']={str((R/name).relative_to(R)):hashlib.sha256((R/name).read_bytes()).hexdigest() for name in ['generated_legs.png','generated_cape.png']};recipe['previous_motion_set']='work/ver_buki_riko/scale_frames/20261023T152146467346Z/motion_set.json'
recipe['source_art']['generated_legs_v2.png']=hashlib.sha256((R/'generated_legs_v2.png').read_bytes()).hexdigest()
recipe.pop('native_registration',None)
recipe['body_standard']['source_sheet_uniform_scales']['legs']=.07
(R/'recipe.json').write_text(json.dumps(recipe,indent=2),encoding='utf-8')
(R/'geometry_check.json').write_text(json.dumps({'outside':fail,'gait':gait,'legs':leg_records,'cape':cape_records},indent=2),encoding='utf-8')
