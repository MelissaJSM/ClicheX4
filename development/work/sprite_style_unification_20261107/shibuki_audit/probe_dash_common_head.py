"""대시 새머리 공통층 + 새 포스 장식16px 후보. 아직 자원 쓰기 없음."""
from pathlib import Path
import sys,json,struct
import numpy as np
from PIL import Image,ImageDraw
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
from scripts.export_x_consistency import Archive,page
from scripts.prepare_shibuki_ultimate_production import records
P=H/'prepared_rising_right_base01/PL00_U.ARC';D=H/'dash_detail_contacts02'
REFS=(67,69,71,75,77,79,81,83,93,94)
EYES={67:(-8,-6),69:(-11,-1),71:(-17,6),75:(-16,6),77:(-11,-3),79:(-7,-6),81:(-8,-8),83:(-8,-9),93:(-7,-8),94:(-10,0)}
def poly(points):
    im=Image.new('1',(384,384));ImageDraw.Draw(im).polygon([(x+160,y+160)for x,y in points],fill=1);return np.array(im,bool)
def main():
    o=H/'dash_common_head_probe01';need(not o.exists(),'Fresh output required');o.mkdir();a=Archive(P.read_bytes());meta=json.loads((D/'report.json').read_text('utf8'))
    yy,xx=np.indices((384,384));x=xx-160;y=yy-160
    rgb=np.array([[(int(w)>>s&31)*255//31 for s in(0,5,10)]for w in a.words[:48]],np.int32)
    mapping={i:int(np.argmin(((rgb[17:32]-rgb[i])**2).sum(1)))+1 for i in range(1,16)}
    templates={records(a.c,5,n)[i:i+4]for n in range(237)for i in range(0,len(records(a.c,5,n)),4)}
    rows=[];pics=[]
    for n in REFS:
        base=np.array(Image.open(D/f'base_{n:03}_indices.png'));raw=np.array(Image.open(D/f'fourth_{n:03}_indices.png'));full=raw.copy();ex,ey=EYES[n]
        for form in('base','fourth'):
            r=next(r for r in meta['rows']if r['form']==form and r['ref']==n);need(sha((D/f'{form}_{n:03}_indices.png').read_bytes())==r['output_sha256'],'Changed contact')
        # Face / forelocks / long hair, always taken from this newly drawn base.
        region=poly([(ex-12,ey-18),(ex+16,ey-18),(ex+16,ey-7),(ex+34,ey-2),(ex+34,ey+5),(ex+17,ey+8),(ex+5,ey+3),(ex-6,ey+3),(ex-12,ey-3)])
        face=(x>=ex-4)&(x<=ex+4)&(y>=ey-3)&(y<=ey+3)
        common=region&(np.isin(base,[0,2,5,8,14,15])|(face&np.isin(base,[7,10,11,12,13])))
        # This tiny ornament window remains the native Head equipment owner.
        decoration=(x>=ex+5)&(x<ex+21)&(y>=ey-13)&(y<ey+3)&region
        common|=decoration
        if n==93:
            raised=poly([(-20,-20),(-9,-20),(-9,-11),(-7,-5),(-12,-3),(-20,-8)])
            common&=~raised;decoration&=~raised
        full[common]=0;full[decoration]=raw[decoration]
        # Overlay can cover, not erase. Only the new base outline differences
        # within the new Fourth material envelope are registered here.
        edge=(base>0)&(full==0)&(~common|decoration);marks=[]
        materials={1:2,4:11,10:10,11:11,12:9,13:9,15:1}
        for py,px in zip(*np.nonzero(edge)):
            src=int(base[py,px]);dst=materials.get(src,mapping[src]);full[py,px]=dst;marks.append([int(px)-160,int(py)-160,src,dst])
        head=np.where(decoration,full,0).astype(np.uint8);rest=np.where(~decoration,full,0).astype(np.uint8)
        result=a.rgba(base);result.alpha_composite(a.rgba(rest,16));result.alpha_composite(a.rgba(head,16))
        Image.fromarray(common.astype(np.uint8)*255).save(o/f'{n:03}_common_mask.png');Image.fromarray(head).save(o/f'{n:03}_head_indices.png');Image.fromarray(rest).save(o/f'{n:03}_rest_indices.png');result.save(o/f'{n:03}_fourth.png')
        ys,xs=np.nonzero(head);bbox=[int(xs.min()-160),int(ys.min()-160),int(xs.max()+1-160),int(ys.max()+1-160)];candidates=[]
        for r in templates:
            flag,t,tx,ty=struct.unpack('<BBbb',r)
            if flag==0 and t not in(0,16) and tx<=bbox[0] and ty<=bbox[1] and tx+16>=bbox[2] and ty+16>=bbox[3]:candidates.append(r.hex())
        rows.append({'ref':n,'head_bbox_world':bbox,'existing_head_records':sorted(candidates),'new_base_common_pixels':int((common&(base>0)).sum()),'edge_material_pixels':marks,'old_art_pixels_used':0})
        pics.extend([(f'{n} raw new Fourth',a.rgba(raw,16)),(f'{n} new common hair + ornament',result)])
    for i in range(0,len(pics),6):page(pics[i:i+6],a.composite(0,15)[0],o/f'comparison_{i//6:02}.png',cols=2,scale=5)
    write(o/'probe.json',{'parent_sha256':sha(P.read_bytes()),'contact_report_sha256':sha((D/'report.json').read_bytes()),'rows':rows,'bank_boundaries_changed':False,'resource_written':False,'body_owner_pending':True,'native_palette16_vs32_diff':[(i,int(a.words[16+i]),int(a.words[32+i]))for i in range(16)if a.words[16+i]!=a.words[32+i]],'visual_review_pending':True})
    print(json.dumps([{'ref':r['ref'],'head':r['head_bbox_world'],'records':len(r['existing_head_records']),'edges':len(r['edge_material_pixels'])}for r in rows]))
if __name__=='__main__':main()
