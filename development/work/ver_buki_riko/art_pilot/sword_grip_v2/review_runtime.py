"""Compare rendered short-grip body plus untouched effects, using captured VRAM."""
from assemble_grip import *
from src.epsxe_state import framebuffer,match_sprite
B=ROOT/'out/ver_buki_riko/riko_motion_20261024T054713269447Z'
EXPECTED_HASH='3f4bc2c8112245817397c9a111f1b18ecd06890dfd06d05a59a866e1fd14ea71'

def review(folder):
 report=json.loads((folder/'verification.local.json').read_text());assert report['modified_bin_sha256']==EXPECTED_HASH
 manifest=json.loads((B/'manifest.json').read_text());worlds=np.load(D/'final_worlds.npz');records=[]
 for n in BODY:
  assert manifest['frame_inputs'][str(n)]['sha256']==sha256((D/f'frame_{n:03d}.png').read_bytes())
  if str(n) not in report['frames']:continue
  full=composed(n,worlds[str(n)]);sprite=full.crop(full.getbbox());matches=[]
  for path in folder.glob(f'*vram*_{n:03d}.bin'):
   vram=path.read_bytes()
   if len(vram)!=1048576:continue
   for page in (0,256):
    screen=framebuffer(vram,0,page);m=match_sprite(screen,sprite)
    if m:
     target=folder/f'grip_composite_actual_{n:03d}_{page}.png';screen.save(target);sprite.save(folder/f'grip_composite_expected_{n:03d}.png')
     altered=np.array(sprite.convert('RGBA'));ys,xs=np.nonzero(altered[:,:,3]);y,x=ys[len(ys)//2],xs[len(xs)//2];altered[y,x,0]^=127
     assert not match_sprite(screen,Image.fromarray(altered)),'Corrupted sprite accepted'
     matches.append({'vram':path.name,'page_y':page,'matches':m,'actual':target.name,'one_pixel_corruption_rejected':True})
  records.append({'body_frame':n,'effect_frame':PAIRS.get(n),'whole_composite_verified':bool(matches),'evidence':matches})
 write(folder/'grip_composite_verification.json',{'build':str(B),'bin_sha256':EXPECTED_HASH,'runtime_report':str(folder/'verification.local.json'),'full_opaque_comparison':True,'frames':records})
 print(json.dumps({'folder':str(folder),'visible_composite_verified':[r['body_frame'] for r in records if r['whole_composite_verified']]}))

if __name__=='__main__':review(Path(sys.argv[1]))
