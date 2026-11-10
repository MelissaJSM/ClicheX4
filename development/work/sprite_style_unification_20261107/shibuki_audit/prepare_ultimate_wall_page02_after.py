"""후반 벽 세 자세의 새 접점을 보존하는 의상 편집 입력만 만든다."""
from pathlib import Path
import sys
import numpy as np
from PIL import Image

H = Path(__file__).resolve().parent
ROOT = H.parents[2]
sys.path.insert(0, str(ROOT))
from native_pose_pack import need, sha, write
from scripts.export_x_consistency import Archive

I = H / 'ultimate_wall_raised_native01'
O = H / 'ultimate_wall_page02_after01'

def main():
    need(not O.exists(), 'Fresh output required')
    a = Archive((H/'prepared_ultimate_lowhp01/PL02_U.ARC').read_bytes())
    target = Image.open(I/'after_edit_target.png').convert('RGBA')
    need(target.size == (1536,512), 'Unexpected source geometry')
    O.mkdir()
    target.save(O/'edit_target.png')
    guide = Image.new('RGBA', target.size)
    style = Image.new('RGBA', (1536,512))
    rows = []
    for i,n in enumerate((61,63,65)):
        q = np.array(Image.open(I/f'{n:03}_indices.png'))
        hm = np.array(Image.open(I/f'{n:03}_head_mask.png')) > 0
        hand = np.array(Image.open(I/f'{n:03}_hand_mask.png')) > 0
        mask = hm | hand
        mask[167:] = True
        locked = np.where(mask,q,0).astype(np.uint8)
        guide.alpha_composite(a.rgba(locked,16).crop((128,120,192,184)).resize((512,512),Image.Resampling.NEAREST),(i*512,0))
        m = (55,57,59)[i]
        im = Image.open(H/'ultimate_wall_contacts_probe01/after'/f'{m:03}.png').convert('RGBA')
        style.alpha_composite(im.crop((128,120,192,184)).resize((512,512),Image.Resampling.NEAREST),(i*512,0))
        rows.append({'ref':n,'source_indices':str((I/f'{n:03}_indices.png').relative_to(ROOT)),'source_sha256':sha((I/f'{n:03}_indices.png').read_bytes()),'guide_only':True})
    guide.save(O/'locked_head_hand_legs.png')
    style.save(O/'costume_reference.png')
    prompt = '''Use case: identity-preserve, precise clothing edit for a PS1-style game sprite.
Image 1 edit_target.png is the exact target: three compact Tenko Shibuki sprites at native64x64 per512x512 cell, transparent1536x512 plate. Image 2 marks the exact head, raised palm and lower legs that MUST stay fixed. Image 3 is the accepted sleeveless ONE-PIECE costume reference, not a pose reference.

Edit only the WHITE/NAVY OUTER JACKET AND SLEEVES of image1 into the same character's sleeveless sailor swim-dress. Preserve all three original poses, the EXACT head scale and position, face, hair locks, gold heart sunglasses, ears, navy flower accessory, neck socket, curled knees, sandal soles, waist and both hand contact positions. Each raised arm must remain bent in its own existing geometry with its raised hand at EXACTLY the present height and horizontal position. The hand and head must not drift or get bigger. The figure is compact and short as the target, not taller or thinner.

Remove the long white jacket sleeves and cuffs to expose natural bare arms, maintaining their centerline and joint positions. Bare upper arms and forearms must connect naturally from the SAME shoulder to the SAME palm; do not use thin elongated arms, disconnected wrists or displaced elbows. Replace only the torso's open jacket with a covered white/light-lavender connected ONE-PIECE sailor swim-dress: navy sailor collar, pink neck ribbon, a few clear bodice folds, a short flared skirt hem, no exposed midriff, no bikini, no shorts. The original jacket is the maximum outer silhouette: the new garment and bare arms fit inside it. Keep the detailed modernized game-pixel clusters from the target; no simplified solid hair blobs and no noisy black scratches.

Output only these three complete AFTER sprites, exact same canvas, source positions and native-scale pixel-grid clusters, on true transparent background. No text, grid, floor, wall, shadow, labels, extra examples or extra poses.'''
    (O/'prompt.txt').write_text(prompt+'\n',encoding='utf8')
    write(O/'inputs.json',{'kind':'후반 벽 3자세 재킷 제거 편집','refs':rows,'source_registration':str((I/'registration.json').relative_to(ROOT)),'sources':{p.name:sha(p.read_bytes())for p in O.glob('*.png')},'generated':False,'packed':False,'game_written':False,'locked_guide_is_not_packing_mask':True})
    print(str(O))

if __name__ == '__main__':
    main()
