"""새 벽 몸체와 실제 기존 배럴을 원점에서 합쳐 발사팔 편집을 준비한다."""
from pathlib import Path
import sys,json,argparse
import numpy as np
from PIL import Image,ImageDraw

H=Path(__file__).resolve().parent
ROOT=H.parents[2]
sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
from scripts.export_x_consistency import Archive

P=H/'prepared_ultimate_lowhp01/PL02_U.ARC'
PSHA='3dd0d9a2cafd8e4d4355ef131c69c39f794698f6752524b39cf488f5b3bc737b'

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--page',type=int,choices=(1,2),default=1)
    args=parser.parse_args()
    O=H/f'ultimate_wall_shot_inputs{args.page:02}'
    need(not O.exists() and sha(P.read_bytes())==PSHA,'Fresh output/frozen parent required')
    O.mkdir()
    a=Archive(P.read_bytes())
    info=json.loads((H/'ultimate_wall_inputs01/manifest.json').read_text('utf8'))
    refs=(55,57,59)if args.page==1 else(61,63,65)
    sheet=Image.new('RGBA',(1536,1024));guide=Image.new('RGBA',sheet.size);gd=ImageDraw.Draw(guide)
    rows=[]
    for row,(form,mask,start) in enumerate((('before',15,16),('after',0,0))):
        for col,n in enumerate(refs):
            bodypath=H/('ultimate_wall_contacts_probe01'if args.page==1 else'ultimate_wall_page02_contacts01')/form/f'{n:03}_indices.png'
            body=np.array(Image.open(bodypath));pic=a.rgba(body,start)
            r=next(v for v in info['refs']if v['body_ref']==n)
            x0,y0,x1,y1=r['barrel_rect_world'];rect=(x0+160,y0+160,x1+160,y1+160)
            actual=a.composite(n+1,mask)[0]
            guard=Image.new('RGBA',(384,384));guard.alpha_composite(actual.crop(rect),(x0+160,y0+160))
            # Clear the whole rectangle including native transparency, not just
            # opaque texels.  These pixels are protected again at registration.
            arr=np.array(pic);arr[y0+160:y1+160,x0+160:x1+160]=np.array(actual)[y0+160:y1+160,x0+160:x1+160]
            target=Image.fromarray(arr)
            target.save(O/f'{form}_{n+1:03}_edit_target.png');guard.save(O/f'{form}_{n+1:03}_barrel.png')
            cell=target.crop((128,120,192,184)).resize((512,512),Image.Resampling.NEAREST)
            sheet.alpha_composite(cell,(col*512,row*512));guide.alpha_composite(cell,(col*512,row*512))
            sx,sy=(-6,-4)if args.page==1 else(1,-3)
            mx,my=r['original_muzzle_world']
            poly=[(mx+8,my-5),(sx+3,sy-4),(sx+5,sy+8),(mx+7,my+8)]
            gd.line([(col*512+(x+32)*8,row*512+(y+40)*8)for x,y in poly+[poly[0]]],fill=(0,255,128,230),width=3)
            rows.append({'body_ref':n,'shot_ref':n+1,'form':form,'new_body_path':bodypath.relative_to(ROOT).as_posix(),'new_body_sha256':sha(bodypath.read_bytes()),'barrel_rect_world':r['barrel_rect_world'],'original_muzzle_world':r['original_muzzle_world'],'barrel_rgba_sha256':sha(actual.crop(rect).tobytes()),'editable_front_arm_only':True,'new_head_body_legs_fixed':True})
    sheet.save(O/'edit_target.png');guide.save(O/'arm_area_guide.png')
    prompt='''Use case: precise-object-edit of six native game sprites, one page.
The first image is the exact editing target, a1536x1024 plate of three poses in two costumes. Each512x512 cell is a64x64 native-pixel window. Top row: white/navy jacket before acquisition. Bottom row: same body in a sleeveless one-piece sailor swim-dress. The second image marks the front-arm working region only; its green guide is not artwork.

Change ONLY the bent front arm into a left-firing buster arm for each cell. The compact original weapon at the left edge is already placed at the game's exact muzzle position; preserve its position, size, silhouette and angle. Keep the entire newly detailed head/ears/face/gold heart sunglasses/hair, neck, torso, rear raised/contact arm, curled knees and sandals exactly unchanged. The middle/side-back pose stays angled; do not turn the torso to face forward. Connect the same shoulder to the weapon by a naturally extended short upper arm and forearm. Remove the old bent front fist; do not leave two front hands. Avoid disconnected wrist pixels, a stretched rectangular sleeve, long sausage arm, broadened torso or any whole-body scaling.

Top-row arms have the same oversized SHORT white jacket sleeves with navy/gold cuff and clear folds. Bottom-row arms are bare skin of the same joint centerline and thickness, without leftover cuffs or sleeve fragments. Match the target's crisp native pixel clusters and clean dark outline, no blurry resizing or scratch texture. This is an arm-only edit: the existing high-detail character art outside the front arm is authoritative.

Output only the six exact same-position sprites on true transparent background, same cell layout, no labels, grid, guide lines, wall, floor, shadow or additional poses.'''
    (O/'prompt.txt').write_text(prompt+'\n','utf8')
    write(O/'inputs.json',{'source_arc_sha256':PSHA,'records':rows,'generated':False,'packed':False,'not_ready_for_game':True,'barrel_scope':'Actual current PL02 composite, full RGBA rectangle including transparency','source_cell_native':[64,64],'source_canvas':[1536,1024],'no_old_body_pixels_used':True})
    print(str(O))

if __name__=='__main__':main()
