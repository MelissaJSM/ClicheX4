from inspect_fit import *
from scripts.extract_zero import save_image
from scripts.discover_inputs import sha256
from src.psx_air_spin import head_views,validate_heads,SIZED_SCOPE as SCOPE,validate_body_mass
from src.psx_bank_patch import patch_bank
from src.psx_frame_edit import read_indexed_png
from scripts.build_riko_bank1 import WALL_BODY,WALL_EFFECTS
from src.psx_player import decode_stream,composition_frame,compose_indices

def run():
 prev=ROOT/'work/ver_buki_riko/art_pilot/wall_saber_v2/recipe.json';recipe=json.loads(prev.read_text('utf8'))
 record=json.loads((D/'fit.json').read_text('utf8'));rotations=np.load(D/'rotations.npz');pivot=json.loads((D/'pivot.json').read_text('utf8'))
 if any(pivot['outside']) or pivot['translation']!=[0,0]:raise ValueError('No common uncut rotation pivot')
 worlds={n:rotations[str(n)] for n in BODY[2:]};heads={};frames={};records={};checks=[]
 for n in (132,160):
  r=next(r for r in record if r['frame']==n);path=ROOT/'out/ver_buki_riko/riko_bank1_20261025T090314908139Z'/('frame_229.png' if n==132 else 'frame_213.png')
  a=np.array(Image.open(path));yy,xx=np.nonzero(a);a=a[yy.min():yy.max()+1,xx.min():xx.max()+1]
  w=np.zeros((192,192),np.uint8);x,y=r['position'];w[96+y:96+y+a.shape[0],96+x:96+x+a.shape[1]]=a;worlds[n]=w
  matches=[]
  for hy in range(y,y+a.shape[0]-18):
   for hx in range(x,x+a.shape[1]-22):
    if np.array_equal(w[96+hy:115+hy,96+hx:119+hx][front!=0],front[front!=0]):matches.append([hx,hy])
  if len(matches)!=1:raise ValueError(('Lead reference',n,matches))
  heads[str(n)]=matches[0]
 hp=np.load(D/'base_sample.npz')['head'];bx,by=pivot['base_position']
 registration={'base_head_world':[int(bx+hp[0]),int(by+hp[1])],'lead_head_world':heads,'rotation_degrees':list(range(0,360,45)),'pivot_world':pivot['pivot_world']}
 for n in sorted(set(BODY)|set(EFFECT)):
  a,b,safe=original(n)
  if n in worlds:
   w=worlds[n];bad=int(np.count_nonzero((w!=0)&~safe));groups=component(w!=0)
   if bad:raise ValueError(('Outside original parts',n,bad))
   a=w[96+b[1]:96+b[3],96+b[0]:96+b[2]]
   checks.append({'frame':n,'outside':bad,'components':[len(g) for g in groups]})
  path=D/f'bank1_{n:03d}.png';size=(a.shape[1],a.shape[0]);save_image(a.tobytes(),size,pal,path)
  frames[n]=(a.tobytes(),size);records[str(n)]={'file':path.name,'sha256':sha256(path.read_bytes())}
 # The wall assets stay byte-identical and are carried into the cumulative recipe.
 for n in sorted(WALL_BODY|WALL_EFFECTS):
  p=prev.parent/recipe['frames'][str(n)]['file'];shutil.copyfile(p,D/p.name);records[str(n)]=recipe['frames'][str(n)];frames[n]=read_indexed_png(p,pal)
 ref=(front.tobytes(),(23,19));bounds={n:original(n)[1] for n in BODY}
 hc=validate_heads({n:frames[n] for n in BODY},bounds,*ref,(0,0,23,19),registration)
 _,packing=patch_bank(gfx,parts,1,5,frames,set(EFFECT)|WALL_EFFECTS,clear_unreferenced=True)
 body_path=ROOT/'config/riko_spin_body_standard.json'
 size_check=validate_body_mass(frames,head_views(*ref,(0,0,23,19),registration),446)
 (D/'body_size_checks.json').write_text(json.dumps(size_check,indent=2),'utf8')
 recipe.update(scope=SCOPE,spin_body_standard_sha256=sha256(body_path.read_bytes()),frames=records,preserved_effect_frames=sorted(set(EFFECT)|WALL_EFFECTS),
  spin_registration=registration,spin_generated_art='generated_spin.png',spin_generated_art_sha256=sha256((D/'generated_spin.png').read_bytes()),
  spin_source_scale=.04,wall_recipe=str(prev.relative_to(ROOT)),wall_recipe_sha256=sha256(prev.read_bytes()),runtime_verified=False,
  art_revision='native_style_body_size_correction_after_v2',native_style_reference='../air_spin_v2/native_crouch_target.png')
 for n,rect in hc['head_rectangles'].items():recipe['body_standard']['head_world_positions'][n]=rect[:2]
 recipe['body_standard']['head_sizes']={**{str(n):[23,19] for n in WALL_BODY},**{n:r[2:] for n,r in hc['head_rectangles'].items()}}
 for name,obj in [('recipe.json',recipe),('packing_checks.json',packing),('art_checks.json',checks),('head_checks.json',hc)]:
  (D/name).write_text(json.dumps(obj,indent=2)+'\n','utf8')
 np.savez(D/'final_worlds.npz',**{str(n):w for n,w in worlds.items()})
 board=Image.new('RGBA',(5*320,2*300),(32,36,48));draw=ImageDraw.Draw(board);epal=__import__('work.ver_buki_riko.art_pilot.sword_v1.inspect_sword',fromlist=['epal']).epal
 gif=[]
 for i,n in enumerate([132,*BODY[2:],160]):
  cell=rgba(worlds[n]);e=n+1 if n in BODY[2:] else None
  if e:
   a,b,_=original(e);cell.alpha_composite(rgba(a,epal),(96+b[0],96+b[1]))
  pic=cell.crop((32,32,144,144)).resize((336,336),Image.Resampling.NEAREST)
  bg=Image.new('RGBA',pic.size,(32,36,48));bg.alpha_composite(pic);gif.append(bg.convert('RGB'))
  board.alpha_composite(cell.crop((48,44,128,114)).resize((320,280),Image.Resampling.NEAREST),(i%5*320,i//5*300+20));draw.text((i%5*320+4,i//5*300+3),f'{n} STATIC',fill='white')
 board.save(D/'effect_review.png');gif[0].save(D/'spin_preview.gif',save_all=True,append_images=gif[1:],duration=[80]*9+[180],loop=0)
 print(json.dumps({'body':len(BODY),'effects_including_shared_133':len(EFFECT),'min_compression_margin':min(r['untouched_tail_bytes'] for r in packing['compression']),'checks':checks}))
if __name__=='__main__':run()
