"""98의 머리/발을 고정하고 내려온 허리와 권총손만 원포즈에 정합할 입력."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image,ImageDraw
D=Path(__file__).resolve().parent;N=D.parent;ROOT=N.parents[2];sys.path[:0]=[str(ROOT),str(N/'native_restore')]
from preview_restore import Archive,digest,write
def main():
 m=json.loads((D/'a_inputs_v1/manifest.json').read_text('utf8'));a=Archive((ROOT/m['parent_arc']).read_bytes());out=D/'torso98_inputs_v1';assert not (out/'manifest.json').exists();out.mkdir(exist_ok=True);target=Image.new('RGBA',(1536,1024));guide=target.copy();style=target.copy();records=[]
 for i,(form,start,mask)in enumerate((('before',16,15),('after',0,0))):
  p=D/f'geometry_position_probe_v1/{form}_098_indices.png';z=np.array(Image.open(p));im=a.rgba(z,start);target.alpha_composite(im.crop((112,96,208,224)).resize((768,1024),Image.Resampling.NEAREST),(i*768,0));guide.alpha_composite(a.composite(98,mask)[0].crop((112,96,208,224)).resize((768,1024),Image.Resampling.NEAREST),(i*768,0));style.alpha_composite(a.composite(89,mask)[0].crop((112,96,208,224)).resize((768,1024),Image.Resampling.NEAREST),(i*768,0));dr=ImageDraw.Draw(guide)
  for x,y,text in((-25,-9,'muzzle'),(-19,-6,'grip'),(0,5,'waist'),(20,-5,'free hand')):
   xx=i*768+(x+48)*8;yy=(y+64)*8;dr.ellipse((xx-4,yy-4,xx+4,yy+4),outline=(0,220,255,255),width=2);dr.text((xx+9,yy-12),text,fill=(0,220,255,255))
  dr.text((i*768+30,30),f'{form}98 desired pose / native96x128 / no body scaling',fill=(0,220,255,255));records.append({'form':form,'native_source':p.relative_to(ROOT).as_posix(),'native_sha256':digest(p),'world_crop':[-48,-64,48,64]})
 target.save(out/'edit_target.png');guide.save(out/'desired_pose.png');style.save(out/'accepted_detail.png');write(out/'manifest.json',{'ref':98,'records':records,'parent_arc_sha256':m['parent_arc_sha256'],'scope':'95와분리한98 관절 국소 편집. 새머리/발보호,의상/실루엣다른거부작업과무관.','files':[{'path':p.relative_to(ROOT).as_posix(),'sha256':digest(p)}for p in sorted(out.iterdir())if p.is_file()]});print(out)
if __name__=='__main__':main()
