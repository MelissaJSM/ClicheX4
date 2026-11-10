"""원US 높이로 교정된 새104 네이티브 포즈를 의상 편집 입력으로 구성한다."""
from pathlib import Path
import sys
H=Path(__file__).resolve().parent; ROOT=H.parents[2]; sys.path.insert(0,str(ROOT))
from PIL import Image
from scripts.export_x_consistency import Archive
from native_pose_pack import need,sha,write

def main():
    out=H/'rising_ultimate_right_retry02'; need(not out.exists(),'New retry only'); out.mkdir()
    a=Archive((H/'prepared_rising_fire_ultimate01/PL02_U.ARC').read_bytes())
    need(sha(a.data)=='71d02fe6d965c1fb42cc786766bad62372c792ccd8ecf6d5bc1e40dc8deb8597','Wrong parent')
    source=H/'rising_right_hand_native04/base_104.png'
    im=Image.open(source).convert('RGBA').crop((128,124,192,188)).resize((768,768),Image.Resampling.NEAREST)
    target=Image.new('RGBA',(1536,1024)); idle=Image.new('RGBA',target.size)
    for col,mask in enumerate((15,0)):
        target.alpha_composite(im,(col*768,128))
        idle.alpha_composite(a.composite(0,mask)[0].crop((128,124,192,188)).resize((768,768),Image.Resampling.NEAREST),(col*768,128))
    target.save(out/'right_hand_pose.png'); idle.save(out/'ultimate_costumes.png')
    prompt='''Use case: identity-preserve. COSTUME-ONLY EDIT of image 1, a transparent game sprite sheet. Image 1 is the exact pose and coordinate target. Image 2 is costume and character-accessory reference ONLY. Output two detailed pixel-art sprites on a transparent 1536x1024 canvas, in exactly the same positions as image 1.
DO NOT CHANGE THE POSE. The high fist is already correctly placed ABOVE THE RIGHT EAR of each sprite, on the IMAGE-RIGHT side. The face looks left, and the other fist stays low at the LEFT chest. Exactly two hands. Do not mirror, switch arms, move the high fist, lower the fist, or copy the standing pose from image 2. The high fist stays centered at approximately canvas (444,224) and (1212,224). The sole, knee, hips, shoulders, head, ears, face direction and short compact body proportions are fixed by image 1.
Change red shrine clothing into the Ultimate costumes shown in image 2: LEFT sprite has the white/navy short sailor jacket with gold piping and WHITE LONG SLEEVES. RIGHT sprite has the sailor swimsuit underlayer WITHOUT the jacket, with completely BARE ARMS and bare legs. On the right there must be no cuff, sleeve, wristband or bracelet. Both variants share identical new lavender layered hair, ears, face, eyes, bare thighs, knees and small white/pink sandals. Replace the red flower with the navy flower and small gold HEART sunglasses as shown in image 2. Keep the existing hair and ear silhouette and face direction. Use fine but clear limited-palette hair strands, collar, folds, gold trim and crisp contour at the same native pixel scale. Do not add extra accessories.
Input 1 has two 64x64 native viewports enlarged 12x, occupying (0,128)-(768,896) and (768,128)-(1536,896). Origins (384,560), (1152,560). Preserve fixed registration; do not enlarge, shrink, translate or stretch the body. Preserve all joint positions while changing costume details. No flame, gun, extra limbs, text, labels, guides, checkerboard or background. Genuine transparent background with opaque sprite pixels. The high RIGHT-SIDE fist and low LEFT-SIDE guarding fist remain exactly where they are in image 1. This is an outfit-only edit, not a new pose.'''
    (out/'prompt.txt').write_text(prompt,'utf8')
    write(out/'manifest.json',{'ref':104,'source_correct_pose_sha256':sha(source.read_bytes()),'parent_sha256':sha(a.data),'forms':['ultimate_before','ultimate_after'],'viewports':[[0,128,768,896],[768,128,1536,896]],'fixed_native_scale':1/12,'wrong_old_ultimate_pose_used':False,'source_background':'alpha240 native registration, no opaque background pixels'})
    print(out)
if __name__=='__main__': main()
