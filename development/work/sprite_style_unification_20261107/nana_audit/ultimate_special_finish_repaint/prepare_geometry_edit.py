"""늘어진 새95/98을 몸 전체 축소 없이 원 관절·접지로 재작화하는 입력."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image,ImageDraw
D=Path(__file__).resolve().parent;N=D.parent;ROOT=N.parents[2];sys.path[:0]=[str(ROOT),str(N/'native_restore')]
from preview_restore import Archive,digest,write
def main():
 meta=json.loads((D/'a_inputs_v1/manifest.json').read_text('utf8'));a=Archive((ROOT/meta['parent_arc']).read_bytes());out=D/'geometry_inputs_v1';assert not (out/'manifest.json').exists();out.mkdir(exist_ok=True)
 target=Image.open(D/'a_v1/generated.png').convert('RGBA');target.save(out/'edit_target.png');guide=Image.open(D/'a_inputs_v1/targets.png').convert('RGBA');dr=ImageDraw.Draw(guide)
 for row in range(2):
  for col,(n,floor)in enumerate(((95,20),(98,23))):
   x=col*768;y=row*768;dr.line((x+128,y+(floor+48)*8,x+640,y+(floor+48)*8),fill=(0,220,255,255),width=3)
   dr.text((x+40,y+45),f'DESIRED POSE {n} / fixed96 cell / feet on cyan baseline',fill=(0,220,255,255));dr.text((x+40,y+67),'Use limb lengths/angles/hand positions, NOT old flat detail.',fill=(0,220,255,255))
 guide.save(out/'desired_pose_guide.png')
 write(out/'manifest.json',{'source_art_sha256':digest(D/'a_v1/generated.png'),'parent_arc_sha256':meta['parent_arc_sha256'],'edit_refs':[95,98],'edit_scope':'새 원화의 얼굴/머리 크기·세부를 보존하고 몸통/관절/손발을 원포즈로 재작화. 전체스케일·기존몸도트복사 없음.','rejected_geometry':{'95_floor_delta':8,'98_floor_delta':5,'95_old_bbox':[-18,-32,17,20],'95_new_bbox':[-21,-32,19,28],'98_old_bbox':[-25,-21,21,23],'98_new_bbox':[-29,-22,24,28]},'files':[{'path':p.relative_to(ROOT).as_posix(),'sha256':digest(p)}for p in sorted(out.iterdir())if p.is_file()]});print(out)
if __name__=='__main__':main()
