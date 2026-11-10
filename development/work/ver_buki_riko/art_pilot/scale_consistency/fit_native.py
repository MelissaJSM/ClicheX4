exec((__import__('pathlib').Path(__file__).with_name('fit_probe.py')).read_text(encoding='utf-8').split('run_slots=')[0])
prior=json.loads((P/'fit_probe.json').read_text());master_indices=np.array(Image.open(master));head=master_indices[:19,12:35].copy()
frames={n:read_indexed_png(master,words) for n in (5,6)};records={};worlds={};failed=[]
for key,r in prior.items():
 kind=r['kind'];j=r['key'];source_key=0 if kind=='run' and j==12 else j
 path=P/f'compact_{kind}_{source_key:02d}.png'
 if not path.exists():path=P/f'probe_{kind}_{source_key:02d}.png'
 ix=np.array(Image.open(path));h,w=ix.shape;ex=r['eye_world'][0]-r['world_origin'][0];ey=r['eye_world'][1]-r['world_origin'][1]
 hx=round(ex-6);hy=round(ey-12.5)
 if kind=='jump' and j==3:hx+=3
 native=np.zeros((96,96),dtype=np.uint8);native[24:24+h,24:24+w]=ix
 # Exact approved head/collar patch; whole generated body below the neck is retained.
 cut_bottom=hy+19
 clear_right=26 if not (kind=='jump' and j==5) else 25
 native[24:24+cut_bottom,24:24+clear_right]=0
 native[24+hy:24+hy+19,24+hx:24+hx+23]=head
 yy,xx=np.nonzero(native);bx0,by0,bx1,by1=int(xx.min()),int(yy.min()),int(xx.max()+1),int(yy.max()+1);sprite=native[by0:by1,bx0:bx1];h,w=sprite.shape
 local_head=[24+hx-bx0,24+hy-by0];common=np.logical_and.reduce([geometry[n][2] for n in r['slots']])
 target=-2 if r['slots'] in ([3],[4]) else -6
 ideal_x=target-(local_head[0]+6);ideal_y=24-h
 choices=[]
 for x in range(ideal_x-5,ideal_x+6):
  for y in (range(ideal_y-1,ideal_y+2) if kind=='run' else range(ideal_y-9,ideal_y+5)):
   mask=sprite!=0;bad=int(np.sum(mask&~common[64+y:64+y+h,64+x:64+x+w]));cost=bad*100+abs(x-ideal_x)+2*abs(y-ideal_y);choices.append((cost,bad,x,y))
 _,bad,x,y=min(choices);world=np.zeros((128,128),dtype=np.uint8);world[64+y:64+y+h,64+x:64+x+w]=sprite
 record={**r,'native_source':path.name,'local_head':local_head,'master_head_roi':[12,0,35,19],'world_origin':[x,y],'size':[w,h],'outside':bad,'head_world':[x+local_head[0],y+local_head[1]],'head_replaced':True,'body_rescaled_after_normalization':False}
 if bad:record['bad_pixels']=[[int(xx+x),int(yy+y)] for yy,xx in np.argwhere((sprite!=0)&~common[64+y:64+y+h,64+x:64+x+w])];failed.append(record)
 records[key]=record;worlds[r['slots'][0]]=world
 for n in r['slots']:
  size,b,_=geometry[n];canvas=world[64+b[1]:64+b[3],64+b[0]:64+b[2]];frames[n]=(canvas.tobytes(),size);save_image(*frames[n],words,P/f'native_frame_{n:03d}.png')
print('FAILURES',json.dumps(failed))
(P/'native_fit.json').write_text(json.dumps(records,indent=2),encoding='utf-8')
if not failed:
 try:
  _,checks=patch_frames(arc,gmeta,gfx,parts,frames,pal);print('COMPRESSION',json.dumps(checks['compression']))
 except Exception as e:print('PREFLIGHT_FAILURE',str(e))
board=Image.new('RGBA',(6*256,4*320),(42,45,54,255));draw=ImageDraw.Draw(board)
for k,(n,world) in enumerate([(147,None),*worlds.items()]):
 tile=Image.new('RGBA',(64,72))
 if n==147:tile.alpha_composite(Image.open(master).convert('RGBA'),(8,16))
 else:
  indices=world[24:96,32:96];mask=indices!=0;a=np.zeros((72,64,4),dtype=np.uint8);a[mask,:3]=colors[indices[mask]-1];a[mask,3]=255;tile=Image.fromarray(a)
 x=k%6*256;y=k//6*320;board.alpha_composite(tile.resize((256,288),Image.Resampling.NEAREST),(x,y+32));draw.text((x+5,y+5),str(n),fill='white');draw.line((x,y+288,x+255,y+288),fill=(95,95,100))
board.save(P/'native_fit_board.png')
