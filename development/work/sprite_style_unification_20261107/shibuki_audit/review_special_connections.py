"""미패킹95/97 후보와 이미 동결된 앞뒤 자세를 같은 원점에 비교한다."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
from scripts.export_x_consistency import Archive,page,metrics
def main():
 d=H/'standing_special_connections01';need(not d.exists(),'Fresh connections');d.mkdir();a=Archive((H/'prepared_hurt_base01/PL00_U.ARC').read_bytes());s=H/'standing_special_layers01';rows=[];images=[]
 for form,mask in(('base',0),('fourth',15)):
  new={n:Image.open(s/f'{form}_{n:03}.png').convert('RGBA')for n in(95,97)};array=np.array(new[95]);new[96]=Image.fromarray(np.roll(array,1,axis=1))
  for group,seq in(('frost_soul',(138,139,96,95,96)),('cyclone',(97,81,99,98,99))):
   pics=[(f'{n} '+('new pending'if n in new else'frozen'),new[n]if n in new else a.composite(n,mask)[0])for n in seq];p=d/f'{form}_{group}.png';page(pics,a.composite(0,mask)[0],p,cols=3,scale=5);images.append({'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p.read_bytes())});rows.append({'form':form,'group':group,'refs':list(seq),'metrics':[{'ref':n,**metrics(im)}for(n,(_,im))in zip(seq,pics)]})
 write(d/'report.json',{'parent_sha256':sha(a.data),'source_layers_sha256':sha((s/'report.json').read_bytes()),'frames':rows,'images':images,'scope':'후보95/96/97과 동결된 주변 자세의 원점/체격 연결 비교이다. 원표 호출시간을 실행한 재생이나 ARC 재추출/실기 검사는 아니다.','native_order_evidence':{'path':'work/sprite_style_unification_20261107/zero_audit/shibuki_standing_special_relations01/report.json','sha256':sha((H.parent/'zero_audit/shibuki_standing_special_relations01/report.json').read_bytes())},'arc_written':False,'visual_review_pending':True});print(d)
if __name__=='__main__':main()
