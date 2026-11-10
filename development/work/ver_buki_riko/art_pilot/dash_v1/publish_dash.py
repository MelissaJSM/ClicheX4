from fit_dash import *
import shutil,hashlib
from scripts.build_riko_idle import patch_frames,check_motion_scale
from scripts.discover_inputs import sha256
base=ROOT/'work/ver_buki_riko/art_pilot/scale_consistency/walk_design_basis'
recipe=json.loads((base/'recipe.json').read_text('utf8'));recipe['scope']='jump_run_dash_v1'
worlds={int(k):w.copy() for k,w in np.load(D/'worlds_final_probe.npz').items()}
records=json.loads((D/'final_registration.json').read_text('utf8'))
if any(r['outside'] or len(r['components'])!=1 for r in records.values()):raise ValueError('Unfitted source pose')
im=Image.open(D/'generated_cape.png');cape_records=[]
for i,n in ((1,47),(2,48)):
 cell=im.crop((round(i*im.width/3),0,round((i+1)*im.width/3),im.height));s,hl=normalize(cell,240/im.width)
 hx,hy=records['46']['head_world'];x,y=hx-hl[0],hy-hl[1];w=np.zeros((128,128),dtype=np.uint8);w[64+y:64+y+s.shape[0],64+x:64+x+s.shape[1]]=s
 world=worlds[46].copy();world[58:74,71:96]=w[58:74,71:96]
 worlds[n]=world;records[str(n)]={**records['46'],'frame':n,'cape_source_cell':i,'cape_world_rectangle':[7,-6,32,10]}
 cape_records.append({'frame':n,'changed_pixels':int((world!=worlds[46]).sum()),'body_outside_cape_exact':True,'source_scale':240/im.width,'source_registration':[x,y]})
worlds[52]=np.roll(worlds[51],-1,axis=1);records['52']={**records['51'],'frame':52,'head_world':[records['51']['head_world'][0]-1,records['51']['head_world'][1]],'derived':'Original parts shift all body tiles one pixel left; same-index shared tiles preserved'}
frames={};checks=[]
for n,world in sorted(worlds.items()):
 size,b,safe=geometry[n];outside=int(((world!=0)&~safe).sum());groups=component(world!=0)
 if outside or len(groups)!=1:raise ValueError(f'Invalid final frame {n}: outside {outside}, components {[len(g) for g in groups]}')
 canvas=world[64+b[1]:64+b[3],64+b[0]:64+b[2]];frames[n]=(canvas.tobytes(),size)
 save_image(*frames[n],words,D/f'frame_{n:03}.png');path=D/f'frame_{n:03}.png'
 recipe['frames'][str(n)]={'file':path.name,'sha256':sha256(path.read_bytes())};recipe['body_standard']['head_world_positions'][str(n)]=records[str(n)]['head_world']
 yy,xx=np.nonzero(world);checks.append({'frame':n,'outside_pixels':outside,'components':len(groups),'opaque_pixels':len(xx),'opaque_bounds':[int(xx.min()-64),int(yy.min()-64),int(xx.max()+1-64),int(yy.max()+1-64)],'head_world':records[str(n)]['head_world']})
for key,r in recipe['frames'].items():
 if int(key) in worlds:continue
 src=base/r['file'];dest=D/r['file'];shutil.copyfile(src,dest);frames[int(key)]=read_indexed_png(dest,words)
 if sha256(dest.read_bytes())!=r['sha256']:raise ValueError('Existing approved frame changed')
reference=read_indexed_png(ROOT/'out/ver_buki_riko/riko_pilot_20261023T082720987715Z/riko_idle147_indexed.png',words)
scale_check=check_motion_scale(recipe,frames,gfx,parts,reference)
_,compression=patch_frames(arc,gmeta,gfx,parts,frames,pal)
recipe['dash_production']={'base_build_sha256':'099e9f178ef9b26d2bc37198f6493ecf3adf65f5ff954f8c8b40f0658ea3f08b','new_frames':list(range(44,53)),'original_animation_ids':[16,17],'additional_shared_animation_ids':[18,19],'original_timing_parts_logic_preserved':True,'existing_38_references_preserved':True,'art_user_review_pending':True,'head_registration_adjustment_frame50':[1,0]}
(D/'recipe.json').write_text(json.dumps(recipe,indent=2),encoding='utf8')
(D/'design_checks.json').write_text(json.dumps({'frames':checks,'cape_variations':cape_records,'scale_check':scale_check,'compression':compression['compression']},indent=2),encoding='utf8')
np.savez(D/'final_worlds.npz',**{str(n):w for n,w in worlds.items()})
board=Image.new('RGBA',(5*320,2*340),(40,43,55,255));draw=ImageDraw.Draw(board)
for i,n in enumerate(range(44,53)):
 board.alpha_composite(rgba(worlds[n][24:104,24:104]).resize((320,320),Image.Resampling.NEAREST),(i%5*320,i//5*340+20));draw.text((i%5*320+4,i//5*340+4),str(n),fill='white')
board.save(D/'dash_sheet_4x.png')
print(json.dumps({'frames':checks,'cape':cape_records,'compression':compression['compression']}))
