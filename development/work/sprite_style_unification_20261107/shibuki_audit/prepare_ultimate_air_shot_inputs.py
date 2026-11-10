"""새 공중11몸체와 수용34 총열의 실제 픽셀로 앞팔 편집 입력을 만든다."""
from pathlib import Path
import json, sys
H = Path(__file__).resolve().parent
ROOT = H.parents[2]
sys.path.insert(0, str(ROOT))
import numpy as np
from PIL import Image, ImageDraw
from scripts.export_x_consistency import Archive, page
from native_pose_pack import need, sha, write
from prepare_air_body_layers import ownership

PARENT_SHA = 'd636032c2ace44e66f5f6303c62315ad4335b9d2bf46b0eff61c3cf1bf94a39d'
GROUPS = ((33, 35, 37), (39, 41, 43), (45, 47, 49), (51, 53))
SHOULDERS = {33: (-5, -4), 35: (-5, -4), 37: (-6, -6), 39: (-3, -5), 41: (-3, -5), 43: (-4, -4), 45: (-5, -4), 47: (-5, -4), 49: (-5, -4), 51: (-5, 0), 53: (-5, -1)}

def shift(v, dx, dy):
    result = np.zeros_like(v)
    y, x = np.nonzero(v)
    result[y + dy, x + dx] = v[y, x]
    return result

def exact_masked(a, rgba, pal, mask):
    colors = np.array(a.rgba(np.arange(16, dtype=np.uint8).reshape(1, 16), pal)).reshape(16, 4)
    pixels = np.array(rgba)
    result = np.zeros(mask.shape, np.uint8)
    seen = np.zeros(mask.shape, bool)
    for i, color in enumerate(colors):
        selected = np.all(pixels == color, axis=2) & mask
        result[selected] = i
        seen |= selected
    need(np.all(seen[mask]), 'Original casing not in form palette')
    return result

