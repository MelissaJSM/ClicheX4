"""Prepare a local ear/raised-hand correction; protect lower artwork."""
from pathlib import Path
import sys,json,hashlib
import numpy as np
from PIL import Image,ImageDraw
D=Path(__file__).resolve().parent;W=D.parent;ROOT=W.parents[1];sys.path.insert(0,str(ROOT))
from scripts.export_x_consistency import Archive
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
p=W/'shibuki_audit/prepared_nova_strike_base01/PL00_U.ARC';assert sha(p)=='36d4d0293abc77052c476e0495f4f4542ca75471c7a149f200e4bdb8f4e1bd4e';a=Archive(p.read_bytes())
out=D/'reach229_inputs03';out.mkdir(exist_ok=False);target=Image.new('RGBA',(2048,1024));old=Image.new('RGBA',target.size);points=[];crop=(96,96,224,224)
for col,mask in enumerate((8,15)):
    form='base_legs'if mask==8 else'fourth';src=D/'registered_neutral03'/f'{form}_229_nearest_indices.png';z=np.array(Image.open(src));q=a.layer(229,0)[0].copy()
    for bit,pb in((8,8),(1,5),(4,7),(2,6)):
        if mask&bit:
            v=a.layer(229,pb)[0];q[v>0]=v[v>0]
    target.alpha_composite(a.rgba(z,0 if mask==8 else 16).crop(crop).resize((1024,1024),Image.Resampling.NEAREST),(1024*col,0));old.alpha_composite(a.composite(229,mask)[0].crop(crop).resize((1024,1024),Image.Resampling.NEAREST),(1024*col,0))
    palms=[]
    for left,right in((138,156),(158,175)):
        yy,xx=np.nonzero(np.isin(q[128:142,left:right]%16,(9,10,11)));assert len(xx)>0
        palms.append({'bbox_world':[int(xx.min()+left-160),int(yy.min()-32),int(xx.max()+left-159),int(yy.max()-31)]})
    points.append({'form':form,'source':src.relative_to(ROOT).as_posix(),'source_sha256':sha(src),'palms':palms})
target.save(out/'edit_target.png');old.save(out/'original_pose.png');guide=target.copy();dr=ImageDraw.Draw(guide)
for col,r in enumerate(points):
    for q in r['palms']:
        x0,y0,x1,y1=q['bbox_world'];dr.rectangle((col*1024+(x0+63)*8,(y0+63)*8,col*1024+(x1+65)*8,(y1+65)*8),outline=(0,255,140,255),width=3)
    dr.line((col*1024+44*8,40*8,col*1024+79*8,40*8),fill=(0,190,255,255),width=3)
guide.save(out/'position_guide.png')
prompt='''Use case: precise-object-edit.
Image1 is the edit target: two detailed hovering console sprites on a2048x1024 transparent sheet. Each cell is128x128 native pixels enlarged8x, origin(64,64). Image2 is the original intended pose. Image3 is a position guide ONLY: the green boxes mark the intended two fists, and the cyan line marks the approximate original ear-tip height. Do not include these guide marks in output.
Correct ONLY the upper ear tips and two raised forearms/hands in each sprite. The edited sprites' ears accidentally became too tall and their fists dropped below the ear tips. Restore the original upward-reaching posture in Image2. Keep the face, eye, bangs, braid, head width and neck completely fixed. Shorten the exaggerated upper ear triangles by about4 native pixels, so the ear tips end around worldY=-24, preserving clean lavender inner-ear shading. Lift BOTH small fists and their connected forearms into the green target boxes, original palm top around worldY=-27, above the shortened ear tips. Do not make extra hands or arms. Preserve the original shoulder positions, reconnect the raised elbows/forearms naturally. Do not flatten the whole top of the head or move the face.
LEFT costume keeps pale white/lavender sleeves and red cuff accents. RIGHT keeps dark purple/black sleeves with gold details and only small pale cuffs; do not copy a broad white left sleeve to the right. Both fists have the existing warm skin color and thin purple contour. Keep the exact outfit identity and coverage.
Strictly preserve all pixels below the upper-arm/neck area: neck, torso, chest, hem, draped cloth, hips, knees, both dark boots and their soles. Do not enlarge, recenter, rotate, lengthen legs, make new accessories, restore the old simple hair, or change the background. Keep the exact fixed canvas/cell placement and the new detailed thin-contour style from Image1. True transparency, no shadows/glow/text. Return two sprites with only the corrected ear/raised-hand reach.'''
(out/'prompt.txt').write_text(prompt,'utf8');(out/'input.json').write_text(json.dumps({'parent_sha256':sha(p),'source_frames':points,'crop':list(crop),'cell':[128,128],'origin':[64,64],'ear_tip_target_world_y':-24,'policy':'229 과도한 귀높이와 낮아진 두손만 국소수정. 새얼굴/옷/다리/발은보존.','files':{f.name:sha(f)for f in out.iterdir()if f.is_file()}},ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps(points))
