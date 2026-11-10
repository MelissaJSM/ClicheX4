"""새 등장 네 자세와 원래 광선/번개를 동일 원점에서 구성한다."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
from scripts.export_x_consistency import Archive,page
from register_ladder_parts import poly,compose
from probe_arrival_silhouettes import parts,over
from analyze_arrival_effects import shift
PARENT_SHA='02f092d7b0ed67ce1174fd30250b86f73c81b42dbfa08c8c3ca06fc638b89acf'
REFS={130,131,133,134,135,136,137,138,139}

def make(data):
 need(sha(data)==PARENT_SHA,'Wrong victory parent');a=Archive(data);d=H/'arrival_native01';targets={n:{b:a.layer(n,b)[0].copy()for b in(0,5,6,7,8)}for n in REFS};native={}
 for n in(133,135,137,138):
  q=np.array(Image.open(d/f'base_{n:03}_indices.png'));native[n]=shift(q,0,-1)if n in(133,135)else q
 for n in(133,135):targets[n][0]=native[n]
 fx136=parts(a,136,[7,8]);fx137=parts(a,137,[6,8]);targets[136][0]=over(shift(native[135],0,-1),fx136);targets[137][0]=over(native[137],fx137)
 base=native[138];rawfull=np.array(Image.open(d/'fourth_138_indices.png'));full=shift(rawfull,-2,0);own=np.full(base.shape,6,np.uint8)
 own[poly([(-8,9),(5,9),(6,24),(-9,24)])]=8
 own[poly([(-15,-28),(2,-28),(3,-20),(12,-21),(14,-8),(10,0),(12,8),(5,8),(2,-1),(-9,-3),(-15,-10)])]=5
 armregion=poly([(-5,-34),(6,-34),(8,-24),(8,-7),(3,-2),(-1,-5),(-2,-23)])
 own[armregion]=7
 # Hair passes in front of the inner raised forearm. Keep its actual new source
 # color cluster with Head; do not split the arm by an arbitrary square.
 yy,xx=np.indices(base.shape);hairfront=armregion&(yy>=136)&(yy<154)&(xx<162)&np.isin(base,[2,5,8,14]);own[hairfront]=5
 rgb=np.array([[(w>>s&31)*255//31 for s in(0,5,10)]for w in a.words[:32]],np.int32)
 nearest={i:int(((rgb[17:32]-rgb[i])**2).sum(1).argmin())+1 for i in range(1,16)};fills=[]
 for y,x in zip(*np.nonzero((base>0)&(full==0))):
  src=int(base[y,x]);bank=int(own[y,x]);color=nearest[src]
  if bank!=5:color={1:2,4:11,10:10,11:11,12:9,13:9,15:1}.get(src,color)
  full[y,x]=color;fills.append([int(x)-160,int(y)-160,src,color,bank])
 need(np.array_equal(shift(rawfull,-2,0)[shift(rawfull,-2,0)>0],full[shift(rawfull,-2,0)>0]),'New Fourth art overwritten')
 layers={0:base,**{b:np.where(own==b,full,0).astype(np.uint8)for b in(5,6,7,8)}};targets[138]=layers;targets[139]={b:shift(q,0,-1)for b,q in layers.items()}
 oldbody=parts(a,131,range(16,24));ring=parts(a,131,range(16));newbody=np.where(native[133]>0,9,0).astype(np.uint8);targets[131][0]=over(ring,newbody)
 bg129=a.layer(129)[0];targets[134][0]=over(bg129,np.where(native[133]>0,np.where(native[133]==15,5,9),0).astype(np.uint8))
 # Historical130 background is re-extracted from its native original energy
 # material map. Retain the three old symmetry-correction pixels elsewhere.
 bg130=np.array(Image.open(H/'arrival_remaining01/silhouettes/130_background_indices.png'))
 v=a.layer(130)[0].copy();v[oldbody>0]=bg130[oldbody>0];targets[130][0]=over(v,newbody)
 changed_region=(oldbody>0)|(newbody>0);need(np.array_equal(targets[130][0][~changed_region],a.layer(130)[0][~changed_region]),'130 outer energy changed')
 need(np.array_equal(targets[131][0][~changed_region],a.layer(131)[0][~changed_region]),'131 outer energy changed')
 need(np.array_equal(parts(a,140,[0,1,2,3,4,5,6,9])>0,a.layer(0)[0]>0),'Existing140 silhouette no longer equals idle')
 report=dict(source_arc_sha256=sha(data),selected_refs=sorted(REFS),global_translations={'133':[0,-1],'135':[0,-1],'138_fourth':[-2,0]},shared_body_136=[135,0,-1],shared_all_layers_139=[138,0,-1],fourth138_new_source_exact_after_rigid_translation=True,edge_registration=fills,external_sparks_136_137_exact=True,frame130_131_outer_energy_outside_body_union_exact=True,frame134_same_bright_mapping_and129_background=True,frame140_already_current_idle_silhouette_preserved=True,frame141142_accepted_idle_connection_preserved=True,frame132_ring_display_must_preserve=True,old_coarse_head_body_overwrite=False,body_or_arm_resize=False,source_hands_are_redrawn_not_pixel_locked=True,not_packed=True)
 return a,targets,own,report

def main():
 data=(H/'prepared_victory_ladder01/PL00_U.ARC').read_bytes();a,targets,own,report=make(data);out=H/'arrival_targets01';need(not out.exists(),'Output exists');out.mkdir()
 for n,layers in targets.items():
  for b,q in layers.items():Image.fromarray(q).save(out/f'{n:03}_bank{b}_indices.png')
 Image.fromarray(own).save(out/'138_owner.png')
 for form,mask in(('base',0),('fourth',15)):
  keys=[133,135,137,138]if mask==0 else[138,139]
  page([(f'{n} {label}',pic)for n in keys for label,pic in[('before',a.composite(n,mask)[0]),('registered',compose(a,targets[n],mask))]],a.composite(0,mask)[0],out/f'{form}_comparison.png',cols=2,scale=5)
 for n in(138,139):page([(f'{n} mask{m:X}',compose(a,targets[n],m))for m in range(16)],a.composite(0,15)[0],out/f'partial_{n}.png',cols=4,scale=4)
 page([(f'{n} {label}',pic)for n in(130,131,134,136,137)for label,pic in[('before',a.composite(n,0)[0]),('registered',compose(a,targets[n],0))]],a.composite(0,0)[0],out/'effects_comparison.png',cols=2,scale=4)
 write(out/'registration.json',report);print(json.dumps(dict(refs=sorted(targets),edge_pixels=len(report['edge_registration']))))
if __name__=='__main__':main()
