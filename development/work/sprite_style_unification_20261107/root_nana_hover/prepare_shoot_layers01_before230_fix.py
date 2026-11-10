"""Join local new sleeves to the registered common body; no old pose artwork."""
from pathlib import Path
import sys,json,hashlib
import numpy as np
from PIL import Image
from scipy.ndimage import label,binary_dilation
D=Path(__file__).resolve().parent;W=D.parent;ROOT=W.parents[1];N=W/'nana_audit';S=N/'base_hover_shot_support01'
sys.path[:0]=[str(ROOT),str(N/'native_restore')]
from preview_restore import Archive,helper
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();read=lambda p:json.loads(p.read_text('utf8'));load=lambda p:np.array(Image.open(p))
Y,X=np.indices((384,384));Y-=160;X-=160
m=read(D/'input_audit.json');a=Archive((ROOT/m['input']['path']).read_bytes());assert sha(ROOT/m['input']['path'])==m['input']['sha256']
coords=read(S/'inputs_a01/manifest.json')['canonical_source_texels'];out=D/'shoot_layers_probe01';out.mkdir(exist_ok=False);frames=[]
def comp(ls,mask,arm=2):
 im=a.rgba(ls[0])
 for bit,pb in((8,8),(1,5),(4,7),(2,6)):
  if mask&bit:im.alpha_composite(a.rgba(ls[pb],32 if pb==7 and arm==2 else 16))
 return im
for n,ox,oy in[(222,-27,-9),(224,-29,-8),(226,-20,-10),(228,-17,-10),(230,-24,-11)]:
 q=n-1;oldlayers={pb:load(D/f'body_layers_probe01/layer{pb}_{q}.png')for pb in(0,5,6,7,8)}
 b=oldlayers[0].copy();b[oldlayers[8]>0]=oldlayers[8][oldlayers[8]>0];f=b.copy()
 for pb in(8,5,7,6):f[oldlayers[pb]>0]=oldlayers[pb][oldlayers[pb]>0]
 oldb,oldf=b.copy(),f.copy();arms={};masks={};guns={};skins={};sources=[]
 for form,z in [('base_legs',b),('fourth',f)]:
  if n<230:
   folder=S/'arm_joint_probe_v2';prefix=f'{form}_{n}';mask=load(folder/f'{prefix}_edit_mask.png')>0;arm=load(folder/f'{prefix}_arm_indices.png');gun=load(folder/f'{prefix}_gun_indices.png');skin=load(folder/f'{prefix}_skin_mask.png')>0
   sources+=[{'path':str((folder/f'{prefix}_{suffix}.png').relative_to(ROOT)).replace('\\','/'),'sha256':sha(folder/f'{prefix}_{suffix}.png')}for suffix in('edit_mask','arm_indices','gun_indices','skin_mask')]
  else:
   src=D/f'registered03_fit01/{form}_230_indices.png';donor=np.roll(load(src),-1,axis=1)
   mask=(X>=-35)&(X<=-4)&(Y>=-15)&(Y<=2);mask&=~((X>=-11)&(Y<=-9));mask|=(X>=-3)&(X<=0)&(Y>=-6)&(Y<=-3)
   arm=np.where(mask,donor,0).astype(np.uint8);gun=np.zeros_like(b)
   for x,y,v in coords:gun[y+oy+9+160,x+ox+23+160]=v
   barrel=(X>=ox-2)&(X<=ox+9)&(Y>=oy-3)&(Y<=oy+1)&mask;arm[barrel]=0
   skin=mask&np.isin(donor,(10,11,12,13))&(X<=ox+9)&(Y>=oy)&(Y<=oy+5)
   arm[gun>0]=gun[gun>0];arm[skin]=donor[skin];mask|=gun>0
   sources.append({'path':src.relative_to(ROOT).as_posix(),'sha256':sha(src),'arm_only_translation':[-1,0]})
  z[mask]=arm[mask];arms[form]=arm;masks[form]=mask;guns[form]=gun;skins[form]=skin
 # Both forms hold the same gun with the same hand. Keep sleeve differences.
 hand=(X>=ox-2)&(X<=ox+9)&(Y>=oy-3)&(Y<=oy+5)
 f[hand]=b[hand];full=np.where(f,f,b).astype(np.uint8)
 own=load(D/f'body_layers_probe01/owner_{q}.png');own[masks['base_legs']|masks['fourth']|hand]=7
 legs=oldlayers[8]>0;assert np.array_equal(b[legs],oldb[legs]) and np.array_equal(full[legs],oldf[legs])
 diff=((full!=b)|np.array([a.words[i]!=a.words[i+16]for i in range(16)])[full])&(full>0)&~legs
 ls={0:np.where(legs,0,b).astype(np.uint8),8:oldlayers[8],**{pb:np.where(diff&(own==pb),full,0).astype(np.uint8)for pb in(5,6,7)}}
 assert comp(ls,8).tobytes()==a.rgba(b).tobytes()
 records=[]
 for mask in range(16):
  for armtype in(1,2):records.append({'mask':mask,'arm':armtype,'components8':int(label(np.array(comp(ls,mask,armtype))[:,:,3]>0,np.ones((3,3)))[1])})
 contacts={}
 for form,z in [('base_legs',b),('fourth',full)]:
  g=guns[form]>0;s=hand&np.isin(z,(10,11,12,13));contacts[form]=int((binary_dilation(s)&g).sum())
  Image.fromarray(z).save(out/f'{form}_{n}_indices.png')
 for pb,z in ls.items():Image.fromarray(z).save(out/f'layer{pb}_{n}.png')
 helper.grid([(f'shooting {n}',[('idle',a.composite(0)[0]),('new basic hover',comp(ls,8)),('Fourth idle',a.composite(0,15)[0]),('new Fourth hover',comp(ls,15))])],out/f'comparison_{n}.png',6)
 helper.grid([(f'partial shooting {n}',[(str(mask),comp(ls,mask))for mask in (8,9,10,12,13,14,15)])],out/f'partial_{n}.png',5)
 frames.append({'ref':n,'sources':sources,'body_ref':q,'engine_origin':[ox,oy],'hand_gun_contacts4':contacts,'all_foot_pixels_preserved':True,'layer_hashes':{str(pb):hashlib.sha256(z.tobytes()).hexdigest()for pb,z in ls.items()},'partial_components':records,'basic_under_transparent_fourth':int(((f==0)&(b>0)).sum())})
(out/'manifest.json').write_text(json.dumps({'parent_arc':m['input']['path'],'parent_sha256':m['input']['sha256'],'refs':[222,224,226,228,230],'frames':frames,'native_packed':False,'runtime_verified':False},ensure_ascii=False,indent=2)+'\n','utf8')
print(json.dumps([{'ref':q['ref'],'contacts':q['hand_gun_contacts4'],'components':sorted({s['components8']for s in q['partial_components']if s['mask']&8})}for q in frames]))
