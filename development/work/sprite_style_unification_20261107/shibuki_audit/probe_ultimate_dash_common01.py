"""새 얼티밋 대시67/69/71에서 머리와 맨다리 공통화. 후보만 출력."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image,ImageDraw
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
from scripts.export_x_consistency import Archive,page,metrics
HEAD={67:[(-20,-24),(15,-24),(15,1),(8,1),(3,-2),(-5,-2),(-11,-2),(-20,-6)],69:[(-23,-19),(17,-19),(17,4),(8,4),(5,1),(0,2),(-6,2),(-16,2),(-23,-2)],71:[(-28,-13),(17,-13),(17,5),(8,5),(2,4),(-1,10),(-8,10),(-19,10),(-28,5)]}
LEGS={67:[[(-9,10),(-2,10),(-1,13),(3,17),(0,23),(-10,23),(-10,13)],[(6,12),(9,12),(15,15),(19,18),(19,24),(10,24),(9,17),(3,13)]],69:[[(-8,12),(-2,12),(3,18),(1,23),(-7,23),(-7,18),(-10,14)],[(4,13),(9,13),(18,15),(18,20),(11,20),(11,17),(4,16)]],71:[[(-14,16),(-4,16),(-1,18),(1,23),(-14,23)],[(4,15),(11,15),(16,17),(17,23),(10,23),(9,20),(3,18)]]}
def poly(points):
    im=Image.new('1',(384,384));ImageDraw.Draw(im).polygon([(x+160,y+160)for x,y in points],fill=1);return np.array(im,bool)
def main():
    o=H/'ultimate_dash_common_probe01';need(not o.exists(),'Fresh output');o.mkdir();p=H/'prepared_ultimate_air01/PL02_U.ARC';a=Archive(p.read_bytes());need(sha(a.data)=='3ae1d8d56c595b04e59abf735ac377ab381c73673c2eaade99679031f3fc65f7','Wrong parent');rgb=np.array([[(int(w)>>s&31)*255//31 for s in(0,5,10)]for w in a.words],np.int32);lut=np.r_[0,1+((rgb[17:32,None]-rgb[None,1:16])**2).sum(2).argmin(1)].astype(np.uint8);rows=[];pics=[]
    for n in(67,69,71):
        src=H/'ultimate_dash_native01';before=np.array(Image.open(src/f'before_{n:03}_indices.png'));fresh=np.array(Image.open(src/f'after_{n:03}_indices.png'));head=poly(HEAD[n]);legs=poly(LEGS[n][0])|poly(LEGS[n][1]);common=head|legs;after=fresh.copy();after[common]=lut[before][common];outside=(after>0)&(before==0);points=[[int(x-160),int(y-160),int(after[y,x])]for y,x in zip(*np.nonzero(outside))]
        # 이 후보 단계에서 바깥점을 자의로 채우거나 지우지 않는다.
        for form,v,pal in(('before',before,16),('after',after,0)):
            Image.fromarray(v).save(o/f'{form}_{n:03}_indices.png');a.rgba(v,pal).save(o/f'{form}_{n:03}.png')
        for label,v in(('head',head),('legs',legs),('common',common),('outside',outside)):Image.fromarray(v.astype(np.uint8)*255).save(o/f'{n:03}_{label}_mask.png')
        need(np.array_equal(after[~common],fresh[~common]),'New costume or bare arm changed outside common mask');pics.extend([(f'{n} new jacket source',a.rgba(before,16)),(f'{n} same new head/legs',a.rgba(after,0))]);rows.append({'ref':n,'head_polygon':HEAD[n],'legs_polygons':LEGS[n],'common_opaque_pixels':int(np.count_nonzero(before[common])),'after_changed_in_common':int(np.count_nonzero(after!=fresh)),'outside_jacket_pixels':points,'foot_y_before':metrics(a.rgba(before,16))['bbox'][3]-1,'foot_y_after':metrics(a.rgba(after,0))['bbox'][3]-1,'old_art_copied':0,'source_changed':False,'exact_noncommon_after':True})
    page(pics,a.composite(0,15)[0],o/'comparison.png',cols=2,scale=5);write(o/'report.json',{'source':'ultimate_dash_native01','parent_sha256':sha(a.data),'palette_mapping':lut.tolist(),'rows':rows,'status':'common mask visual probe; foot69 adjustment and outside-source audit pending','arc_written':False,'user_accepted':False});print(json.dumps(rows))
if __name__=='__main__':main()
