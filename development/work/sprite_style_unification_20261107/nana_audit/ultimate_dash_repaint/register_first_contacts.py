"""새 원화의 신발/아랫종아리만 소량 강체정합, 기존몸 덮기·채색 없음."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image,ImageDraw
from scipy.ndimage import label
D=Path(__file__).resolve().parent;N=D.parent;ROOT=D.parents[3]
sys.path[:0]=[str(D),str(ROOT),str(N/'native_restore'),str(N/'ultimate_wall_repaint')]
from preview_restore import Archive,sha,digest,write,need,helper
from prepare_inputs import SRC,EXPECTED
from register_contacts import move
POLYGONS={
67:([(-5,14),(1,14),(2,17),(3,23),(-5,23)],1,0),
79:([(2,11),(5,11),(6,13),(5,18),(2,18),(1,14)],1,-2),
93:([(5,11),(8,11),(11,16),(10,19),(6,19),(5,15)],-1,0)}
def main():
 need(digest(SRC)==EXPECTED,'Parent');a=Archive(SRC.read_bytes());out=D/'first_contacts_probe_v1';out.mkdir(exist_ok=False);records=[];rows=[]
 for n in(67,71,79,93):
  src=D/f'before_first_registered_v2/before_{n:03}.png';old=np.array(Image.open(src));new=old.copy();changes=[]
  if n in POLYGONS:
   poly,dx,dy=POLYGONS[n];im=Image.new('L',(384,384));ImageDraw.Draw(im).polygon([(x+160,y+160)for x,y in poly],fill=255);mask=np.array(im)>0
   new,q=move(new,mask,dx,dy);q.update(region='new lower calf/shoe',polygon_world=poly);changes.append(q);im.save(out/f'foot_mask_{n:03}.png')
  need(label(new>0,np.ones((3,3)))[1]==label(old>0,np.ones((3,3)))[1],f'New component {n}')
  need(int(np.nonzero(new)[0].max())==int(np.nonzero(old)[0].max()),'Lowest sole Y')
  Image.fromarray(new).save(out/f'before_{n:03}.png');records.append({'ref':n,'source':str(src.relative_to(ROOT)),'source_sha256':digest(src),'changes':changes,'before_index_sha256':sha(old.tobytes()),'after_index_sha256':sha(new.tobytes()),'old_game_pixels_used':0,'body_color_fill_used':False,'status':'71 local redraw still pending'if n==71 else'local contact candidate'})
  rows.append((f'Ultimate dash {n}',[('idle',a.composite(0,15)[0]),('old contact',a.composite(n,15)[0]),('new source',a.rgba(old,16)),('new local contact candidate',a.rgba(new,16))]))
 helper.grid(rows,out/'comparison.png',6);write(out/'registration.json',{'parent_arc_sha256':EXPECTED,'frames':records,'source_authored_detail_preserved':True,'art_review_pending':True,'native_packed':False,'runtime_verified':False});print(out)
if __name__=='__main__':main()
