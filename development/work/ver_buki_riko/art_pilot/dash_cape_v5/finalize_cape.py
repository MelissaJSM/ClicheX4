import sys,shutil
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent.parent/'dash_v1'))
from fit_dash import *
from scripts.build_riko_idle import patch_frames,check_motion_scale
from scripts.discover_inputs import sha256
D=Path(__file__).resolve().parent; previous=D.parent/'dash_v2'
recipe=json.loads((previous/'recipe.json').read_text('utf8'))
worlds={int(n):v.copy() for n,v in np.load(previous/'final_worlds.npz').items()}
sources=np.load(D/'source_worlds.npz');yy,xx=np.indices((128,128));x=xx-64;y=yy-64
# Registration of the generated cloth layer moves it two pixels upward to fit
# wholly inside the three unique 16x16 tiles. Shared lower tiles never cut it.
cape_mask=((x>=1)&(x<32)&(y>=-6)&(y<10))|((x>=18)&(x<32)&(y>=10)&(y<12))
# Include the missing shoulder junction, which the v3 x>=1 mask excluded.
shoulder_junction=(x>=-4)&(x<8)&(y>=2)&(y<9)
protected_head=np.zeros((128,128),dtype=bool)
protected_head[51:70,42:65]=hm
cape_mask=(cape_mask|shoulder_junction)&~protected_head
root_mask=cape_mask&(x<1)
checks=[];base=worlds[46].copy();root=np.roll(sources['46'],-2,axis=0)
for n in (46,47,48):
 layer=np.roll(sources[str(n)],-2,axis=0)
 # All lower shared pixels are cleared of the obsolete floating cape tip.
 layer[(x>=18)&(y>=10)&(y<12)]=0
 layer[root_mask]=root[root_mask]
 w=base.copy();w[cape_mask]=layer[cape_mask]
 assert np.array_equal(w[~cape_mask],base[~cape_mask])
 assert not ((w!=0)&~geometry[n][2]).any()
 assert len(component(w!=0))==1
 # A connected whole-body silhouette is insufficient: the old waist path
 # concealed an empty shoulder-to-cape junction. Check that junction itself.
 attachment=w[68:71,63:71]  # world x=-1..6, y=4..6
 assert np.all(attachment!=0),'Transparent gap at the shoulder attachment'
 worlds[n]=w
 # Measure cloth thickness at the former thin connector, excluding dark outline.
 thickness={str(cx):int(np.isin(w[64:73,64+cx],[2,6,10,7,12,15]).sum()) for cx in range(1,7)}
 assert min(thickness.values())>=2,thickness
 checks.append({'frame':n,'cape_root_cloth_pixels_by_column':thickness,'shoulder_junction_world':[-1,4,7,7],'shoulder_junction_transparent_pixels':int((attachment==0).sum()),'outside_cape_exact':True,'components':1,'outside_pixels':0})
frames={}
for key,r in recipe['frames'].items():
 n=int(key);dest=D/r['file']
 if n in (46,47,48):
  size,b,_=geometry[n];w=worlds[n];canvas=w[64+b[1]:64+b[3],64+b[0]:64+b[2]]
  frames[n]=(canvas.tobytes(),size);save_image(*frames[n],words,dest)
 else:
  shutil.copyfile(previous/r['file'],dest);frames[n]=read_indexed_png(dest,words)
 r['sha256']=sha256(dest.read_bytes())
reference=read_indexed_png(ROOT/'out/ver_buki_riko/riko_pilot_20261023T082720987715Z/riko_idle147_indexed.png',words)
scale=check_motion_scale(recipe,frames,gfx,parts,reference);_,compression=patch_frames(arc,gmeta,gfx,parts,frames,pal)
recipe['dash_production']['revision']='Continuous shoulder-attached cape; generated cloth inside unique tiles; common shoulder junction only; whole cape surface animated without a mid-cape splice'
recipe['dash_production']['previous_bin_sha256']='a2ff0b8c3ec3fd3748a2058725f2b7764a899c13a1e859b11b4c46a885b95c7f'
(D/'recipe.json').write_text(json.dumps(recipe,indent=2),encoding='utf8')
(D/'design_checks.json').write_text(json.dumps({'cape_checks':checks,'scale_check':scale,'compression':compression['compression'],'generated_layer_registration':[0,-2],'body_head_and_limbs_outside_cape_preserved':True},indent=2),encoding='utf8')
np.savez(D/'final_worlds.npz',**{str(n):w for n,w in worlds.items()})
board=Image.new('RGBA',(1200,800),(40,43,55,255));draw=ImageDraw.Draw(board)
for i,n in enumerate((46,47,48)):
 for row,src in enumerate((np.load(previous/'final_worlds.npz')[str(n)],worlds[n])):
  board.alpha_composite(rgba(src[38:102,32:96]).resize((400,400),Image.Resampling.NEAREST),(400*i,400*row))
  draw.text((400*i+8,400*row+8),f'{"Before" if row==0 else "After"} {n}',fill='white')
board.save(D/'cape_before_after.png')
print(json.dumps({'checks':checks,'compression':[v for v in compression['compression'] if v['frames']==[46,47,48]]}))
