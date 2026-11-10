"""새 벽 몸/원래 배럴을 지키는 발사팔 편집 입력을 준비한다."""
from pathlib import Path
import sys,argparse,json
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
import numpy as np
from PIL import Image,ImageDraw
from scripts.c01_audio_build import read_disc
from scripts.export_x_consistency import Archive,page
from native_pose_pack import SOURCE,SOURCE_SHA,need,write,sha
from src.psx_disc import file_hash

def main():
 p=argparse.ArgumentParser();p.add_argument('--body',type=Path,required=True);p.add_argument('--output',type=Path,required=True);args=p.parse_args();body=args.body.resolve();out=args.output.resolve()
 need(body.is_relative_to(H)and out.is_relative_to(H)and not out.exists(),'Isolated new folder required');need(file_hash(SOURCE)==SOURCE_SHA,'Source changed');a=Archive(read_disc(SOURCE,('PL00_U.ARC',))[0]['PL00_U.ARC']);guards=json.loads((H/'wall_barrel_guard01/guard.json').read_text('utf8'))['rows'];out.mkdir();rows=[]
 for page_number,refs in enumerate(((55,57,59),(61,63,65)),1):
  board=Image.new('RGBA',(1536,1024));guide=Image.new('RGBA',(1536,1024));d=ImageDraw.Draw(guide)
  for r,(name,mask)in enumerate((('base',0),('fourth',15))):
   for c,n in enumerate(refs):
    layers={b:np.array(Image.open(body/f'{n:03}_bank{b}_indices.png'))for b in(0,5,6,7,8)};im=a.rgba(layers[0])
    if mask:
     for b in(8,5,7,6):im.alpha_composite(a.rgba(layers[b],16))
    guard=next(q for q in guards if q['body_ref']==n);barrel=np.array(Image.open(H/'wall_barrel_guard01'/f'{n+1:03}_indices.png'));need(sha(barrel.tobytes())==guard['raw_index_sha256'],'Gun guard changed');im.alpha_composite(a.rgba(barrel))
    im.save(out/f'{name}_{n+1:03}_edit_target.png');cell=im.crop((128,120,192,184)).resize((512,512),Image.Resampling.NEAREST);board.alpha_composite(cell,(c*512,r*512));guide.alpha_composite(cell,(c*512,r*512))
    mx,my=guard['muzzle_world'];shoulder={55:(-6,-2),57:(-6,-1),59:(-6,-2),61:(-2,-2),63:(0,-1),65:(-2,-1)}[n]
    # Guide is not final art. Barrel remains outside the editable arm extent.
    points=[(mx+9,my-5),(shoulder[0]+3,shoulder[1]-4),(shoulder[0]+4,shoulder[1]+8),(mx+7,my+8)]
    d.line([(c*512+(x+32)*8,r*512+(y+40)*8)for x,y in points+[points[0]]],fill=(0,255,128,230),width=3)
    rows.append({'body_ref':n,'shot_ref':n+1,'form':name,'body_source':body.relative_to(ROOT).as_posix(),'body_layer_hashes':{str(b):sha(v.tobytes())for b,v in layers.items()},'muzzle_world':[mx,my],'barrel_exact':guard,'shoulder_anchor_world':list(shoulder),'new_body_only':True,'left_bent_fist_to_replace':True,'new_firing_arm_still_required':True})
  board.save(out/f'page{page_number:02}.png');guide.save(out/f'guide{page_number:02}.png')
 write(out/'inputs.json',{'source_bin_sha256':SOURCE_SHA,'canvas':[1536,1024],'native_cell':[64,64],'native_world_crop':[-32,-40,32,24],'scale':.125,'top_row':'base','bottom_row':'fourth','records':rows,'existing_gun_only_reused':True,'not_ready_to_pack':True})
 print(out)

if __name__=='__main__':main()
