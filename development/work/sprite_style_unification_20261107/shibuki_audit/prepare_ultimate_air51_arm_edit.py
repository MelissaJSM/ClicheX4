"""새 공중51 의상 전후의 반대팔 관절 차이만 교정할 원화 입력."""
from pathlib import Path
import json, sys
H = Path(__file__).resolve().parent
ROOT = H.parents[2]
sys.path.insert(0, str(ROOT))
from PIL import Image, ImageDraw
from native_pose_pack import need, sha, write

def main():
    out = H / 'ultimate_air51_arm_edit01'
    need(not out.exists(), 'Fresh owned output required')
    out.mkdir()
    im = Image.new('RGBA', (1536, 1024))
    sources = []
    for col, form in enumerate(('before', 'after')):
        src = H / f'ultimate_air_contacts02/{form}_051.png'
        pose = Image.open(src).convert('RGBA')
        im.alpha_composite(pose.crop((128, 124, 192, 188)).resize((768, 768), Image.Resampling.NEAREST), (768 * col, 128))
        sources.append({'form': form, 'path': src.relative_to(ROOT).as_posix(), 'sha256': sha(src.read_bytes())})
    im.save(out / 'edit_target.png')
    guide = Image.new('RGB', im.size, (25, 31, 43))
    guide.paste(im, (0, 0), im)
    d = ImageDraw.Draw(guide)
    # Native world targets describe anatomy, not a position inferred from bbox.
    for col in range(2):
        ox, oy = 384 + 768 * col, 560
        d.rectangle((ox - 12, oy + 24, ox + 36, oy + 72), outline=(70, 240, 180), width=3)
        d.line((ox - 36, oy + 48, ox + 72, oy + 48), fill=(70, 240, 180), width=2)
    guide.save(out / 'fist_position_guide.png')
    prompt = '''Use case: precise-object-edit. Edit only the right-hand sprite's bare arm on the IMAGE-RIGHT side in edit_target.png. The left sprite is the exact corresponding pose in a jacket: preserve it unchanged as the joint-position reference. The two sprites are the SAME compact Tenko Shibuki in exactly the same airborne posture; only their clothing differs.
The right sprite currently drops its image-right forearm and fist too low/outward. Bend that bare elbow naturally and bring the small closed fist UP and IN toward the right edge of her chest, matching the image-right cuff/fist center of the LEFT jacket sprite. Its native target fist is around world x0..2,y2..5; the current wrong fist is x4..6,y6..8. The optional green guide is anatomy reference only, never draw guides into the result. Keep the shoulder attached at its existing position and form one short continuous upper arm, elbow, forearm and fist; exactly TWO arms total. Keep her other image-left raised fist completely unchanged. Do not add sleeve fabric, a glove, third hand or a second forearm.
Transparent1536x1024 canvas. Two768x768 viewports start at (0,128) and(768,128); fixed12x native enlargement with origins(384,560) and(1152,560). Keep the two bodies at EXACT existing scale and coordinates. Do not resize or move any complete sprite. Preserve the entire hair/ears, gold heart sunglasses, face/eyes, navy flower, neck, sailor swimsuit, navy/gold collar, skirt, thighs, knees, sandals and all other contours. Preserve the accepted compact detailed pixel-cluster style, crisp dark outline and2~3 coherent skin tones. Change ONLY the right sprite's image-right bare arm and the few adjacent pixels uncovered by bending it. Do not paint flat flesh over hair, erase existing hairstyle, lengthen the torso/legs or copy the jacket sleeve onto the swimsuit. No labels, boxes, guide marks, background or shadows. Output both sprites, with the LEFT reference unchanged.'''
    (out / 'prompt.txt').write_text(prompt + '\n', encoding='utf8')
    write(out / 'input.json', {'sources': sources, 'ref': 51, 'target_form': 'after', 'native_fixed_scale': 1 / 12, 'source_size': [1536, 1024], 'native_origin': [160, 160], 'viewports': [[0, 128, 768, 896], [768, 128, 1536, 896]], 'world_crop': [-32, -36, 32, 28], 'new_art_only': True, 'reference_fist_world': [0, 2, 2, 5], 'old_after_fist_world': [4, 6, 6, 8], 'no_resource_written': True})
    print(out)

if __name__ == '__main__':
    main()
