from pathlib import Path
import sys,json,struct,shutil,numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT))
from scripts.discover_inputs import psx_arc
from scripts.extract_zero import save_image
from src.psx_static_effect import compose_static,patch_static,sha256
from src.psx_player import composition_frame
from work.ver_buki_riko.art_pilot.wall_saber_v1.fit_wall import original
D=Path(__file__).parent;V1=D.with_name('rakuhouha_v1')
arc=(ROOT/'out/ver_buki_riko/riko_bank1_20261025T123814831210Z/modified.arc').read_bytes();es=psx_arc(arc)
def ent(k):
 e=next(e for e in es if e['type']==k);return arc[e['offset']:e['offset']+e['size']]
tex=ent('0x10206');parts=ent('0x3');words=struct.unpack('<16H',(D/'effect_palette.bin').read_bytes())
o,b,_=original(182);zero=np.zeros((192,192),np.uint8);zero[95+b[1]:95+b[3],96+b[0]:96+b[2]]=o
worlds=np.load(V1/'final_worlds.npz');frames={};records={};comps={};masks={}
remaps={23:{0:0,1:9,2:9,3:8,4:8,5:8,6:7,7:8,8:7,9:7,10:6,11:6,12:6,13:5,14:6,15:5},24:{0:0,1:15,2:15,3:14,4:14,5:14,6:12,7:14,8:11,9:12,10:10,11:10,12:10,13:5,14:10,15:5}}
for n,body in ((23,185),(24,182)):
 c=composition_frame(parts,6,n);comps[n]=c;data,size,b,prov=compose_static(tex,c);a=np.frombuffer(data,np.uint8).reshape(size[1],size[0]);out=a.copy()
 old=(zero[96+b[1]:96+b[3],96+b[0]:96+b[2]]>0)&(a!=0);old[:max(0,-17-b[1])]=False
 # The source body is exactly at the original body's world y-1; the long ponytail is absent from the effect.
 if n==23:assert np.count_nonzero(np.isin(a,[6,7,8,9])&~old)==0
 counts={}
 for locs in prov:
  for loc in locs:counts[loc]=counts.get(loc,0)+1
 unique=np.array([len(l)==1 and counts[l[0]]==1 for l in prov]).reshape(a.shape)
 assert not np.any(old&~unique)
 # Fill only the old body's footprint. Use the clean mirrored dome when available,
 # otherwise the two nearest unmasked pixels on that scanline.
 for yy,xx in zip(*np.nonzero(old)):
  mirror=-12-(xx+b[0])-b[0]
  if 0<=mirror<size[0] and not old[yy,mirror] and a[yy,mirror]:value=a[yy,mirror]
  else:
   available=np.flatnonzero((~old[yy])&(a[yy]!=0))
   if not len(available):
    out[yy,xx]=0;continue
   closest=available[np.argsort(abs(available-xx),kind='stable')[:2]]
   value=a[yy,closest[0]]
   if n==24 and 13 in a[yy,available]:value=13
  out[yy,xx]=value
 riko=worlds[str(body)][96+b[1]:96+b[3],96+b[0]:96+b[2]]
 overlay=(riko>0)&(a>0)&unique
 remap=np.array([remaps[n][i] for i in range(16)],np.uint8)
 out[overlay]=remap[riko[overlay]]
 assert np.array_equal(out[~(old|overlay)],a[~(old|overlay)])
 assert np.array_equal((out==0)[~old],(a==0)[~old])
 frames[n]=(out.tobytes(),size);im=save_image(out.tobytes(),size,words,D/f'effect_{n}.png');masks[str(n)]=old|overlay
 records[str(n)]={'file':f'effect_{n}.png','sha256':sha256((D/f'effect_{n}.png').read_bytes()),'bounds':b,'body_source':body,'body_source_sha256':sha256((V1/f'bank1_{body:03d}.png').read_bytes()),'old_body_mask_pixels':int(old.sum()),'riko_tint_pixels':int(overlay.sum()),'transparency_outside_old_body_unchanged':True,'original_body_world_offset':[0,-1],'riko_world_offset':[0,0],'tint_map':remaps[n]}
changed=patch_static(tex,comps,frames);changed_tiles=sorted({(i//128//16)*16+(i%128)//8 for i,(a,b) in enumerate(zip(tex,changed)) if a!=b})
users=[]
for bi in (1,2,3,4,6):
 for n in range(composition_frame(parts,bi,0)['bank_frame_count']):
  c=composition_frame(parts,bi,n)
  if set(changed_tiles)&{p['page']*256+p['tile'] for p in c['parts']}:users.append([bi,n])
assert users==[[6,23],[6,24]],users
for name in ('recipe.json',):shutil.copyfile(V1/name,D/name)
for p in V1.glob('bank1_*.png'):shutil.copyfile(p,D/p.name)
np.savez(D/'edit_masks.npz',**masks)
recipe={'kind':'us_rakuhouha_embedded_body_v1','source_texture_sha256':sha256(tex),'parts_sha256':sha256(parts),'palette_file':'effect_palette.bin','palette_sha256':sha256((D/'effect_palette.bin').read_bytes()),'palette_evidence_file':'../../burst_layers/20261025T124957930178Z/vram_08.bin','palette_evidence_sha256':sha256((ROOT/'work/ver_buki_riko/burst_layers/20261025T124957930178Z/vram_08.bin').read_bytes()),'frames':records,'changed_tiles':changed_tiles,'only_composition_users':users,'modified_texture_sha256':sha256(changed),'original_alpha_outside_old_body_preserved':True,'projectile_frames_27_72_unchanged':True}
(D/'static_effects.json').write_text(json.dumps(recipe,indent=2),'utf8');(D/'candidate_static_texture.bin').write_bytes(changed)
r=json.loads((D/'recipe.json').read_text());r['static_effect_set']='static_effects.json';(D/'recipe.json').write_text(json.dumps(r,indent=2),'utf8')
board=Image.new('RGB',(960,720),(32,36,48));draw=ImageDraw.Draw(board)
for i,n in enumerate((23,24)):
 for j,name in enumerate((f'original_effect_{n}.png',f'effect_{n}.png')):
  im=Image.open(D/name).convert('RGBA');im=im.resize((im.width*5,im.height*5),Image.Resampling.NEAREST);x=i*480;y=j*360;board.paste(im,(x+(480-im.width)//2,y+20),im);draw.text((x+10,y+2),f'{n} '+('SOURCE ZERO' if j==0 else 'RIKO SAME BODY'),fill='white')
board.save(D/'effect_review.png');print(json.dumps({'changed_tiles':changed_tiles,'users':users,'frames':records}))
