"""새 저체력 원화의 공통 머리/피부/머리카락과 네 의상 파츠를 분리한다."""
from pathlib import Path
import sys,json
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
import numpy as np
from PIL import Image,ImageDraw
from scripts.export_x_consistency import Archive,page
from scripts.c01_audio_build import read_disc
from native_pose_pack import SOURCE,SOURCE_SHA,sha,need,write
from src.psx_disc import file_hash

D=H/'lowhp_generation02/accepted_head'
NATIVE_INPUT_SHA={'base_120_indices.png': 'a4fae01ec864faf33a3bfa919d350602d55211a57b1127bfb1400b646b9d6c36', 'fourth_body_indices.png': 'd40700ea3a9c57f36fe86b43e1e7ca6124dd463df4d7bed0b1b02af7ae39681f', 'accepted_head_indices.png': '8b1cc50c3e7c969bfd923b5054b268703d5b1aa1866deadfdf2edb0bfd591987', 'accepted_head_ornament_indices.png': 'ea1fee4f6a63ceee946f50b91cf29e6ec08db391966c11fbbaa098b1d41b9840'}
def polygon(points):
 im=Image.new('1',(384,384));ImageDraw.Draw(im).polygon([(x+160,y+160)for x,y in points],fill=1);return np.array(im,bool)

def breathe(a,delta):
 # Same accepted phase: head, torso, hip and thighs share motion; soles fixed.
 result=a.copy()
 for y in range(135,183):
  local=y-135;shift=delta if local<35 else round(delta*max(0,43-local)/8)
  result[y]=a[y-shift]
 need(np.array_equal(result[178:],a[178:]),'Feet moved')
 return result

def make_targets(arc):
 need(sha((H/'lowhp_generation02/generated.png').read_bytes())=='cc71332d171b7ecab1e97b794b5bb2a77454a6dc19669d47a3b9a6974890ad96','New art changed')
 for name,expected in NATIVE_INPUT_SHA.items():need(sha((D/name).read_bytes())==expected,'Registered native input changed: '+name)
 base=np.array(Image.open(D/'base_120_indices.png'));fourth=np.array(Image.open(D/'fourth_body_indices.png'));head=np.array(Image.open(D/'accepted_head_indices.png'));ornament=np.array(Image.open(D/'accepted_head_ornament_indices.png'))
 # Shared body details are from the NEW base painting, never old coarse lowHP.
 hair=polygon([(5,-4),(12,-4),(12,5),(8,6),(8,0),(5,-1)])|polygon([(7,12),(12,12),(12,21),(5,21),(5,18),(7,17)])
 hand=polygon([(-4,-4),(0,-4),(0,1),(-4,1)])|polygon([(3,10),(5,10),(5,11),(3,11)])
 hand&=np.isin(base,[10,11,12,13]);common=(hair|hand)&(base>0)
 fourth[common]=0
 # Overlay cannot erase base. Four NEW outline corners remain exactly base15.
 outside=(base>0)&(fourth==0)&(head==0)&~common
 need(int(outside.sum())==4 and np.all(base[outside]==15),'Unexpected outside clothing')
 yy,xx=np.indices(base.shape);owner=np.full(base.shape,6,np.uint8)
 arms=polygon([(-10,-4),(-5,-4),(-5,0),(-3,3),(-3,6),(-6,9),(-11,9)])|polygon([(3,-3),(7,-3),(9,3),(9,9),(6,12),(3,12)])
 legs=(yy>=173)&(xx>=154)&(xx<=165)
 owner[arms]=7;owner[legs]=8
 # The accepted head and its ornament are used at the correct common origin.
 ref={0:base,5:ornament,6:np.zeros_like(base),7:np.zeros_like(base),8:np.zeros_like(base)}
 rgba_base=np.array(arc.rgba(base));rgba_full=np.array(arc.rgba(fourth,16))
 needed=(fourth>0)&np.any(rgba_base!=rgba_full,axis=2)
 for b in(6,7,8):ref[b][needed&(owner==b)]=fourth[needed&(owner==b)]
 need(int(base[155,154])==13,'Accepted lower lip position changed')
 targets={};records=[]
 for n in range(120,126):
  delta=-((n-120)//2);layers={b:v.copy()for b,v in ref.items()}
  # Original mouth alternation keeps its source color; locate it on the new lower lip.
  if n%2:layers[0][155,154]=11
  layers={b:breathe(v,delta)for b,v in layers.items()};targets[n]=layers
  records.append({'ref':n,'relative_breathing_shift':delta,'feet_rows178_plus_exact':True,'mouth_open':bool(n%2),'mouth_source_index':11 if n%2 else 13,'mouth_master_world':[-6,-5],'head_source_ref':116,'layer_pixels':{str(b):int((v>0).sum())for b,v in layers.items()}})
 return targets,{'source_art_sha256':sha((H/'lowhp_generation02/generated.png').read_bytes()),'accepted_head_ref':116,'head_region':'y<156','same_angle_head_authorized':True,'old_lowHP_head_or_body_copied':False,'common_hair_from_new_base_pixels':int((hair&(base>0)).sum()),'common_hands_from_new_base_pixels':int(hand.sum()),'base_outline_corners_preserved':[[int(x)-160,int(y)-160]for y,x in zip(*np.nonzero(outside))],'native_timing_table_changed':False,'body_width_not_stretched':True,'records':records},owner,common

def compose(a,layers,mask,arm=2):
 im=a.rgba(layers[0])
 for bit,b in((8,8),(1,5),(4,7),(2,6)):
  if mask&bit:im.alpha_composite(a.rgba(layers[b],32 if b==7 and arm==2 else 16))
 return im

def main():
 need(file_hash(SOURCE)==SOURCE_SHA,'Source changed');a=Archive(read_disc(SOURCE,('PL00_U.ARC',))[0]['PL00_U.ARC']);targets,info,owner,common=make_targets(a)
 out=H/'lowhp_final01';need(not out.exists(),'Output exists');out.mkdir()
 for n,layers in targets.items():
  for b,v in layers.items():Image.fromarray(v).save(out/f'{n:03}_layer{b}.png')
  for mask,name in((0,'base'),(15,'fourth')):compose(a,layers,mask).save(out/f'{name}_{n:03}.png')
 for mask,name in((0,'base'),(15,'fourth')):
  items=[]
  for n in targets:items.extend([(f'{name} {n} current',a.composite(n,mask)[0]),(f'{name} {n} new',compose(a,targets[n],mask))])
  page(items,a.composite(0,mask)[0],out/f'{name}_comparison.png',cols=2,scale=4)
 page([(f'120 mask{m:02X}',compose(a,targets[120],m))for m in range(16)],a.composite(0,15)[0],out/'partial_masks.png',cols=4,scale=4)
 Image.fromarray(owner).save(out/'part_owner_indices.png');Image.fromarray(common.astype(np.uint8)*255).save(out/'new_common_hair_hands_mask.png');write(out/'provenance.json',info)
 print(json.dumps({'outside':info['base_outline_corners_preserved'],'pixels':info['records'][0]['layer_pixels']}))
if __name__=='__main__':main()

