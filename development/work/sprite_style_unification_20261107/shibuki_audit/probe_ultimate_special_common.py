"""새95/97에서 머리·맨다리·손을 두 의상에 공유하는 읽기 가능한 후보."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image,ImageDraw
from scipy.ndimage import label
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
from scripts.export_x_consistency import Archive,page,metrics

HEAD={95:[(-18,-27),(14,-27),(14,4),(9,4),(8,2),(5,1),(4,-2),(-7,-2),(-8,1),(-12,1),(-13,-3),(-18,-3)],
      97:[(-18,-27),(14,-27),(14,5),(9,5),(7,3),(6,-1),(3,-3),(-2,-3),(-3,-2),(-8,-2),(-9,-4),(-14,-4),(-18,-7)]}
HANDS={95:[[(-18,5),(-12,5),(-11,7),(-12,8),(-18,8)],[(7,5),(12,5),(12,8),(7,8)]],
       97:[[(-15,-4),(-12,-5),(-10,-4),(-10,0),(-12,2),(-15,1)],[(-3,-3),(1,-3),(2,-2),(2,1),(-1,2),(-3,0)]]}

def poly(points):
    im=Image.new('1',(384,384));ImageDraw.Draw(im).polygon([(x+160,y+160) for x,y in points],fill=1);return np.array(im,bool)

def main():
    out=H/'ultimate_special_common_probe01';need(not out.exists(),'Fresh common probe');out.mkdir()
    a=Archive((H/'prepared_ultimate_return01/PL02_U.ARC').read_bytes())
    rgb=np.array([[(int(w)>>k&31)*255//31 for k in (0,5,10)] for w in a.words],np.int32)
    lut=np.r_[0,1+((rgb[17:32,None]-rgb[None,1:16])**2).sum(2).argmin(1)].astype(np.uint8)
    yy,xx=np.indices((384,384));x=xx-160;y=yy-160;rows=[];pics={'before':[],'after':[]}
    for ref in (95,97):
        source=H/'ultimate_special_native01'
        before=np.array(Image.open(source/f'before_{ref:03}_indices.png'))
        fresh=np.array(Image.open(source/f'after_{ref:03}_indices.png'));after=fresh.copy()
        head=poly(HEAD[ref]);legs=(y>=12)&(y<25);hands=np.zeros_like(head)
        for points in HANDS[ref]:hands|=poly(points)
        if ref==97:hands&=np.isin(before,[10,11,12,13])
        common=head|legs|hands;after[common]=lut[before][common]
        outside=(after>0)&(before==0)
        for form,value,pal,mask in (('before',before,16,15),('after',after,0,0)):
            Image.fromarray(value).save(out/f'{form}_{ref:03}_indices.png');im=a.rgba(value,pal);im.save(out/f'{form}_{ref:03}.png')
            pics[form].extend([(f'{ref} old',a.composite(ref,mask)[0]),(f'{ref} new common',im)])
        for name,m in (('head',head),('legs',legs),('hands',hands),('common',common),('outside',outside)):
            Image.fromarray(m.astype(np.uint8)*255).save(out/f'{ref:03}_{name}_mask.png')
        labels,count=label(after>0,np.ones((3,3)))
        rows.append({'ref':ref,'head_polygon':HEAD[ref],'legs_y':[12,25],'hands_polygons':HANDS[ref],
            'hands_only_source_skin':ref==97,'before_source_exact':True,'after_outside_common_exact':bool(np.array_equal(after[~common],fresh[~common])),
            'common_opaque_cells':int((before[common]>0).sum()),'after_common_changes':int((after!=fresh).sum()),
            'outside_before':[[int(px)-160,int(py)-160,int(after[py,px])] for py,px in zip(*np.nonzero(outside))],
            'after_components':sorted(map(int,np.bincount(labels.flat)[1:]),reverse=True),
            'before_metrics':metrics(a.rgba(before,16)),'after_metrics':metrics(a.rgba(after)),
            'whole_body_resize':False,'old_art_copied':0})
    for form,mask in (('before',15),('after',0)):page(pics[form],a.composite(0,mask)[0],out/f'{form}_comparison.png',cols=2,scale=5)
    write(out/'report.json',{'parent_sha256':sha(a.data),'native_report_sha256':sha((H/'ultimate_special_native01/report.json').read_bytes()),
        'palette_before_to_after':lut.tolist(),'rows':rows,'arc_written':False,'visual_review_pending':True,
        'costume_reference_note':'원설정화 후폼에 퍼지는 짧은 옷단이 실제 있어 그것만으로 원화오류로 판정하지 않는다. 새 머리/손발 공통과 새 의상 경계를 별도로 검사한다.'})
    print(json.dumps(rows))

if __name__=='__main__':main()
