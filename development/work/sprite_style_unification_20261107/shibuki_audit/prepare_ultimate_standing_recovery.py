"""새 기본86/87/92의 서로 다른 자세를 위한 Ultimate 의상 6셀 입력."""
from pathlib import Path
import sys
from PIL import Image
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
from scripts.export_x_consistency import Archive

def main():
    d=H/'ultimate_standing_recovery_inputs01';need(not d.exists(),'새 입력 폴더 필요')
    p=H/'prepared_standing_special_ultimate01/PL02_U.ARC'
    bp=H/'prepared_standing_fire_base01/PL00_U.ARC'
    a=Archive(p.read_bytes());b=Archive(bp.read_bytes())
    need(sha(a.data)=='26fd4c46813775ae7a2210b463725952abbabc5f3c172eafb7b5533f994168ce','Ultimate 부모 변경')
    need(sha(b.data)=='4fe7173665d2bd2e5484a8c62eeb17d286ee61b781abf78e9525e03acb5f8175','기본 신작 변경')
    target=Image.new('RGBA',(1536,1536));style=Image.new('RGBA',target.size);old=Image.new('RGBA',target.size)
    crop=(112,128,208,192)
    for row,n in enumerate((86,87,92)):
        for col,(form,mask) in enumerate((('before',15),('after',0))):
            pos=(col*768,row*512)
            target.alpha_composite(b.composite(n,0)[0].crop(crop).resize((768,512),Image.Resampling.NEAREST),pos)
            if row==0: ref=a.composite(0,mask)[0]
            elif row==1: ref=Image.open(H/f'ultimate_standing_fire_common01/{form}_085.png').convert('RGBA')
            else: ref=Image.open(H/f'ultimate_standing_followthrough_common03/{form}_091.png').convert('RGBA')
            style.alpha_composite(ref.crop(crop).resize((768,512),Image.Resampling.NEAREST),pos)
            old.alpha_composite(a.composite(n,mask)[0].crop(crop).resize((768,512),Image.Resampling.NEAREST),pos)
    prompt='''Use case: identity-preserve. Asset: exact-position console pixel character sprites.
Image1 is the EDIT TARGET: one transparent1536x1536 page with EXACTLY2columns and3rows. Each768x512 cell represents96x64 logical pixels at8x, origin at logical(48,32). Preserve the whole page, all six positions, exact sprite scale, head and limb coordinates and large blank margins. Do not crop, center, fill cells or stretch bodies.
Top row86: short purple buster aimed horizontally left near the face, elbow folded down, distinct recoil pose. Middle row87: bent front forearm remains raised beside the face, with the short buster angled up-left as shown, in a distinct recovery stance. Bottom row92: front arm lowered toward the chest, a separate recovery pose with different arms and feet. Reproduce each target body separately:87 and92 are NOT the idle pose or copies of each other. Preserve exact muzzle direction/position, wrist and elbow bends, lowered other hand, torso angle, head tilt/gaze, knee bends, ankles and sole heights. Exactly two arms and two hands per character. Keep the accepted compact softly rounded proportions, ear-inclusive head about38percent of full height and short torso/limbs. No taller legs or thinner body.
Image2 is the costume and detail reference: LEFT column is jacket-on, RIGHT is jacket-off. Upper row shows actual accepted idle; lower rows show current detailed shooting poses. Change only the target costume/identity details to this reference while preserving all target joints. LEFT wears a pale lavender-white cropped jacket with dark navy collar/cuff shading, visible zipper and fabric folds over the lavender one-piece outfit, narrow pink center accent, bare lower legs and sandals. RIGHT wears that same lavender one-piece, bare shoulders and both bare arms, bare legs and sandals. Every right-column arm, including the front forearm and wrist beneath the purple buster, must have warm skin with purple shadow edges: no white sleeve, cuff or glove. Do not invent shorts, skirt, stockings or boots.
Replace each red hair ribbon with small GOLD SUNGLASSES resting on the crown at the matching head angle. Preserve the detailed lavender hair locks and braid, clear fox-ear planes, small gold eye and controlled purple outline. Use the reference's restrained2-3tone pixel shading. The two costumes share identical head/face and hand/foot coordinates. Garments are the only difference.
Image3 is older Ultimate pose context only. Do not paste its old simple head/body or erroneous white sleeve onto the newly detailed target. Keep the short purple buster, never a pistol, added fist or extra hand. No projectile, effect, halo, glow, cast shadow, labels, grid or text. True transparent background. Keep every pixel sprite in its original target cell position.'''
    d.mkdir();target.save(d/'edit_target.png');style.save(d/'accepted_style.png');old.save(d/'old_pose_context.png')
    (d/'prompt.txt').write_text(prompt,'utf8')
    write(d/'input.json',{'refs':[86,87,92],'forms_by_column':['before','after'],'parent':{'path':p.relative_to(ROOT).as_posix(),'sha256':sha(a.data)},'base_source':{'path':bp.relative_to(ROOT).as_posix(),'sha256':sha(b.data)},'style_sources':{str(n):sha((H/f'{q}/report.json').read_bytes()) for n,q in [(85,'ultimate_standing_fire_common01'),(91,'ultimate_standing_followthrough_common03')]},'layout':{'canvas':[1536,1536],'grid':[2,3],'logical_canvas':[192,192],'cell':[96,64],'origin':[48,32],'crop':list(crop)},'policy':'기본형 신작86/87/92의 독립 자세에 Ultimate 의상 적용.87/92를 대기 별칭으로 취급하지 않음.','files':{q.name:sha(q.read_bytes()) for q in d.iterdir() if q.is_file()}})
    print(d)
if __name__=='__main__':main()
