from pathlib import Path
P=Path(__file__).parent
exec((P/'fit_probe.py').read_text(encoding='utf-8').split('run_slots=')[0])
import hashlib,shutil
R=P/'gait_cape_repair';U=P/'upper_body_repair';recipe=json.loads((R/'recipe.json').read_text());reg=recipe['body_standard']['head_world_positions'];head=np.array(Image.open(master))[:19,12:35]
def world(n):
 a=np.array(Image.open(R/f'frame_{n:03d}.png'));b=geometry[n][1];w=np.zeros((128,128),dtype=np.uint8);w[64+b[1]:64+b[3],64+b[0]:64+b[2]]=a;return w
im=Image.open(U/'generated_upper_v2.png').convert('RGBA').resize((192,144),Image.Resampling.NEAREST);a=np.array(im);m=a[:,:,3]>=128;ix=np.zeros(m.shape,dtype=np.uint8);rgb=a[:,:,:3].astype(np.int32);ix[m]=np.argmin(((rgb[m,None]-colors[None])**2).sum(2),1)+1
source_dy=[0,0,1,0,0,1];assign=[0,1,1,2,2,2,3,4,4,5,5,5]
records=[];worlds={};frames={}
for phase,g in enumerate(recipe['gait']['phase_assignment']):
 key=assign[phase];tile=ix[key//3*72:(key//3+1)*72,key%3*64:(key%3+1)*64];dy=g['whole_pose_dy'];sy=source_dy[key]
 for n in g['slots']:
  w=world(n);before=w.copy();x0,x1=-18,25;y0,y1=-5+dy,8+dy
  w[64+y0:64+y1,64+x0:64+x1]=tile[40-5+sy:40+8+sy,32+x0:32+x1]
  hx,hy=reg[str(n)];sub=w[64+hy:64+hy+19,64+hx:64+hx+23];sub[head!=0]=head[head!=0]
  assert np.array_equal(w[64+8+dy:],before[64+8+dy:])
  size,b,safe=geometry[n];bad=np.argwhere((w!=0)&~safe);records.append({'frame':n,'art_key':key,'whole_pose_dy':dy,'lower_body_start_y':8+dy,'lower_body_unchanged':True,'changed_pixels':int(np.sum(w!=before)),'outside':[[int(x-64),int(y-64)] for y,x in bad]})
  a=w[64+b[1]:64+b[3],64+b[0]:64+b[2]];frames[n]=(a.tobytes(),size);save_image(*frames[n],words,U/f'frame_{n:03d}.png');worlds[n]=w
for n in range(3,35):
 if n not in worlds:shutil.copyfile(R/f'frame_{n:03d}.png',U/f'frame_{n:03d}.png');frames[n]=read_indexed_png(U/f'frame_{n:03d}.png',words)
fail=[r for r in records if r['outside']];print('FAIL',json.dumps(fail))
if not fail:
 _,checks=patch_frames(arc,gmeta,gfx,parts,frames,pal);print('COMPRESSION',max(c['encoded_bytes'] for c in checks['compression']))
recipe['frames']={str(n):{'file':f'frame_{n:03d}.png','sha256':hashlib.sha256((U/f'frame_{n:03d}.png').read_bytes()).hexdigest()} for n in range(3,35)}
recipe['upper_body_motion']={'records':records,'head_foreground_preserved':True,'pelvis_and_legs_preserved':True,'cape_repair_preserved':True,'prior_build':'out/ver_buki_riko/riko_motion_20261023T195248689307Z','user_feedback':'이번엔 부드러운데... 상체가 굳어있어서 너무 조심스레걷는느낌이 강한데 수정좀해볼래...?'}
recipe['source_art']={'generated_upper_v2.png':hashlib.sha256((U/'generated_upper_v2.png').read_bytes()).hexdigest(),'../gait_cape_repair/recipe.json':hashlib.sha256((R/'recipe.json').read_bytes()).hexdigest()};recipe['previous_motion_set']='work/ver_buki_riko/scale_frames/20261023T195224671886Z/motion_set.json'
(U/'recipe.json').write_text(json.dumps(recipe,indent=2,ensure_ascii=False),encoding='utf-8')
board=Image.new('RGBA',(6*256,2*304),(42,45,54,255));draw=ImageDraw.Draw(board)
for k,n in enumerate([7,8,10,11,12,13,14,15,17,18,19,20]):
 a=worlds[n][24:96,32:96];m=a!=0;rgba=np.zeros((72,64,4),dtype=np.uint8);rgba[m,:3]=colors[a[m]-1];rgba[m,3]=255;board.alpha_composite(Image.fromarray(rgba).resize((256,288),Image.Resampling.NEAREST),(k%6*256,k//6*304+16));draw.text((k%6*256+3,k//6*304),str(n),fill='white')
board.save(U/'upper_review.png')
