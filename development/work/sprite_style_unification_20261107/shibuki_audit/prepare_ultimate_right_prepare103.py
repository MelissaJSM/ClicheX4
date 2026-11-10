"""103 새 오른손 준비 포즈를 그대로 사용해 Ultimate 의상 편집 입력을 만든다."""
from pathlib import Path
import sys
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from PIL import Image
from scripts.export_x_consistency import Archive
from native_pose_pack import need,sha,write
def main():
    out=H/'rising_ultimate_prepare103';need(not out.exists(),'New input only');out.mkdir()
    a=Archive((H/'prepared_rising_fire_ultimate01/PL02_U.ARC').read_bytes());source=H/'rising_right_hand_native04/base_103.png'
    im=Image.open(source).convert('RGBA').crop((128,124,192,188)).resize((768,768),Image.Resampling.NEAREST)
    target=Image.new('RGBA',(1536,1024));idle=Image.new('RGBA',target.size);nextpose=Image.new('RGBA',target.size)
    for col,mask in enumerate((15,0)):
        target.alpha_composite(im,(col*768,128));idle.alpha_composite(a.composite(0,mask)[0].crop((128,124,192,188)).resize((768,768),Image.Resampling.NEAREST),(col*768,128))
        nxt=Image.open(H/'rising_ultimate_right_native02'/f'{"before"if col==0 else"after"}_104.png').convert('RGBA')
        nextpose.alpha_composite(nxt.crop((128,124,192,188)).resize((768,768),Image.Resampling.NEAREST),(col*768,128))
    target.save(out/'right_prepare_pose.png');idle.save(out/'ultimate_costumes.png');nextpose.save(out/'next104_style_only.png')
    prompt='''Use case: identity-preserve. Costume-only edit of the TWO custom game sprites in image 1. Preserve image 1 pose and pixel positions exactly. Image 2 is accepted Ultimate clothing/accessory reference. Image 3 is the NEXT animation frame for matching clothing and hair detail only; do not copy its high punch pose.
The pose in image 1 is a preparation before the upward punch: face looks LEFT, RIGHT-SIDE fist is bent beside the RIGHT cheek/neck at about canvas(450,520), second copy(1218,520). LEFT-SIDE hand stays low near the LEFT chest. Keep exactly these two hands and the original bent elbows. Neither fist is above the ears yet. No extra hand, no mirrored figure, no high vertical arm, no tall limbs.
LEFT character wears white/navy short sailor jacket with gold piping and full WHITE SLEEVES as in image 2 left and image 3 left. RIGHT character wears the same sailor swimsuit without the outer jacket, completely BARE ARMS, no cuff, sleeve, wristband or bracelet, as in image 2 right and image 3 right. Bare thighs and white/pink sandals for both. Replace red shrine flower with navy flower; add small golden HEART sunglasses perched above eyes. Preserve original lavender layered hair, ear outline, face direction and knee/foot positions; add the detailed hair strands and fine costume folds consistent with image 3. Exactly same head, hair, face, legs, hands and sandals between both costume variants. Only jacket coverage differs.
Native 64x64 sprites at12x, viewports(0,128)-(768,896),(768,128)-(1536,896), origins(384,560),(1152,560). Transparent1536x1024canvas, no pose translation/scaling/stretching. Keep short compact accepted proportions. Preserve limb joints and sole registration. No weapon/fire/effect/background/labels/text/guide. Clean opaque sprite pixels on genuinely transparent background. Costume-only edit of image1, no copying the raised arm from image3.'''
    (out/'prompt.txt').write_text(prompt,'utf8');write(out/'manifest.json',{'ref':103,'source_pose_sha256':sha(source.read_bytes()),'forms':['ultimate_before','ultimate_after'],'fixed_scale':1/12,'high_punch_pose_reference_role':'style only, not geometry','parent_sha256':sha(a.data)});print(out)
if __name__=='__main__':main()
