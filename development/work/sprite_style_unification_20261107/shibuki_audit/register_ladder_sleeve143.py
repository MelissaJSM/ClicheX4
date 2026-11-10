"""실제 보완 원화의 두 소매 안쪽 명암만 새 native 사다리에 등록한다."""
from pathlib import Path
import sys,json
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
import numpy as np
from PIL import Image
from scripts.export_x_consistency import Archive,page
from scripts.prepare_shibuki_run_cycle import quantize
from native_pose_pack import need,sha,write

def main():
 source=H/'ladder_detail_inputs01/generated_sleeve143.png';need(sha(source.read_bytes())=='d0d83fd758ab4f1cf51b745ee5483c3dd4e22b732d8d6e63abbd25d52eb3b1db','Source changed');im=Image.open(source).convert('RGBA');a=Archive((H/'prepared_wall_front01/PL00_U.ARC').read_bytes());out=H/'ladder_page01_detail02';need(not out.exists(),'Output exists');out.mkdir();rows=[]
 yy,xx=np.indices((384,384));x=xx-160;y=yy-160
 for row,(name,start,mask)in enumerate((('base',0,0),('fourth',16,15))):
  reviews=[]
  for n in(143,144,146):
   path=H/f'ladder_detail_vote_probe01/{name}_{n:03}_coverage20_indices.png';v=np.array(Image.open(path));target=v.copy();changed=[]
   if n==143:
    rgb=np.array([[(int(w)>>s&31)*255//31 for s in(0,5,10)]for w in a.words[start:start+16]],np.int32);q=quantize(im.crop((0,row*512,512,(row+1)*512)),(64,64),rgb,128);new=np.zeros_like(v);new[128:192,128:192]=q
    region=(x>=-15)&(x<=-1)&(y>=-1)&(y<=9)
    if mask==0:region&=np.isin(v,[3,6,9])&np.isin(new,[3,6,9,8,14])
    else:region&=np.isin(v,[3,4,5])&np.isin(new,[2,3,4,5,6])
    target[region]=new[region];need(np.array_equal(target>0,v>0),'Alpha changed');need(np.array_equal(target[~region],v[~region]),'Outside sleeve changed');changed=[[int(px-160),int(py-160),int(v[py,px]),int(target[py,px])]for py,px in zip(*np.nonzero(v!=target))]
    Image.fromarray(region.astype(np.uint8)*255).save(out/f'{name}_143_sleeve_mask.png')
   Image.fromarray(target).save(out/f'{name}_{n:03}_indices.png');pic=a.rgba(target,start);pic.save(out/f'{name}_{n:03}.png');reviews.extend([(f'{n} first native',Image.open(H/f'ladder_native_page01/{name}_{n:03}.png')),(f'{n} detail candidate',pic)]);rows.append({'form':name,'ref':n,'source_native_sha256':sha(path.read_bytes()),'new_sleeve_pixels':changed,'source_midtones_restored_before_sleeve':True,'alpha_unchanged':True,'head_hand_outline_feet_outside_sleeve_unchanged':True})
  page(reviews,a.composite(0,mask)[0],out/f'{name}_comparison.png',cols=2,scale=4)
 write(out/'registration.json',{'candidate_only_not_packed':True,'sleeve_source_sha256':sha(source.read_bytes()),'hair_source':'ladder_detail_vote_probe01/analysis.json threshold20%','rows':rows,'old_game_head_or_body_used':False,'arm_scale_or_position_changed':False,'new_black_lines_drawn':False,'visually_reviewed':False});print([(r['form'],r['ref'],len(r['new_sleeve_pixels']))for r in rows])

if __name__=='__main__':main()