def main():
    out = H / 'ultimate_air_shot_inputs01'
    need(not out.exists(), 'Fresh output required')
    a = Archive((H / 'prepared_rising_right_ultimate01/PL02_U.ARC').read_bytes())
    need(sha(a.data) == PARENT_SHA, 'Parent changed')
    out.mkdir()
    bodies = out / 'bodies'
    bodies.mkdir()
    barrel_dir = out / 'barrels'
    barrel_dir.mkdir()
    master_mask_path = H / 'air_barrel_guard02/master_034_mask.png'
    master_mask = np.array(Image.open(master_mask_path)) > 0
    master = exact_masked(a, a.composite(34, 0)[0], 0, master_mask)
    need(set(np.unique(master)) == {0, 2, 5, 8, 14, 15}, 'Casing includes skin or sleeve')
    need(np.count_nonzero(master) == 60, 'Master casing size changed')
    need(np.array_equal(np.array(a.rgba(master, 0)), np.array(a.rgba(master, 16))), 'Gun palette differs between costumes')
    Image.fromarray(master).save(barrel_dir / 'master_indices.png')
    Image.fromarray(master_mask.astype(np.uint8) * 255).save(barrel_dir / 'master_mask.png')
    info = json.loads((H / 'ultimate_air_inputs01/manifest.json').read_text('utf8'))
    pairs = {r['body']: r for r in info['pairs']}
    records = []
    body_records = []
    barrels = {}
    barrel_pics = []
    for n in range(33, 55, 2):
        mx, my = map(int, pairs[n]['original_muzzle_world'])
        dx, dy = mx + 24, my + 10
        gun = shift(master, dx, dy)
        guard = shift(master_mask.astype(np.uint8), dx, dy).astype(bool)
        Image.fromarray(gun).save(barrel_dir / f'{n + 1:03}_indices.png')
        Image.fromarray(guard.astype(np.uint8) * 255).save(barrel_dir / f'{n + 1:03}_mask.png')
        barrels[n] = (gun, guard)
        for form, mask, pal in [('before', 15, 16), ('after', 0, 0)]:
            src = H / ('ultimate_air51_arm_registered01/after_051_indices.png' if form == 'after' and n == 51 else f'ultimate_air_contacts02/{form}_{n:03}_indices.png')
            v = np.array(Image.open(src))
            Image.fromarray(v).save(bodies / f'{form}_{n:03}_indices.png')
            a.rgba(v, pal).save(bodies / f'{form}_{n:03}.png')
            body_records.append({'form': form, 'body_ref': n, 'source': src.relative_to(ROOT).as_posix(), 'source_sha256': sha(src.read_bytes()), 'index_sha256': sha(v.tobytes()), 'source_pixels_exact': True})
            actual = np.array(a.composite(n + 1, mask)[0])
            expected = np.array(a.rgba(gun, pal))
            diff = guard & np.any(actual != expected, axis=2)
            raw = np.zeros_like(actual)
            raw[guard] = actual[guard]
            barrel_pics.extend([(f'{form} {n + 1} old casing only', Image.fromarray(raw)), (f'{form} {n + 1} accepted34 module', a.rgba(gun, pal))])
            records.append({'form': form, 'body_ref': n, 'shot_ref': n + 1, 'muzzle_world': [mx, my], 'module_translation': [dx, dy], 'casing_pixels': int(np.count_nonzero(gun)), 'casing_changed_from_old': int(diff.sum()), 'casing_changed_world': [[int(x - 160), int(y - 160)] for y, x in np.column_stack(np.nonzero(diff))], 'old_nonbody_sleeve_or_skin_not_copied': True})
    for i in range(0, len(barrel_pics), 8):
        page(barrel_pics[i:i + 8], a.composite(0, 0)[0], barrel_dir / f'comparison_{i // 8:02}.png', cols=2, scale=5)
    for pn, refs in enumerate(GROUPS, 1):
        folder = out / f'page{pn:02}'
        folder.mkdir()
        # Last page also stays1536x1024 so the fixed1/8 registration is invariant.
        sheet = Image.new('RGBA', (1536, 1024))
        guide = sheet.copy()
        gd = ImageDraw.Draw(guide)
        for row, (form, mask, pal) in enumerate([('before', 15, 16), ('after', 0, 0)]):
            for col, n in enumerate(refs):
                v = np.array(Image.open(bodies / f'{form}_{n:03}_indices.png'))
                gun, guard = barrels[n]
                target = v.copy()
                target[guard] = gun[guard]
                native = a.rgba(target, pal)
                native.save(folder / f'{form}_{n + 1:03}_edit_target.png')
                cell = native.crop((128, 124, 192, 188)).resize((512, 512), Image.Resampling.NEAREST)
                need(np.count_nonzero(np.array(native)[:, :, 3]) == np.count_nonzero(np.array(native.crop((128, 124, 192, 188)))[:, :, 3]), 'Input cropped body')
                sheet.alpha_composite(cell, (col * 512, row * 512))
                guide.alpha_composite(cell, (col * 512, row * 512))
                mx, my = map(int, pairs[n]['original_muzzle_world'])
                sx, sy = SHOULDERS[n]
                points = [(mx + 8, my - 4), (sx + 2, sy - 4), (sx + 3, sy + 6), (mx + 8, my + 6)]
                gd.line([(col * 512 + (x + 32) * 8, row * 512 + (y + 36) * 8) for x, y in points + [points[0]]], fill=(0, 255, 128, 230), width=3)
                yy, xx = np.nonzero(ownership(n) == 7)
                box = [int(xx.min()) - 160, int(yy.min()) - 160, int(xx.max()) - 160, int(yy.max()) - 160]
                gd.rectangle((col * 512 + (box[0] + 32) * 8, row * 512 + (box[1] + 36) * 8, col * 512 + (box[2] + 32) * 8, row * 512 + (box[3] + 36) * 8), outline=(255, 170, 0, 230), width=2)
        sheet.save(folder / 'edit_target.png')
        guide.save(folder / 'arm_guide.png')
        prompt = f'''Use case: precise-object-edit. Edit only the shooting foreground arm of the {len(refs) * 2} compact pixel sprites in image1. Image1 is the authoritative exact new body, face, hair, outfit and rear hand. Image2 green/ orange lines are only arm-position guides, NEVER artwork. Transparent1536x1024 canvas, three512x512 cells across/two rows, fixed8x native64x64 windows with origins32,36. Columns correspond to body refs{refs}; keep any empty third column transparent.
Top row: Tenko Shibuki in accepted short white/navy jacket with gold trim. Bottom row: identical joints and body in sleeveless white sailor swim-dress, BARE ARMS. Preserve the newly detailed lavender fox ears/hair, gold heart sunglasses, navy flower, face/eyes, collar, torso/hem, rear arm/hand, knees and sandals at EXACT coordinates. Do not rescale or reposition a whole sprite.
Replace the original bent/raised FOREGROUND arm (the one on image-LEFT, indicated by orange guide) with a natural short LEFT-firing arm. The lavender compact original buster at far LEFT is already at the exact game muzzle position: preserve every gun pixel, size, silhouette and angle. Join that gun to the existing shoulder with a properly bent short upper arm, elbow and forearm. REMOVE the previous bent foreground fist while creating this firing arm. The OTHER image-right/rear arm stays exactly in its original pose. Exactly TWO arms/hands in each result, never an extra hand beside the face or above the head. For overhead poses, only lower the foreground arm; keep the other overhead hand unchanged. Fill the legitimately uncovered area with the existing hair or outfit texture, not a flat flesh patch.
Top shooting sleeves retain the jacket's short loose volume, folded white/light-lavender fabric, navy cuff and gold edge. Bottom has bare skin along the SAME centerline, no old white cuffs or sleeve remnants. Do not stretch a rectangular sleeve, make a long sausage arm, erase neck/hair detail, paste a coarse old head, widen the torso or move feet. Detailed crisp pixel clusters matching the input, coherent2~3 skin/fabric tones, dark clean outline. No guides, letters, background, wall, floor, glow, shadow or new pose. This is ONLY a foreground firing-arm edit.'''
        (folder / 'prompt.txt').write_text(prompt + '\n', encoding='utf8')
    write(out / 'manifest.json', {'parent_sha256': PARENT_SHA, 'bodies': body_records, 'barrels': records, 'master_barrel': {'source_ref': 34, 'source_form': 'after', 'native_indices_sha256': sha(master.tobytes()), 'master_mask_source': master_mask_path.relative_to(ROOT).as_posix(), 'master_mask_source_sha256': sha(master_mask_path.read_bytes()), 'opaque_pixels': 60, 'skin_or_sleeve_pixels': 0, 'same_rgba_in_both_palettes': True}, 'page_body_refs': [list(g) for g in GROUPS], 'new_shots_generated': False, 'candidate_only': True, 'resource_written': False, 'muzzle_coordinates_unchanged': True, 'module_reuse_changes_old_misshapen_casing': True})
    print(json.dumps({'body_displays': len(body_records), 'shot_pages': len(GROUPS), 'barrel_changes': [(r['form'], r['shot_ref'], r['casing_changed_from_old']) for r in records]}))

if __name__ == '__main__':
    main()
