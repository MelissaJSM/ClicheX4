"""별개154/183의 새 두 의상에 공통머리/사지와 손을 등록한다."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image,ImageDraw
from scipy.ndimage import label
D=Path(__file__).resolve().parent;N=D.parent;ROOT=N.parents[2];sys.path[:0]=[str(ROOT),str(N/'native_restore')]
from preview_restore import Archive,digest,sha,write,need,helper
POLYS={
154:[[(-8,-1),(-2,-1),(3,1),(6,7),(10,10),(10,15),(-1,15),(-3,11),(-3,9),(-7,8)],[(-15,4),(-10,3),(-8,3),(-6,1),(-3,2),(-2,6),(-5,9),(-14,9)]],
183:[[(-8,9),(-5,8),(5,9),(9,14),(8,21),(-7,21),(-9,17)],[(-13,1),(-7,1),(-6,7),(-2,8),(-3,12),(-9,12),(-12,8)],[(8,1),(15,1),(15,7),(12,11),(9,12),(7,9),(10,6)]]}
ACCENTS={154:[(-6,-10),(-6,-9)],183:[(-3,-1),(-2,-1)]}
def mask_for(n):
 im=Image.new('L',(384,384));dr=ImageDraw.Draw(im)
 for points in POLYS[n]:dr.polygon([(x+160,y+160)for x,y in points],fill=1)
 for x,y in ACCENTS[n]:dr.point((x+160,y+160),fill=1)
 return np.array(im)>0
def main():
 parent=N/'ultimate_return_repaint/packed_return_candidate_v1/PL02_U.ARC';a=Archive(parent.read_bytes());src=D/'c_registered_v1';out=D/'c_common_probe_v2';out.mkdir(exist_ok=False);rows=[];records=[]
 for n in (154,183):
  b=np.array(Image.open(src/f'before_{n:03}_indices.png'));donor=np.array(Image.open(src/f'after_{n:03}_indices.png'));m=mask_for(n);v=np.where(m,donor,b).astype(np.uint8);fringe=(v>0)&(b==0);before=b.copy();before[fringe]=v[fringe]
  for x,y in ACCENTS[n]:need(donor[y+160,x+160]==15,'원화후폼의 실제 귀장식 색15')
  need(np.all((v==0)|(before>0)),'새후폼알파포함');layer5=np.where((before!=v)|(before==15),before,0).astype(np.uint8);im=a.rgba(v);im.alpha_composite(a.rgba(layer5,16));need(im.tobytes()==a.rgba(before,16).tobytes(),'의상RGBA합성')
  for tag,z in(('before',before),('after',v),('costume_mask',m.astype(np.uint8)),('boundary_mask',fringe.astype(np.uint8)),('layer0',v),('layer5',layer5)):Image.fromarray(z).save(out/f'{tag}_{n:03}_indices.png')
  rows.append((str(n),[('new jacket source',a.rgba(b,16)),('new bare source',a.rgba(donor)),('common jacket',a.rgba(before,16)),('common bare',a.rgba(v))]))
  records.append({'ref':n,'before_source_sha256':digest(src/f'before_{n:03}_indices.png'),'after_source_sha256':digest(src/f'after_{n:03}_indices.png'),'costume_polygons':POLYS[n],'after_ear_accents_source15':ACCENTS[n],'new_before_boundary_source_links':[{'world':[int(x-160),int(y-160)],'source_index':int(v[y,x])}for y,x in np.argwhere(fringe)],'after_changed_from_donor':int((v!=donor).sum()),'components8':{k:int(label(z>0,np.ones((3,3)))[1])for k,z in(('before',before),('after',v))},'whole_body_scaled_or_shifted':False,'outside_costume_new_before_exact':True})
 helper.grid(rows,out/'comparison.png',7);write(out/'manifest.json',{'parent_sha256':digest(parent),'source_registration_sha256':digest(src/'registration.json'),'frames':records,'scope':'별개154/183 새원화의 공통부 검토. 손/손목최종접점 및 머리/의상경계는 정적 검토 중.149/151/153 보류원화는 읽거나 쓰지 않음.','native_packed':False,'runtime_verified':False});print(json.dumps([{'ref':q['ref'],'boundary':len(q['new_before_boundary_source_links']),'changed':q['after_changed_from_donor'],'components':q['components8']}for q in records]))
if __name__=='__main__':main()
