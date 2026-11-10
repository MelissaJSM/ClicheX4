"""기본90/91의 별도 두 자세를 보존한 Ultimate 의상 네셀 입력."""
from pathlib import Path
import sys,json
from PIL import Image
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
from scripts.export_x_consistency import Archive
def main():
    d=H/'ultimate_standing_followthrough_inputs01';need(not d.exists(),'새 입력 폴더 필요')
    p=H/'prepared_standing_special_ultimate01/PL02_U.ARC';bp=H/'prepared_standing_fire_base01/PL00_U.ARC';a=Archive(p.read_bytes());b=Archive(bp.read_bytes())
    need(sha(a.data)=='26fd4c46813775ae7a2210b463725952abbabc5f3c172eafb7b5533f994168ce','Ultimate부모 변경');need(sha(b.data)=='4fe7173665d2bd2e5484a8c62eeb17d286ee61b781abf78e9525e03acb5f8175','기본신작 변경')
    target=Image.new('RGBA',(1536,1536));style=Image.new('RGBA',target.size);old=Image.new('RGBA',target.size);crop=(112,112,208,208)
    for row,n in enumerate((90,91)):
        for col,(form,mask)in enumerate((('before',15),('after',0))):
            pos=(col*768,row*768)
            target.alpha_composite(b.composite(n,0)[0].crop(crop).resize((768,768),Image.Resampling.NEAREST),pos)
            ref=a.composite(0,mask)[0]if row==0 else Image.open(H/f'ultimate_standing_fire_common01/{form}_089.png').convert('RGBA')
            style.alpha_composite(ref.crop(crop).resize((768,768),Image.Resampling.NEAREST),pos)
            old.alpha_composite(a.composite(n,mask)[0].crop(crop).resize((768,768),Image.Resampling.NEAREST),pos)
    prompt='''Use case: identity-preserve.
Asset: exact-position console pixel sprites for the same established fox character, with two costume variants.
Image1 is the EDIT TARGET: a transparent1536x1536 page, exactly2columns and2rows of768x768 cells, each96x96 logical pixels at8x. KEEP this whole page geometry, every sprite's exact current scale and anchor and the large blank margins. No cropping, enlargement or centering to fill cells.
TOP row90 has the torso leaning left and the front arm pointing the short purple buster diagonally up-left; the rear hand rests behind the hip. BOTTOM row91 has the buster lowered to horizontal left and a different wider knee/foot stance. These are TWO DISTINCT BODY POSES; do not recycle one body or the idle body. Preserve each muzzle coordinate and angle, gun dimensions, hand/wrist/elbow locations, head angle and gaze, torso tilt, knees, ankle positions, sole heights and the exact foot silhouettes. Exactly two arms and two hands. Retain the short, softly rounded proportions with ear-inclusive head about38percent of full height, short torso and limbs. Keep native proportions, without longer legs or a slimmer body.
Image2 is the outfit/detail reference: upper row is each costume's accepted idle; lower row is the newly detailed raised-buster pose of the SAME character. LEFT column: pale lavender-white cropped jacket, dark navy collar/cuff shadows, visible zipper and fabric folds over the reference lavender one-piece outfit, narrow pink center accent, bare lower legs and sandals. RIGHT column: the same reference lavender one-piece and center accent, bare shoulders, bare arms and lower legs, sandals. Neither arm in the right column wears a sleeve or cuff; both exposed arms must use the reference's warm skin colors and purple shadow outline. No shorts, skirt, boots, stockings or invented accessories. Copy the outfit identity, not the reference pose.
Replace Image1's red hair ribbon with small GOLD SUNGLASSES resting on the crown at each pose's correct angle. Preserve the new target's layered lavender hair, distinct braid, ear planes, gold eye and controlled purple outline, using the same detail density as Image2. Both columns must keep IDENTICAL head/face, joints and limbs; garments are the only difference.
Image3 is older Ultimate pose context, only to confirm the actions. Do not copy its flat old hair or simplified clothing, or any erroneous white sleeve on the right. Do not cover the newer detailed target with the old body.
Keep the short purple buster and both hands, not a pistol or bare fist. No added weapon, third hand, projectile or motion effect. Clean logical-pixel clusters, controlled2-3tone shading, no smooth painting, noisy tiny lines, halo, glow, ground shadow, grids, labels or text. True transparent background. Preserve all four target positions.'''
    d.mkdir();target.save(d/'edit_target.png');style.save(d/'accepted_style.png');old.save(d/'old_pose_context.png');(d/'prompt.txt').write_text(prompt,'utf8')
    write(d/'input.json',{'refs':[90,91],'forms_by_column':['before','after'],'parent':{'path':p.relative_to(ROOT).as_posix(),'sha256':sha(a.data)},'base_source':{'path':bp.relative_to(ROOT).as_posix(),'sha256':sha(b.data)},'style_source':{'path':'ultimate_standing_fire_common01/report.json','sha256':sha((H/'ultimate_standing_fire_common01/report.json').read_bytes())},'layout':{'canvas':[1536,1536],'logical_canvas':[192,192],'cell':[96,96],'origin':[48,48],'crop':list(crop)},'policy':'새기본90/91의 각기 다른 수용 포즈를 유지하는 Ultimate의상 신작.89팔만변경한별칭/원US완전복원 주장아님.','files':{q.name:sha(q.read_bytes())for q in d.iterdir()if q.is_file()}})
    print(d)
if __name__=='__main__':main()
