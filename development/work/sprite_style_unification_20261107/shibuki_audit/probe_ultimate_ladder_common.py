"""새 사다리8몸체의 머리/사지 공통 후보. 구형 그림은 복사하지 않는다."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image,ImageDraw
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
from scripts.export_x_consistency import Archive,page,metrics
from audit_ultimate_ladder_contacts import SOURCES
SOURCES={**SOURCES,151:'ultimate_ladder151_arm_composed01'}
HEAD={
143:[[(-15,-23),(8,-23),(11,-11),(9,-8),(16,-5),(17,5),(12,8),(14,17),(7,18),(4,12),(4,7),(3,3),(-2,-1),(-9,-1),(-15,-8)]],
144:[[(-9,-26),(10,-26),(13,-15),(11,-7),(8,-4),(3,-2),(-6,-3),(-10,-10)],[(-9,-1),(-6,0),(-6,5),(-9,13),(-12,10),(-12,3)],[(7,5),(12,5),(13,12),(8,12)]],
146:[[(-8,-24),(10,-24),(13,-14),(12,-7),(8,-3),(2,-2),(-6,-3),(-9,-10)],[(-8,-1),(-6,0),(-7,5),(-8,11),(-11,11),(-11,4)],[(7,5),(13,5),(14,11),(8,12)]],
149:[[(-15,-23),(2,-23),(3,-18),(8,-16),(8,-8),(7,-6),(13,-3),(15,6),(11,9),(12,16),(5,17),(3,12),(4,7),(3,3),(-2,-2),(-8,-4),(-14,-10)]],
151:[[(-8,-24),(9,-24),(12,-15),(10,-9),(8,-5),(2,-2),(-5,-3),(-9,-10)],[(-9,-1),(-6,0),(-6,5),(-9,10),(-13,9),(-13,3)],[(7,3),(12,3),(14,9),(10,12),(6,8)]],
153:[[(-11,-28),(11,-28),(14,-17),(10,-10),(7,-7),(-7,-7),(-12,-12)],[(-11,-5),(-7,-4),(-7,0),(-10,4),(-14,3),(-14,-1)],[(7,-5),(12,-5),(15,3),(10,8),(6,4)]],
154:[[(-18,-18),(4,-18),(10,-9),(10,-6),(15,-3),(17,6),(12,10),(13,17),(7,17),(3,11),(3,7),(-4,3),(-12,2),(-18,-4)]],
183:[[(-11,-9),(10,-9),(13,1),(12,9),(9,14),(4,14),(-5,13),(-9,10),(-13,3)]]}
LEG_Y={143:10,144:9,146:9,149:10,151:8,153:1,154:14,183:21}
HANDS={143:[(-16,-7,-11,-1)],144:[(-15,-19,-10,-13),(10,-11,15,-5)],146:[(-12,-29,-6,-23),(11,-10,16,-4)],149:[(-3,-29,3,-23),(-13,-6,-8,0)],151:[(-10,-29,-5,-23),(8,-14,14,-8)],153:[(-16,-11,-10,-6),(12,-12,18,-6)],154:[],183:[]}
def poly(points):
    im=Image.new('1',(384,384));ImageDraw.Draw(im).polygon([(x+160,y+160)for x,y in points],fill=1);return np.array(im,bool)
def main(output_name='ultimate_ladder_common_probe01'):
    o=H/output_name;need(not o.exists(),'Fresh output');o.mkdir();p=H/'prepared_ultimate_dash01/PL02_U.ARC';a=Archive(p.read_bytes());rgb=np.array([[(int(w)>>s&31)*255//31 for s in(0,5,10)]for w in a.words],np.int32);lut=np.r_[0,1+((rgb[17:32,None]-rgb[None,1:16])**2).sum(2).argmin(1)].astype(np.uint8);yy,xx=np.indices((384,384));rows=[];pics={'before':[],'after':[]}
    for n,folder in SOURCES.items():
        before=np.array(Image.open(H/folder/f'before_{n:03}_indices.png'));fresh=np.array(Image.open(H/folder/f'after_{n:03}_indices.png'));head=np.zeros_like(before,bool)
        for points in HEAD[n]:head|=poly(points)
        legs=yy>=160+LEG_Y[n];hands=np.zeros_like(before,bool)
        for x0,y0,x1,y1 in HANDS[n]:hands[y0+160:y1+160,x0+160:x1+160]=True
        common=head|legs|hands;after=fresh.copy();after[common]=lut[before][common];outside=(after>0)&(before==0)
        for form,v,pal,mask in(('before',before,16,15),('after',after,0,0)):
            Image.fromarray(v).save(o/f'{form}_{n:03}_indices.png');im=a.rgba(v,pal);im.save(o/f'{form}_{n:03}.png');pics[form].extend([(f'{n} parent {form}',a.composite(n,mask)[0]),(f'{n} new common {form}',im)])
        for name,v in [('head',head),('legs',legs),('hands',hands),('common',common),('outside',outside)]:Image.fromarray(v.astype('uint8')*255).save(o/f'{n:03}_{name}_mask.png')
        need(np.array_equal(after[~common],fresh[~common]),'Costume changed outside mask');points=[[int(x-160),int(y-160),int(after[y,x])]for y,x in zip(*np.nonzero(outside))]
        rows.append({'ref':n,'source':folder,'source_files':{f'{form}_{n:03}_indices.png':sha((H/folder/f'{form}_{n:03}_indices.png').read_bytes())for form in('before','after')},'head_polygons':HEAD[n],'legs_from_y':LEG_Y[n],'hand_rectangles':HANDS[n],'changed_after_common':int(np.count_nonzero(after!=fresh)),'outside_jacket_pixels':points,'old_art_copied':0,'after_noncommon_exact':True,'same_new_common_pixels':True,'new_lowest_y':metrics(a.rgba(before,16))['bbox'][3]-1,'old_lowest_y':metrics(a.composite(n,15)[0])['bbox'][3]-1})
    for form,mask in [('before',15),('after',0)]:
        for start in range(0,len(pics[form]),6):page(pics[form][start:start+6],a.composite(0,mask)[0],o/f'{form}_comparison_{start//6:02}.png',cols=2,scale=5)
    write(o/'report.json',{'scope':'새 원화 공통 머리/다리/손 후보. 가림·옷 경계 직접 열람 전이며 바깥점 삭제·채움 없음.','parent_sha256':sha(a.data),'palette_mapping':lut.tolist(),'rows':rows,'arc_written':False,'visual_review_pending':True,'shooting150_155_pending':True,'sole_and_common_seams_pending':True});print(json.dumps([{'ref':r['ref'],'outside':len(r['outside_jacket_pixels']),'lowest':[r['old_lowest_y'],r['new_lowest_y']]}for r in rows]))
if __name__=='__main__':main()
