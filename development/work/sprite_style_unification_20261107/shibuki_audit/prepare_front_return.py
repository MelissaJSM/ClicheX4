"""새 정면156과 귀환157/158을 고정범위에 무손실 등록한다."""
from pathlib import Path
import sys,json
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
import numpy as np
from PIL import Image
from scripts.c01_audio_build import read_disc
from scripts.export_x_consistency import Archive,page
from src.psx_disc import file_hash
from native_pose_pack import SOURCE,SOURCE_SHA,sha,need,write,load
from prepare_return158 import targets as old_return_targets,shift
import pack_lowhp_return as native_packer

PARENT_SHA='b3f16cb0cb82c694d0330d27b63a6092bec31156979762cab7922769cee037a1'
SELECTED={156,157,158}
PARTS=(0,5,6,7,8)
ART=H/'front156_aligned02'
ART_HASH={'base_indices.png':'efbad6eb37e1ffed2fb1742913c1f6b902c27374a121fa31c9953b4b4c7eb98e','fourth_overlay_indices.png':'a6fe5a9b101240399f8800c0be1d7bf8e24f6dc85d8745ecc1fc0fe4cd848590'}

def outline(v,color):
 mask=v>0;p=np.pad(mask,1);edge=(p[:-2,1:-1]|p[2:,1:-1]|p[1:-1,:-2]|p[1:-1,2:])&~mask
 out=v.copy();out[edge]=color;return out

def compose(a,layers,mask=15,arm=2):
 im=a.rgba(layers[0])
 for bit,b in((8,8),(1,5),(4,7),(2,6)):
  if mask&bit:im.alpha_composite(a.rgba(layers[b],32 if b==7 and arm==2 else 16))
 return im

def targets(original):
 for name,h in ART_HASH.items():need(sha((ART/name).read_bytes())==h,'Registered new art hash differs')
 base=load(ART/'base_indices.png');overlay=load(ART/'fourth_overlay_indices.png')
 yy,xx=np.indices(base.shape);owner=np.full(base.shape,6,np.uint8)
 owner[yy<156]=5
 owner[(yy>=156)&(yy<168)&((xx<=153)|(xx>=168))]=7
 owner[(yy>=173)&(xx>=154)&(xx<=166)]=8
 layers={0:base,**{b:np.where(owner==b,overlay,0).astype(np.uint8)for b in(5,6,7,8)}}
 want=original.rgba(base);want.alpha_composite(original.rgba(overlay,16))
 need(compose(original,layers).tobytes()==want.tobytes(),'Semantic ownership alters adopted artwork')
 desired={156:layers}
 desired[157]={b:shift(v,-1)for b,v in layers.items()};desired[157][0]=outline(outline(desired[157][0],14),6)
 _,ring,_,ringproof=old_return_targets(original)
 desired[158]={b:shift(v,-10)for b,v in layers.items()}
 body=desired[158][0];v=ring.copy();v[body>0]=body[body>0];desired[158][0]=v
 # Verify the historical aura's body was copied, not a deliberate recolor.
 history=ROOT/'work/ver_buki_riko/shibuki_art/remaining_v1/production06'
 old156=np.zeros((384,384),np.uint8);old157=old156.copy()
 old156[80:240,80:240]=np.array(Image.open(history/'frame_156.png'))
 old157[80:240,80:240]=np.array(Image.open(history/'frame_157.png'))
 need(np.array_equal(old157,outline(outline(shift(old156,-1),14),6)),'Historical aura rule changed')
 need(np.array_equal(old157,original.layer(157)[0]),'Historical157 no longer current')
 proof={'new_art_sha256':ART_HASH,'body_source':'front156_aligned02','old_game_head_body_used':False,'part_ownership':{'5':'new Fourth bow and flower above native y=-4','6':'new Fourth torso/skirt/long side coat panels','7':'new Fourth outer sleeve regions y=-4..7','8':'new Fourth central lower legs y>=13'},'part_pixel_counts':{str(b):int(np.count_nonzero(layers[b]))for b in PARTS},'157':{'body_ref':156,'translation':[0,-1],'inner_aura_index':14,'outer_aura_index':6,'each_outline_4_connected_pixels':1,'historical_source157_matches_current':True,'old156_later_detail_texels_missing_in_old157':int(np.count_nonzero(original.layer(156)[0]!=old156)),'body_recolor_not_intended':True},'158':ringproof,'palette_bytes_unchanged':True,'partial_masks_are_costume_layer_combinations':True,'game_runtime_verified':False}
 return desired,owner,ring,proof

def pack(parent,desired):
 previous_sha=native_packer.ARC_SHA;previous_selected=native_packer.SELECTED
 try:
  native_packer.ARC_SHA=PARENT_SHA;native_packer.SELECTED=SELECTED
  result,proof=native_packer.pack(parent,desired)
 finally:native_packer.ARC_SHA=previous_sha;native_packer.SELECTED=previous_selected
 proof.pop('new_body_and_accepted_idle_head',None)
 proof.update(new_body_and_new_front_head=True,frozen_lowhp120_125_unchanged=True,selected_return_refs=sorted(SELECTED))
 return result,proof

def main():
 need(file_hash(SOURCE)==SOURCE_SHA,'Source BIN changed')
 source=read_disc(SOURCE,('PL00_U.ARC',))[0]['PL00_U.ARC'];original=Archive(source)
 parent=(H/'prepared_lowhp_return01/PL00_U.ARC').read_bytes();need(sha(parent)==PARENT_SHA,'Stable checkpoint changed')
 desired,owner,ring,provenance=targets(original)
 result,proof=pack(parent,desired)
 out=H/'prepared_front_return01';need(not out.exists(),'Output already exists');out.mkdir()
 (out/'PL00_U.ARC').write_bytes(result);write(out/'verification.json',proof);write(out/'provenance.json',provenance)
 write(out/'proposal.json',{'project':'ver_buki_riko','baseline_sha256':SOURCE_SHA,'files':{'PL00_U.ARC':{'path':(out/'PL00_U.ARC').relative_to(ROOT).as_posix(),'before':sha(source),'after':sha(result)}}})
 Image.fromarray(owner).save(out/'part_ownership_indices.png');original.rgba(ring).save(out/'preserved_ring.png')
 actual=Archive(result)
 for mask,label in((0,'base'),(15,'fourth')):
  items=[]
  for n in(156,157,158,159):items.extend([(f'{label} current {n}',original.composite(n,mask)[0]),(f'{label} prepared {n}',actual.composite(n,mask)[0])])
  page(items,actual.composite(0,mask)[0],out/f'{label}_comparison.png',cols=2,scale=4)
 for n in SELECTED:page([(f'{n} mask{m:02X}',actual.composite(n,m)[0])for m in range(16)],actual.composite(0,15)[0],out/f'partial_{n}.png',cols=4,scale=3)
 print(json.dumps({'passed':True,'PL00_sha256':sha(result),'groups':proof['groups'],'parts_slack':proof['parts_slack'],'graphics_slack':proof['graphics']['remaining_slack']}))

if __name__=='__main__':main()
