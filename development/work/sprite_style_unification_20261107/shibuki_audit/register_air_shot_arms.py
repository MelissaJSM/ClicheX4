"""새 발사팔만 의미 영역으로 등록한다. 단색 채움/팔 늘임/기존 머리 복원 없음."""
from pathlib import Path
import sys,json
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
import numpy as np
from PIL import Image
from scripts.export_x_consistency import Archive,page
from native_pose_pack import sha,need,write
from inspect_air_layers import P
from prepare_air_body_layers import polygon,rect
from prepare_lowhp_final import compose

REFS=(33,35,37,39,41,43,45,47,49,51,53)
def arm_masks(n):
    removed={
        33:[(-17,-8),(-7,-8),(-3,-3),(-4,5),(-15,6)],
        35:[(-18,-9),(-7,-9),(-3,-3),(-5,5),(-15,6)],
        37:[(-19,-19),(-9,-19),(-7,-11),(-5,-5),(-9,-2),(-18,-8)],
        39:[(-16,-28),(-7,-28),(-6,-20),(-8,-12),(-13,-11)],
        41:[(-19,-29),(-7,-29),(-6,-20),(-8,-11),(-15,-12)],
        43:[(-22,-25),(-10,-25),(-9,-17),(-7,-11),(-11,-7),(-21,-14)],
        45:[(-17,-11),(-7,-11),(-3,-5),(-4,5),(-15,6)],
        47:[(-17,-10),(-7,-10),(-3,-4),(-4,6),(-15,7)],
        49:[(-17,-8),(-7,-8),(-3,-3),(-4,7),(-15,8)],
        51:[(-17,-4),(-7,-4),(-3,2),(-4,10),(-15,11)],
        53:[(-17,-6),(-7,-6),(-3,0),(-4,8),(-15,9)],
    }[n]
    # The cut runs below the face into the same shoulder; the new source supplies
    # skin/clothing/transparent pixels inside it, never a flat replacement color.
    added={
        33:[(-25,-11),(-13,-11),(-8,-8),(-3,-5),(-3,1),(-15,1),(-22,-4)],
        35:[(-25,-11),(-13,-11),(-8,-8),(-3,-5),(-3,1),(-16,1),(-23,-4)],
        37:[(-24,-11),(-12,-11),(-8,-8),(-3,-4),(-4,1),(-16,1),(-23,-4)],
        39:[(-23,-11),(-13,-11),(-8,-8),(-3,-6),(-2,-2),(-13,-2),(-22,-5)],
        41:[(-23,-11),(-13,-11),(-8,-8),(-3,-6),(-2,-2),(-13,-2),(-22,-5)],
        43:[(-23,-11),(-13,-11),(-8,-8),(-3,-6),(-2,-2),(-13,-2),(-22,-5)],
        45:[(-24,-10),(-12,-10),(-8,-6),(-3,-4),(-3,1),(-16,1),(-23,-3)],
        47:[(-24,-10),(-12,-10),(-8,-6),(-3,-4),(-3,1),(-16,1),(-23,-3)],
        49:[(-26,-12),(-14,-12),(-8,-7),(-3,-4),(-3,2),(-16,2),(-24,-3)],
        51:[(-27,-8),(-15,-8),(-9,-3),(-3,0),(-3,6),(-17,6),(-25,1)],
        53:[(-27,-8),(-15,-8),(-9,-3),(-3,-1),(-3,5),(-17,5),(-25,0)],
    }[n]
    rm=polygon(removed)
    # This two-pixel old cuff remains beyond the slanted polygon for ref42.
    # Sample its exact location from the regenerated transparent source too.
    if n==41:rm|=rect((-18,-19,-16,-16))
    return rm,polygon(added)

