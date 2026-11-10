"""새 원화의 종아리만 등록하고 첫 원화의 실제 발바닥과 상체는 보존한다."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image,ImageDraw
from scipy.ndimage import label
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
from scripts.export_x_consistency import Archive,page,metrics
POLYS={213:[[(-6,16),(2,16),(4,17),(7,17),(8,19),(8,20),(1,20),(-6,19)]],215:[[(-11,9),(-7,9),(-5,11),(-5,12),(-10,12)],[(-2,11),(3,11),(3,13),(6,16),(8,18),(8,20),(2,20),(1,17),(-2,14)]]}
def poly(points):
    p=Image.new('1',(384,384));ImageDraw.Draw(p).polygon([(160+x,160+y)for x,y in points],fill=1);return np.array(p,bool)
def main():
    d=H/'nova_ultimate_footwear_composed01';need(not d.exists(),'새 출력만');d.mkdir()
    a=Archive((H/'prepared_chaser_ultimate01/PL02_U.ARC').read_bytes());yy,xx=np.indices((384,384));x=xx-160;y=yy-160;rows=[]
    for form,mask,pal in [('before',15,16),('after',0,0)]:
        pics=[]
        for n in (213,215):
            first=np.array(Image.open(H/f'nova_ultimate_native01/{form}_{n:03}_indices.png'));donor=np.array(Image.open(H/f'nova_ultimate_footwear_native01/{form}_{n:03}_indices.png'))
            region=np.logical_or.reduce([poly(ps)for ps in POLYS[n]])
            # 첫 원화의 작은 샌들·발바닥은 올바른 원좌표에 있으므로 그대로 유지한다.
            feet=((y>=20)&(x>=3)) if n==213 else (((y>=12)&(x<=-5))|((y>=20)&(x>=3)))
            region&=~feet;out=first.copy();out[region]=donor[region]
            need(np.array_equal(out[~region],first[~region]),'국소영역 밖 보존');need(np.array_equal(out[feet],first[feet]),'기존 새발 보존')
            labs,_=label(out>0,np.ones((3,3)));cc=sorted(map(int,np.bincount(labs.flat)[1:]),reverse=True);need(len(cc)==1,'관절 연결')
            im=a.rgba(out,pal);need(metrics(im)['bbox']==metrics(a.rgba(first,pal))['bbox'],'전체 외곽 높이/폭 보존')
            Image.fromarray(out).save(d/f'{form}_{n:03}_indices.png');im.save(d/f'{form}_{n:03}.png');Image.fromarray(region.astype('uint8')*255).save(d/f'{form}_{n:03}_donor_mask.png');Image.fromarray(feet.astype('uint8')*255).save(d/f'{form}_{n:03}_feet_protected.png')
            changes=[[int(px)-160,int(py)-160,int(first[py,px]),int(out[py,px])]for py,px in zip(*np.nonzero(first!=out))]
            rows.append({'ref':n,'form':form,'polygons':POLYS[n],'changed':len(changes),'changes':changes,'outside_exact':True,'first_new_feet_exact':True,'body_resize':False,'body_translation':[0,0],'components':cc,'metrics':metrics(im),'rgba_sha256':sha(im.tobytes())})
            pics.extend([(f'{n} 첫 새 원화',a.rgba(first,pal)),(f'{n} 종아리 국소 등록',im)])
        page(pics,a.composite(0,mask)[0],d/f'{form}_comparison.png',cols=2,scale=5)
    write(d/'report.json',{'sources':['nova_ultimate_native01','nova_ultimate_footwear_native01'],'rows':rows,'policy':'첫 새 원화의 작은 샌들·발바닥은 유지하고 새 donor의 종아리 피부/그늘만 의미영역 등록. 높은 donor 발바닥을 채택하거나 늘리지 않음.','arc_written':False,'accepted':False});print(json.dumps([{k:r[k]for k in('ref','form','changed','components','metrics')}for r in rows]))
if __name__=='__main__':main()
