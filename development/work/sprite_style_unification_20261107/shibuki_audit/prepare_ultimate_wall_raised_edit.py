"""새 두상 모듈을 목 기준점으로 옮기고 원 손 접점에 새 손을 놓은 팔 교정 입력."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image,ImageDraw
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import sha,need,write
from scripts.export_x_consistency import Archive,page
from register_ultimate_lowhp_pilot import move
I=H/'ultimate_wall_page02_native01';O=H/'ultimate_wall_raised_edit01';P=H/'prepared_ultimate_lowhp01/PL02_U.ARC'
def main():
    need(not O.exists(),'Fresh output required');O.mkdir();a=Archive(P.read_bytes());board=Image.new('RGBA',(1536,512));rows=[];items=[]
    basepoly=[[-7,-27],[3,-29],[10,-27],[10,-21],[13,-19],[11,-14],[9,-9],[6,-6],[-1,-6],[-6,-12],[-9,-18]]
    for i,n in enumerate((61,63,65)):
        q=np.array(Image.open(I/f'{n:03}_indices.png'));out=q.copy();poly=[(x+(0 if n==61 else 1),y)for x,y in basepoly]
        m=Image.new('1',(384,384));ImageDraw.Draw(m).polygon([(x+160,y+160)for x,y in poly],fill=1);mask=np.array(m,bool)
        head=np.where(mask,q,0).astype(np.uint8);dx,dy=(-5,3)if n==65 else(-3,3);out[mask]=0;mh=move(head,dx,dy);out[mh>0]=mh[mh>0]
        rect,delta={61:([13,-29,20,-21],[-1,0]),63:([16,-23,23,-16],[-3,-4]),65:([17,-28,24,-19],[-7,1])}[n]
        x0,y0,x1,y1=rect;hand=np.zeros_like(q);hand[y0+160:y1+160,x0+160:x1+160]=q[y0+160:y1+160,x0+160:x1+160]
        out[y0+160:y1+160,x0+160:x1+160]=0;ph=move(hand,*delta);out[ph>0]=ph[ph>0]
        Image.fromarray(out).save(O/f'{n:03}_pose_guide_indices.png');Image.fromarray(head).save(O/f'{n:03}_head_module.png');Image.fromarray(hand).save(O/f'{n:03}_hand_module.png')
        a.rgba(out,16).save(O/f'{n:03}_pose_guide.png');board.alpha_composite(a.rgba(out,16).crop((128,120,192,184)).resize((512,512),Image.Resampling.NEAREST),(i*512,0))
        rows.append({'ref':n,'head_module_translation':[dx,dy],'head_module_polygon_world':poly,'hand_module_rect_world':rect,'hand_translation':delta,'source_sha256':sha((I/f'{n:03}_indices.png').read_bytes()),'old_head_copied':False,'scale_changed':False,'guide_only_not_packable':True})
        items.extend([(f'{n} new source',a.rgba(q,16)),(f'{n} contact guide gaps need art',a.rgba(out,16))])
    board.save(O/'edit_target.png');page(items,a.composite(0,15)[0],O/'guide_review.png',cols=2,scale=5)
    prompt='''Precise local edit of edit_target.png: finish ONLY the raised-right-arm/neck/hair-junction connections of these three Ultimate jacket Shibuki sprites. The first image is an exact native coordinate guide with the existing new detailed head and exposed hand already moved to the required wall-contact positions. Some seam/gap/stub artifacts from those translations are intentional editing guides, not final design. Repair them naturally. The second image after_edit_target.png is the untouched NEW detailed source, for exact body/feet/clothing/hair design. The third old pose sheet is ONLY a geometric contact reference; never copy its coarse head, plain white clothing or simplified limbs.

Canvas1536x512, three equal512px cells at8x native scale. Native viewport64x64, world(-32,-40..32,24), origin(32,40). Preserve the guide head and hand positions. Left61 head was moved left3/down3 native pixels and raised palm left1. Middle63 head left3/down3 and raised palm left3/up4. Right65 head left5/down3 and raised palm left7/down1. Do NOT move those palms back to the untouched second image positions. Keep the head/ears/face/glasses precisely the same SIZE and detailed shape; the correction is position only. Preserve all pixels of legs/knees/sandals, lower torso, tail, forward fist and lower jacket at the positions of the detailed source.

Between the existing shoulder and the now correctly placed raised palm, redraw a naturally shorter or more vertically bent jacket sleeve with a sensible elbow. Keep compact arm length and thick folded sleeve volume, dark cuff with gold trim, white/navy Ultimate jacket. Remove the old angled sleeve stub, reconnect the shifted head to the existing collar/neck, and repair the small back-hair seam where the head moved. Never lengthen a rectangular strip, duplicate an arm, float a hand, cover the face with a sleeve or add black padding to hide gaps. The right hand is adjacent to/above the head in these wall-contact poses, with the exact positions from the first guide.

Retain lavender layered hair, gold heart sunglasses, navy flower, small human face, crisp sailor collar and pink necktie, gold-edged white/navy jacket, compact full-bodied proportions and subtle game-pixel highlights. No full-body rescaling, new pose, changed foot position, enlarged head, flat blob, futuristic armor, red shrine costume or naked/sleeveless arm. This page is jacket BEFORE acquisition. Only repair the specified upper-body connections. Output three clean sprites on true transparency, same cell placement, no guide artifacts, grids, labels, walls, floor or shadows.'''
    (O/'prompt.txt').write_text(prompt+'\n','utf8');write(O/'inputs.json',{'rows':rows,'generated':False,'game_written':False,'parent_sha256':sha(P.read_bytes()),'geometry_reason':'발 고정 후 얼굴이 x+3/+3/+5,y-3이고 들린 손이 특히63/65에서 벽 접점 밖으로 움직였다. 같은 새 두상/손 모듈을 평행이동해 크기와 정체성을 유지하며 팔 연결부만 다시 그린다.','sources':{str(p.relative_to(ROOT)):sha(p.read_bytes())for p in[O/'edit_target.png',I/'after_edit_target.png',H/'ultimate_wall_inputs01/page02_before_poses.png']}})
    print(str(O))
if __name__=='__main__':main()
