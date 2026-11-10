"""사격42/44에 남은 세 번째 팔을 실제 위치로 지정한 국소 편집 입력."""
from pathlib import Path
import sys
H = Path(__file__).resolve().parent
ROOT = H.parents[2]
sys.path.insert(0, str(ROOT))
from PIL import Image, ImageDraw
from native_pose_pack import need, sha, write

def main():
    out = H / 'ultimate_air_shot_extra_arm_edit01'
    need(not out.exists(), 'Fresh input required')
    out.mkdir()
    target = Image.new('RGBA', (1024, 1024))
    rows = []
    boxes = {42: [-19, -30, -9, -13], 44: [-21, -25, -9, -12]}
    for row, form in enumerate(('before', 'after')):
        for col, ref in enumerate((42, 44)):
            src = H / 'ultimate_air_shot_native02' / f'{form}_{ref:03}.png'
            tile = Image.open(src).convert('RGBA').crop((128, 124, 192, 188)).resize((512, 512), Image.Resampling.NEAREST)
            target.alpha_composite(tile, (512 * col, 512 * row))
            rows.append({'form': form, 'ref': ref, 'source': src.relative_to(ROOT).as_posix(), 'sha256': sha(src.read_bytes()), 'extra_arm_world_box': boxes[ref]})
    target.save(out / 'edit_target.png')
    guide = target.copy()
    d = ImageDraw.Draw(guide)
    for row in range(2):
        for col, ref in enumerate((42, 44)):
            x0, y0, x1, y1 = boxes[ref]
            d.rectangle((512 * col + (x0 + 32) * 8, 512 * row + (y0 + 36) * 8, 512 * col + (x1 + 32) * 8, 512 * row + (y1 + 36) * 8), outline=(255, 40, 60, 255), width=4)
    guide.save(out / 'extra_arm_guide.png')
    prompt = '''Use case: precise-object-edit to repair incorrect anatomy. The FOUR sprites in image1 currently each have THREE arms: a leftward firing arm, a raised arm on image-RIGHT, and an erroneous additional raised arm on image-LEFT. REMOVE ONLY THE THIRD ARM ON IMAGE-LEFT. Image2 RED BOXES mark this exact wrong extra hand/forearm. Its peach fingers and sleeve/skin are separate from the fox ear. The output must have exactly TWO arms: leftward firing arm plus unchanged IMAGE-RIGHT overhead arm.
Keep the lavender fox EAR and hair behind the removed extra arm: reveal a small natural continuation of existing layered hair wherever needed, and transparent background above it. Do not turn the hand into a skin-colored ear, cover it with solid lavender, add black scratches, or leave a cuff/skin stump. Keep BOTH actual fox ears intact. Do not remove the correct image-right overhead hand. Do not remove or move the already-correct left-firing forearm or its buster.
Transparent1024x1024 canvas: two512x512 cells across, two rows; fixed8x native64x64 viewports with origin(32,36). TOP: short white/navy jacket. BOTTOM: sleeveless white sailor swim-dress with bare arms. Columns are pose42 then44. Keep the entire existing face/eyes/gold sunglasses, main hair and navy flower, head scale, neck, chest, sleeve of the correct remaining arm, waist/hem, curled knees, sandals, body positions and original gun coordinates absolutely unchanged. Only remove the marked extraneous left raised hand/forearm, exposing appropriate tiny hair-edge detail behind it. Crisp pixel clusters at the exact source scale. No redesign, no labels, no red boxes, no glow, no shadows, no background. EXACTLY TWO ARMS PER SPRITE.'''
    (out / 'prompt.txt').write_text(prompt + '\n', encoding='utf8')
    write(out / 'input.json', {'rows': rows, 'fixed_scale': 0.125, 'source_size': [1024, 1024], 'native_crop': [-32, -36, 32, 28], 'previous_generated_sha256': 'e4891163b53c0bd0fd7b12b87f8aff6c44e227e6c7447ea61cdf8da6b9d71fab', 'rejected_refs': [42, 44], 'previous_source40_usable_only_after_separate_review': True, 'three_arm_defect_confirmed_by_actual_image_review': True, 'native_previous_single_component_is_not_art_pass': True, 'no_resource_written': True})
    print(out)

if __name__ == '__main__':
    main()
