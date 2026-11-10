"""새 포스 의상 donor만 의미영역 등록하고 첫 새 머리·손발 외부를 보존한다."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image,ImageDraw
from scipy.ndimage import label
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
from scripts.export_x_consistency import Archive,page,metrics
POLYS={213:[[(-14,8),(-8,7),(-5,8),(-2,7),(3,8),(8,10),(9,16),(8,24),(-3,24),(-9,18),(-14,15)]],215:[[(-19,-21),(-12,-21),(-12,-16),(-10,-10),(-9,-5),(-8,-3),(-12,0),(-16,-8),(-19,-16)],[(-10,-3),(-6,-2),(-2,-3),(5,-1),(8,4),(7,14),(6,25),(0,25),(-5,16),(-10,19),(-13,11),(-12,5),(-8,2)]]}
HANDS={213:[(-15,3,-9,8),(3,10,9,15)],215:[(-20,-28,-10,-21),(-1,6,6,12)]}
def poly(points):
    p=Image.new('1',(384,384));ImageDraw.Draw(p).polygon([(160+x,160+y)for x,y in points],fill=1);return np.array(p,bool)
def main():
    d=H/'nova_fourth_costume_composed01';need(not d.exists(),'새 출력');d.mkdir();a=Archive((H/'prepared_chaser_base01/PL00_U.ARC').read_bytes());rows=[];pics=[]
    for n in (213,215):
        old=np.array(Image.open(H/f'nova_base_native01/fourth_{n:03}_indices.png'));donor=np.array(Image.open(H/f'nova_fourth_costume_native01/fourth_{n:03}_indices.png'));region=np.logical_or.reduce([poly(ps)for ps in POLYS[n]])
        protect=np.zeros(old.shape,bool)
        for x0,y0,x1,y1 in HANDS[n]:protect|=poly([(x0,y0),(x1,y0),(x1,y1),(x0,y1)])&np.isin(old,[9,10,11])
        region&=~protect;out=old.copy();out[region]=donor[region]
        need(np.array_equal(out[~region],old[~region]),'의상밖 보존');need(np.array_equal(out[protect],old[protect]),'피부 손 보존')
        labs,_=label(out>0,np.ones((3,3)));cc=sorted(map(int,np.bincount(labs.flat)[1:]),reverse=True)
        im=a.rgba(out,16);Image.fromarray(out).save(d/f'fourth_{n:03}_indices.png');im.save(d/f'fourth_{n:03}.png');Image.fromarray(region.astype('uint8')*255).save(d/f'{n:03}_costume_mask.png');Image.fromarray(protect.astype('uint8')*255).save(d/f'{n:03}_skin_protected_mask.png')
        changes=[[int(x)-160,int(y)-160,int(old[y,x]),int(out[y,x])]for y,x in zip(*np.nonzero(old!=out))]
        rows.append({'ref':n,'changed':len(changes),'changes':changes,'polygons':POLYS[n],'protected_skin_pixels':int(protect.sum()),'outside_exact':True,'components':cc,'source_metrics':metrics(a.rgba(old,16)),'new_metrics':metrics(im),'rgba_sha256':sha(im.tobytes())});pics.extend([(f'{n} 첫 새몸',a.rgba(old,16)),(f'{n} 의상 국소 등록',im)])
    page(pics,a.composite(0,15)[0],d/'comparison.png',cols=2,scale=5)
    write(d/'report.json',{'rows':rows,'source_directories':['nova_base_native01','nova_fourth_costume_native01'],'body_resized':False,'old_body_copied':False,'arc_written':False,'policy':'두 원화의 고정 동일 원점에서 의상 폴리곤만 donor로 등록. 머리/손/나머지외부는 첫 새원화 exact. 얼굴·손 피부는 별도 보호.'});print(json.dumps([{k:r[k]for k in('ref','changed','components','new_metrics')}for r in rows]))
if __name__=='__main__':main()