def main():
    out=H/'air_shot_arms_registered06';need(not out.exists(),'Fresh output required');out.mkdir();a=Archive(P.read_bytes());src=H/'air_shot_native_probe02';rows=[]
    for form,pal,mask in(('base',0,0),('fourth',16,15)):
        pics=[]
        for n in REFS:
            oldlayers={b:np.array(Image.open(H/f'air_body_layers01/{n:03}_bank{b}_indices.png'))for b in(0,5,6,7,8)}
            # A partial costume genuinely displays two CLUTs. Keep RGBA from
            # each layer rather than falsely collapsing it into one palette.
            body=oldlayers[0].copy();body_rgba=np.array(compose(a,oldlayers,mask))
            source=np.array(Image.open(src/f'{form}_{n+1:03}_source_indices.png'));remove,add=arm_masks(n)
            hair=np.array(Image.open(H/f'air_common_head_probe03/{n:03}_common_head_mask.png'))>0
            # White sleeve and lavender highlights share indices; a broad hair
            # color mask would wrongly erase the new sleeve. Use the visible
            # face boundary instead. The locally regenerated source also owns
            # the ear contour revealed by removal of the raised front arm.
            faceboxes={33:(-9,-13,1,-4),35:(-9,-13,1,-4),37:(-9,-14,1,-4),39:(-8,-16,1,-5),41:(-7,-16,2,-5),43:(-9,-15,1,-5),45:(-10,-13,0,-3),47:(-9,-13,1,-3),49:(-9,-13,1,-3),51:(-10,-9,0,1),53:(-10,-10,0,0)}
            face=rect(faceboxes[n]);patch=(remove|add)&~face
            # The generator shifted the barrel in refs46/48. Never register
            # that extra barrel: the source's hand below and sleeve behind the
            # actual casing remain. No hand/body coordinate is stretched.
            if n in(45,47):patch&=~rect((-32,-14,-11,-4))
            q=body.copy();q[patch]=source[patch];display=body_rgba.copy();display[patch]=np.array(a.rgba(source,pal))[patch]
            gun=np.array(Image.open(H/f'air_barrel_guard02/{n+1:03}_indices.png'));gm=np.array(Image.open(H/f'air_barrel_guard02/{n+1:03}_mask.png'))>0
            q[gm]=gun[gm];display[gm]=np.array(a.rgba(gun,0))[gm];allowed=patch|gm
            need(np.array_equal(display[~allowed],body_rgba[~allowed]),'Body outside arm changed')
            need(np.array_equal(q[gm],gun[gm]),'Actual barrel changed')
            rgba=Image.fromarray(display);rgba.save(out/f'{form}_{n+1:03}.png')
            if form=='base':Image.fromarray(q).save(out/f'{form}_{n+1:03}_indices.png')
            Image.fromarray(np.where(patch,source,0).astype(np.uint8)).save(out/f'{form}_{n+1:03}_arm_source_indices.png');Image.fromarray(allowed.astype(np.uint8)*255).save(out/f'{form}_{n+1:03}_allowed_mask.png');Image.fromarray(patch.astype(np.uint8)*255).save(out/f'{form}_{n+1:03}_patch_mask.png')
            delta=np.any(display!=body_rgba,axis=2);heat=display.copy();heat[delta]=(255,40,180,255);Image.fromarray(heat).save(out/f'{form}_{n+1:03}_delta.png')
            rows.append({'form':form,'ref':n+1,'body_ref':n,'source_sha256':sha(source.tobytes()),'target_rgba_sha256':sha(display.tobytes()),'source_only_arm_patch_pixels':int(patch.sum()),'changed_pixels':int(delta.sum()),'visible_new_head_preserved_pixels':int(np.count_nonzero(body[hair&~patch&~gm])),'arm_revealed_hair_comes_from_new_source':True,'body_outside_patch_exact':True,'gun_guard_exact':True,'manual_flat_fill_or_stretch':False,'visual_review_pending':True})
            pics.extend([(f'{n} fixed new body',Image.fromarray(body_rgba)),(f'{n+1} registered firing arm',rgba)])
        for i in range(0,len(pics),6):page(pics[i:i+6],a.composite(0,mask)[0],out/f'{form}_comparison_{i//6:02}.png',cols=2,scale=5)
    write(out/'registration.json',{'candidate_only':True,'source_parent_sha256':sha(P.read_bytes()),'rows':rows,'resource_written':False,'arm_source_only_registration':True})
    print(json.dumps({'output':str(out),'rows':len(rows)}))
if __name__=='__main__':main()
