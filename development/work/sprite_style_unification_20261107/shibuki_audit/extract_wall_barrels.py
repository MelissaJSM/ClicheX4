"""현재 수용 벽 사격 배럴만 실제 팔레트/원점 그대로 추출한다."""
from pathlib import Path
import sys,json
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
import numpy as np
from PIL import Image
from scripts.c01_audio_build import read_disc
from scripts.export_x_consistency import Archive,page
from native_pose_pack import SOURCE,SOURCE_SHA,need,sha,write
from src.psx_disc import file_hash

def main():
 need(file_hash(SOURCE)==SOURCE_SHA,'Source changed');a=Archive(read_disc(SOURCE,('PL00_U.ARC',))[0]['PL00_U.ARC'])
 source=ROOT/'work/ver_buki_riko/shibuki_art/wall_v1/production19/pairs.json';need(sha(source.read_bytes())=='107ddf7a7506377d199a7c7f555fcfc95ca1b0ec23e9cfb21f48a90f587a46da','Historical anchors changed')
 out=H/'wall_barrel_guard01';need(not out.exists(),'Output exists');out.mkdir();rows=[];items=[]
 for r in json.loads(source.read_text('utf8'))['frames']:
  n=r['run'];mx,my=map(int,r['original_muzzle_world']);ix=a.layer(n+1)[0]
  # The barrel is the actual ten-pixel horizontal gun block. The wrist/white
  # sleeve to its right and below are explicitly excluded from this reuse.
  bounds=[mx-1,my-3,mx+9,my+5];mask=np.zeros_like(ix,bool);mask[bounds[1]+160:bounds[3]+160,bounds[0]+160:bounds[2]+160]=True
  mask&=ix>0;barrel=np.where(mask,ix,0).astype(np.uint8);need(barrel.any(),'Missing original gun');Image.fromarray(barrel).save(out/f'{n+1:03}_indices.png');a.rgba(barrel).save(out/f'{n+1:03}.png')
  rgba=np.array(a.rgba(barrel));old0=np.array(a.composite(n+1,0)[0]);old15=np.array(a.composite(n+1,15)[0]);need(np.array_equal(rgba[mask],old0[mask]),'Base source gun mismatch');need(np.array_equal(rgba[mask],old15[mask]),'Fourth source gun differs; explicit redesign needed')
  rows.append({'body_ref':n,'shot_ref':n+1,'muzzle_world':[mx,my],'barrel_rectangle_world_exclusive':bounds,'nontransparent_pixels':int(mask.sum()),'raw_index_sha256':sha(barrel.tobytes()),'base_and_fourth_rgba_identical':True,'head_body_and_old_sleeve_not_copied':True})
  items.extend([(f'{n+1} existing gun only',a.rgba(barrel)),(f'{n+1} current full sprite',a.composite(n+1,0)[0])])
 page(items,a.composite(0,0)[0],out/'comparison.png',cols=2,scale=4);write(out/'guard.json',{'source_bin_sha256':SOURCE_SHA,'source_arc_sha256':sha(a.data)if hasattr(a,'data')else None,'source_anchor_sha256':sha(source.read_bytes()),'rows':rows,'input_only_not_new_firing_art':True})
 print(rows)

if __name__=='__main__':main()
