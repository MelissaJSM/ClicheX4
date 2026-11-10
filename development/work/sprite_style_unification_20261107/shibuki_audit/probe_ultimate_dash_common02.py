"""후반 낮은대시·회복75/77/79의 새 머리와 맨다리 공통 후보."""
from pathlib import Path
import json,sys
import numpy as np
from PIL import Image,ImageDraw
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
from scripts.export_x_consistency import Archive,page,metrics
from probe_ultimate_dash_common01 import poly
HEAD={75:[(-27,-12),(14,-12),(14,7),(3,7),(0,5),(-4,6),(-5,10),(-20,10),(-27,6)],77:[(-21,-22),(21,-22),(21,4),(13,4),(11,1),(9,0),(3,-1),(-4,-1),(-9,1),(-14,1),(-21,-3)],79:[(-18,-23),(18,-23),(18,3),(10,3),(7,0),(2,-2),(-3,-3),(-7,-2),(-15,-2),(-18,-6)]}
LEGS={75:[[(-14,16),(-9,16),(-6,18),(-2,20),(-2,24),(-13,24),(-14,18)],[(0,15),(6,15),(13,18),(14,24),(6,24),(5,20),(-1,18)]],77:[[(-11,10),(-6,9),(-1,11),(1,19),(-2,24),(-10,24),(-11,18),(-13,13)],[(2,12),(8,12),(13,15),(20,19),(20,24),(12,24),(11,19),(4,16)]],79:[[(-9,9),(-4,9),(-2,13),(-1,20),(-3,24),(-12,24),(-11,18),(-11,11)],[(2,12),(6,11),(9,14),(16,18),(17,24),(10,24),(10,19),(4,16)]]}
def main():
    o=H/'ultimate_dash_common_probe02';need(not o.exists(),'Fresh output');o.mkdir();src=H/'ultimate_dash_native02';a=Archive((H/'prepared_ultimate_air01/PL02_U.ARC').read_bytes());rgb=np.array([[(int(w)>>s&31)*255//31 for s in(0,5,10)]for w in a.words],np.int32);lut=np.r_[0,1+((rgb[17:32,None]-rgb[None,1:16])**2).sum(2).argmin(1)].astype(np.uint8);yy,xx=np.indices((384,384));x,y=xx-160,yy-160;rows=[];pics={'before':[],'after':[]}
    for n in(75,77,79):
        before=np.array(Image.open(src/f'before_{n:03}_indices.png'));fresh=np.array(Image.open(src/f'after_{n:03}_indices.png'));head=poly(HEAD[n]);legs=poly(LEGS[n][0])|poly(LEGS[n][1]);common=head|legs;after=fresh.copy();after[common]=lut[before][common];outside=(after>0)&(before==0);points=[[int(px-160),int(py-160),int(after[py,px])]for py,px in zip(*np.nonzero(outside))]
        for form,v,pal,mask in(('before',before,16,15),('after',after,0,0)):
            Image.fromarray(v).save(o/f'{form}_{n:03}_indices.png');im=a.rgba(v,pal);im.save(o/f'{form}_{n:03}.png');pics[form].extend([(f'{n} current {form}',a.composite(n,mask)[0]),(f'{n} new common {form}',im)])
        for k,v in(('head',head),('legs',legs),('common',common),('outside',outside)):Image.fromarray(v.astype(np.uint8)*255).save(o/f'{n:03}_{k}_mask.png')
        need(np.array_equal(after[~common],fresh[~common]),'Costume outside common changed');rows.append({'ref':n,'head_polygon':HEAD[n],'legs_polygons':LEGS[n],'common_opaque_pixels':int(np.count_nonzero(before[common])),'changed_after_common':int(np.count_nonzero(after!=fresh)),'outside_jacket_pixels':points,'foot_before':metrics(a.rgba(before,16))['bbox'][3]-1,'foot_after':metrics(a.rgba(after,0))['bbox'][3]-1,'source_old_art_reused':0})
    for form,mask in(('before',15),('after',0)):page(pics[form],a.composite(0,mask)[0],o/f'{form}_comparison.png',cols=2,scale=5)
    write(o/'report.json',{'source_report_sha256':sha((src/'report.json').read_bytes()),'parent_sha256':sha(a.data),'palette_mapping':lut.tolist(),'rows':rows,'status':'semantic common-mask probe; outside and joints not yet accepted','arc_written':False});print(json.dumps(rows))
if __name__=='__main__':main()
