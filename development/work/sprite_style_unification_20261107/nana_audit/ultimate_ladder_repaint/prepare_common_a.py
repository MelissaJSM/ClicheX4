"""허용된 첫 사다리3 원화의 공통 머리/사지와 의상 의미영역을 비교한다."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image,ImageDraw
from scipy.ndimage import label
D=Path(__file__).resolve().parent;N=D.parent;ROOT=N.parents[2];sys.path[:0]=[str(ROOT),str(N/'native_restore')]
from preview_restore import Archive,digest,sha,write,need,helper
POLYS={
143:[ [(-10,-13),(-4,-16),(4,-13),(8,-8),(9,-1),(7,7),(-7,7),(-10,1)], [(-16,-28),(-8,-27),(-7,-23),(-3,-20),(1,-16),(0,-10),(-5,-10),(-10,-16),(-15,-22)] ],
144:[ [(-7,-16),(-3,-17),(4,-13),(6,-3),(7,8),(-7,8),(-8,-3)], [(-12,-31),(-5,-31),(-4,-25),(-1,-22),(2,-15),(0,-9),(-5,-9),(-8,-17),(-11,-24)] ],
146:[ [(-8,-13),(-2,-14),(4,-11),(7,-3),(7,8),(-8,8),(-8,-1)], [(-11,-33),(-3,-33),(-3,-26),(-1,-21),(2,-14),(1,-8),(-5,-8),(-8,-16),(-10,-25)] ]
}
def mask_for(n):
 im=Image.new('L',(384,384));dr=ImageDraw.Draw(im)
 for points in POLYS[n]:dr.polygon([(x+160,y+160)for x,y in points],fill=1)
 return np.array(im)>0
def main():
 a=Archive((N/'ultimate_return_repaint/packed_return_candidate_v1/PL02_U.ARC').read_bytes());src=D/'a_arm_registered_v1';out=D/'a_common_probe_v1';out.mkdir(exist_ok=False);records=[];rows=[]
 for n in(143,144,146):
  b=np.array(Image.open(src/f'before_{n}_indices.png'));donor=np.array(Image.open(src/f'after_{n}_indices.png'));m=mask_for(n);after=np.where(m,donor,b).astype(np.uint8);before=b.copy();fringe=(after>0)&(before==0);before[fringe]=after[fringe];need(np.array_equal(after[~m],b[~m]),'공통머리사지');need(np.all((after==0)|(before>0)),'재킷 덮개알파')
  layers={0:after,5:np.where(before!=after,before,0).astype(np.uint8)}
  c=a.rgba(after);c.alpha_composite(a.rgba(layers[5],16));need(c.tobytes()==a.rgba(before,16).tobytes(),'최종팔레트 포함전폼합성')
  for tag,z in(('before',before),('after',after),('costume_mask',m.astype(np.uint8)),('boundary_mask',fringe.astype(np.uint8))):Image.fromarray(z).save(out/f'{tag}_{n:03}_indices.png')
  for pb,z in layers.items():Image.fromarray(z).save(out/f'layer{pb}_{n:03}.png')
  rows.append((str(n),[('new jacket source',a.rgba(b,16)),('new bare source',a.rgba(donor)),('shared jacket candidate',a.rgba(before,16)),('shared bare candidate',a.rgba(after))]))
  records.append({'ref':n,'polygons':POLYS[n],'before_source':(src/f'before_{n}_indices.png').relative_to(ROOT).as_posix(),'after_source':(src/f'after_{n}_indices.png').relative_to(ROOT).as_posix(),'before_source_sha256':digest(src/f'before_{n}_indices.png'),'after_source_sha256':digest(src/f'after_{n}_indices.png'),'shared_source':'new before head and limbs outside costume polygons','after_changed_from_donor':int((after!=donor).sum()),'new_before_boundary_links':[{'world':[int(x-160),int(y-160)],'index':int(after[y,x]),'source':'new bare donor same coordinate'}for y,x in np.argwhere(fringe)],'before_components8':int(label(before>0,np.ones((3,3)))[1]),'after_components8':int(label(after>0,np.ones((3,3)))[1]),'outside_costume_exact':True,'native_packed':False})
 helper.grid(rows,out/'comparison.png',6);write(out/'manifest.json',{'parent_sha256':sha(a.data),'frames':records,'scope':'첫3 허용원화의 공통부 진단후보. 후속149151153 하의 교정거부와 별개이며 해당그림/의상은 변경하지 않음. 현단계는 미술·원손발 정합 미완료로 패킹/동결하지 않는다.','runtime_verified':False});print(json.dumps([{'ref':q['ref'],'common_changes':q['after_changed_from_donor'],'boundary':len(q['new_before_boundary_links']),'components':[q['before_components8'],q['after_components8']]}for q in records]))
if __name__=='__main__':main()
