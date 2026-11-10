"""새등장5자세 공통머리/사지 후보.135보류는 제외,옛master/전신리사이즈 없음."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image,ImageDraw
from scipy.ndimage import label
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
from scripts.export_x_consistency import Archive,page,metrics

HEAD={
133:[[(-17,-15),(5,-15),(7,-11),(8,-5),(9,-4),(8,0),(6,2),(4,4),(-3,5),(-8,3),(-13,3),(-16,-1)],[(5,-6),(9,-5),(9,-1),(12,1),(13,4),(15,5),(17,9),(17,15),(13,15),(12,10),(9,9),(8,5),(5,4),(3,0)]],
136:[[(-17,-25),(10,-25),(11,-16),(9,-10),(6,-7),(1,-5),(-4,-5),(-9,-7),(-13,-10),(-17,-15)],[(5,-14),(10,-13),(14,-8),(13,-6),(10,-5),(11,-2),(14,0),(14,5),(11,9),(8,10),(7,6),(8,3),(6,0),(5,-4),(3,-8)]],
137:[[(-14,-25),(8,-25),(9,-19),(8,-16),(10,-13),(8,-9),(5,-6),(1,-4),(-4,-5),(-8,-6),(-12,-9),(-14,-13)],[(8,-4),(12,-2),(12,2),(11,6),(9,11),(6,12),(5,10),(7,8),(8,4),(7,1)]],
138:[[(-15,-28),(-4,-28),(0,-23),(1,-15),(-1,-9),(-2,-6),(-4,-5),(-9,-5),(-14,-9),(-15,-20)],[(5,-20),(10,-19),(12,-15),(8,-11),(8,-7),(11,-3),(13,1),(11,4),(10,8),(8,14),(5,14),(4,9),(6,4),(5,0),(4,-4),(3,-9)], [(-12,-5),(-8,-4),(-8,2),(-10,5),(-13,4),(-13,0)]],
139:[[(-15,-29),(-4,-29),(0,-24),(1,-16),(-1,-10),(-2,-7),(-4,-6),(-9,-6),(-14,-10),(-15,-21)],[(5,-21),(10,-20),(12,-16),(8,-12),(8,-8),(11,-4),(13,0),(11,3),(10,7),(8,13),(4,13),(4,8),(6,3),(5,-1),(4,-5),(3,-10)], [(-12,-6),(-8,-5),(-8,1),(-10,4),(-13,3),(-13,-1)]]}
LEGS={
133:[[(-16,11),(-11,11),(-11,15),(-12,19),(-14,24),(-21,24),(-21,19),(-18,16)],[(4,11),(9,11),(12,15),(13,18),(18,19),(18,24),(9,24),(9,19),(7,17),(4,15)]],
136:[[(-12,6),(-7,6),(-7,11),(-10,17),(-10,23),(-17,23),(-17,18),(-13,15)],[(0,6),(5,6),(7,12),(10,18),(12,18),(12,23),(3,23),(2,18),(1,14),(-2,10)]],
137:[[(-10,7),(-5,7),(-3,11),(-5,16),(-5,24),(-14,24),(-14,18),(-11,15)], [(-2,8),(3,8),(5,11),(6,17),(10,19),(10,24),(1,24),(0,18),(-1,15),(-3,12)]],
138:[[(-9,7),(-4,7),(-3,15),(-3,24),(-10,24),(-10,18),(-10,13)], [(-3,7),(1,6),(3,10),(3,24),(-4,24),(-4,17)]],
139:[[(-10,8),(-5,8),(-4,14),(-4,23),(-11,23),(-11,17)], [(-4,8),(0,8),(2,13),(2,23),(-5,23),(-5,16)]]}
HAND_RECTS={133:[(-10,19,-1,24),(1,9,6,12)],136:[(-13,-7,-7,-1),(0,-6,5,-1)],137:[(-15,-15,-9,-9),(3,-13,9,-7)]}
def poly(points):
    im=Image.new('1',(384,384));ImageDraw.Draw(im).polygon([(x+160,y+160)for x,y in points],fill=1);return np.array(im,bool)
def regions(points):
    m=np.zeros((384,384),bool)
    for p in points:m|=poly(p)
    return m
def main():
    out=H/'ultimate_arrival_common_probe03';need(not out.exists(),'Fresh common probe');out.mkdir();parent=H/'prepared_ultimate_hurt02/PL02_U.ARC';a=Archive(parent.read_bytes());rgb=np.array([[(int(w)>>s&31)*255//31 for s in(0,5,10)]for w in a.words],np.int32);lut=np.r_[0,1+((rgb[17:32,None]-rgb[None,1:16])**2).sum(2).argmin(1)].astype(np.uint8);rows=[];pics={'before':[],'after':[]}
    for n,folder in((133,'ultimate_arrival_native01'),(136,'ultimate_arrival136_foot_contacts01'),(137,'ultimate_arrival_native02'),(138,'ultimate_arrival_overhead_arm_composed02'),(139,'ultimate_arrival_overhead_arm_composed02')):
        s=H/folder;b=np.array(Image.open(s/f'before_{n:03}_indices.png'));fresh=np.array(Image.open(s/f'after_{n:03}_indices.png'));head=regions(HEAD[n]);legs=regions(LEGS[n]);hands=np.zeros_like(head)
        for x0,y0,x1,y1 in HAND_RECTS.get(n,[]):hands[y0+160:y1+160,x0+160:x1+160]=True
        hands&=np.isin(b,[10,11,12,13])
        if n==133:hands[179:184,150:159]=True
        # One transparent cell belongs to the new inner thigh contour. Copy
        # the complete new-before boundary, not an alpha-wide global clip.
        if n==136:legs[169,157]=True
        if n==137:
            head[144:157,143:150]=False;head[146:159,164:171]=False
        if n in(138,139):
            arm=np.array(Image.open(s/f'{n:03}_arm_mask.png'))>0;head&=~arm
            hands=np.array(Image.open(s/f'{n:03}_new_clasp_mask.png'))>0
            # The gap immediately below the138 clasp is transparent in the
            # new-before hand. Do not copy its surrounding jacket cuff.
            if n==138:hands[135,158]=True
        common=head|legs|hands;after=fresh.copy();after[common]=lut[b][common];outside=(after>0)&(b==0);yy,xx=np.nonzero(outside);lab,count=label(after>0,np.ones((3,3)));sizes=sorted(map(int,np.bincount(lab.flat)[1:]),reverse=True)
        for f,v,pal,mask in(('before',b,16,15),('after',after,0,0)):
            Image.fromarray(v).save(out/f'{f}_{n:03}_indices.png');im=a.rgba(v,pal);im.save(out/f'{f}_{n:03}.png');pics[f].extend([(f'{n} old {f}',a.composite(n,mask)[0]),(f'{n} new common {f}',im)])
        for name,m in(('head',head),('legs',legs),('hands',hands),('common',common),('outside_before',outside)):Image.fromarray(m.astype(np.uint8)*255).save(out/f'{n:03}_{name}_mask.png')
        rows.append({'ref':n,'source_folder':folder,'source_hashes':{f:sha((s/f'{f}_{n:03}_indices.png').read_bytes())for f in('before','after')},'head_polygons':HEAD[n],'leg_polygons':LEGS[n],'hand_rectangles':HAND_RECTS.get(n,[]),'changed_after_pixels':int((after!=fresh).sum()),'outside_before':[[int(x)-160,int(y)-160,int(after[y,x])]for y,x in zip(yy,xx)],'before_exact':True,'after_noncommon_exact':bool(np.array_equal(after[~common],fresh[~common])),'component_sizes':sizes,'before_metrics':metrics(a.rgba(b,16)),'after_metrics':metrics(a.rgba(after))})
    for form,mask in(('before',15),('after',0)):
        for start in range(0,len(pics[form]),4):page(pics[form][start:start+4],a.composite(0,mask)[0],out/f'{form}_comparison_{start//4:02}.png',cols=2,scale=5)
    write(out/'report.json',{'rows':rows,'palette_map':lut.tolist(),'parent_sha256':sha(parent.read_bytes()),'scope':'새5자세 공통머리/사지 후보.135 보류 제외. 같은 새before가 출처이며 거친 옛몸이나idle 머리를 덮지 않는다.','refs_excluded':[135],'wholebody_resized':False,'old_art_copied':0,'arc_written':False,'effects_added':False,'foot136_one_pixel_high_pending':False,'foot136_module_registration':'ultimate_arrival136_foot_contacts01/report.json','visual_review_pending':True});print(json.dumps([{'ref':r['ref'],'outside':r['outside_before'],'components':r['component_sizes']}for r in rows]))
if __name__=='__main__':main()
