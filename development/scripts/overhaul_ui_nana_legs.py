"""C-04: repair the run shoe-color dilation while preserving indexed geometry."""
import argparse
import json
import struct
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.overhaul_ui_inventory import BUILDS, D, load
from scripts.overhaul_ui_fixes import require
from scripts.prepare_riko_ui import entry, replace_entry
from scripts.overhaul_sprites_audit import render, rgba
from scripts.discover_inputs import sha256
from src.psx_player import graphics_bank, decode_stream, composition_frame, bank_offsets
from src.psx_compress import encode_stream, replace_stream
from src.psx_sprite_batch import pack_original_layout
from src.psx_ui_atlas import local_composition
from src.psx_bank_repack import repack_graphics_bank

# Retain only the two short shoe caps, independently registered for each pose.
# Coordinates are native world pixels, exclusive right/bottom. No silhouettes
# or palette colors are authored here: only mistaken red calf pixels change.
SHOE_REGIONS = {
    1: [(-6,20,2,23),(8,20,14,23)],
    3: [(-6,20,2,23),(8,20,14,23)],
    5: [(-17,18,-9,22),(21,7,24,15)],
    7: [(-19,19,-11,23),(20,7,23,16)],
    9: [(-14,19,-6,23),(15,17,19,23)],
    11: [(-6,19,4,23),(7,12,10,16)],
    13: [(-9,19,1,23),(7,13,11,18)],
    15: [(-9,18,1,22),(7,12,11,17)],
    17: [(-9,19,1,23),(16,17,21,21)],
    19: [(-16,14,-10,23)],
    21: [(-15,16,-9,24),(21,10,24,15)],
    23: [(-9,20,1,24),(16,18,21,22)],
    25: [(-3,20,6,24),(5,13,9,17)],
    27: [(5,20,13,24),(0,14,4,18)],
    29: [(-5,19,4,23),(12,10,16,16)],
    31: [(-16,18,-7,22),(15,18,20,23)],
}


def corrected_leg(arc, frame):
    a, _ = render(arc, 0, 8, frame)
    y, x = np.indices(a.shape)
    x -= 160
    y -= 160
    ordinary = frame if frame % 2 else frame - 1
    keep = np.zeros_like(a, bool)
    for left, top, right, bottom in SHOE_REGIONS[ordinary]:
        keep |= (x >= left) & (x < right) & (y >= top) & (y < bottom)
    edit = (a == 5) & (y >= 8) & ~keep
    result = a.copy()
    result[edit] = 12
    # Restore the existing one-pixel calf shading rule from the run generator.
    right_edge = (np.roll(a, -1, axis=1) == 1) & (np.roll(a, -2, axis=1) == 0)
    result[edit & right_edge] = 11
    require(np.array_equal(a > 0, result > 0), 'Leg alpha changed')
    require(np.all((a == result) | ((a == 5) & np.isin(result, (11,12)))),
            'Changed a color other than misplaced shoe red')
    yy, xx = np.nonzero(edit)
    return result, {
        'frame': frame, 'ordinary_pose': ordinary,
        'shoe_regions_world_exclusive': SHOE_REGIONS[ordinary],
        'red_calf_pixels_fixed': len(xx),
        'changed_world_xy': [[int(q-160),int(p-160)] for p,q in zip(yy,xx)],
        'silhouette_and_contact_points_exact': True,
        'recolor_only': {'before': 5, 'after': [11,12]},
    }


def full_preview(arc, frame):
    words = struct.unpack_from('<64H', entry(arc,9))
    im = Image.new('RGBA', (384,384))
    for bank in (0,8,5,7,6):
        a,_ = render(arc,0,bank,frame)
        im.alpha_composite(rgba(a, words if bank == 0 else
                               words[32:48] if bank == 7 else words[16:32]))
    return im


def patch(arc, selected):
    g, parts = entry(arc,2), entry(arc,3)
    bank = graphics_bank(g,0,allow_bank_aliases=True)
    groups = {}
    for f in bank['frames']:
        groups.setdefault(f['offset'],[]).append(f['index'])
    targets, metadata = {}, []
    for n in sorted(selected):
        targets[n], proof = corrected_leg(arc,n)
        metadata.append(proof)
    expected = {}
    for start, aliases in groups.items():
        if not set(aliases) & selected:
            continue
        require(set(aliases) <= selected, 'Affected stream has an unselected alias')
        f = bank['frames'][aliases[0]]
        original = decode_stream(g,start,f['limit'],f['tile_count']*128).data
        raw = original
        for n in aliases:
            comp = local_composition(composition_frame(parts,8,n))
            tiles = {p['tile'] for p in comp['parts']}
            for b in (0,5,6,7):
                require(not tiles & {p['tile'] for p in composition_frame(parts,b,n)['parts']},
                        'Leg tile aliases another outfit part')
            raw = pack_original_layout(raw,f['tile_count'],targets[n],comp,tiles,origin=(160,160))
        for n in aliases:
            expected[n] = raw
    replacements = {n:encode_stream(raw) for n,raw in expected.items()}
    in_place = all(len(replacements[n]) <= bank['frames'][n]['limit']-bank['frames'][n]['offset']
                   for n in expected)
    changed = g
    compression = []
    repack = None
    if in_place:
        for start, aliases in groups.items():
            if aliases[0] not in expected:
                continue
            changed, check = replace_stream(changed,bank['frames'][aliases[0]],expected[aliases[0]],
                                            allocated_limit=bank['frames'][aliases[0]]['limit'])
            compression.append(check)
    else:
        changed, repack = repack_graphics_bank(g,0,replacements)
    result = replace_entry(arc,2,changed)
    checked = 0
    protected = 0
    for b in range(len(bank_offsets(g,allow_aliases=True))):
        old_bank = graphics_bank(g,b,allow_bank_aliases=True)
        new_bank = graphics_bank(changed,b,allow_bank_aliases=True)
        for before, after in zip(old_bank['frames'],new_bank['frames']):
            old_raw = decode_stream(g,before['offset'],before['limit'],before['tile_count']*128).data
            new_raw = decode_stream(changed,after['offset'],after['limit'],after['tile_count']*128).data
            wanted = expected.get(before['index'],old_raw) if b == 0 else old_raw
            require(new_raw == wanted, 'Unexpected decoded reference changed')
            checked += 1
            protected += wanted == old_raw
    for n in selected:
        actual,_ = render(result,0,8,n)
        require(np.array_equal(actual,targets[n]), 'Leg layer readback differs')
        for b in (0,5,6,7):
            before,_ = render(arc,0,b,n)
            after,_ = render(result,0,b,n)
            require(np.array_equal(before,after), 'Protected layer changed')
    require(entry(result,3) == parts and entry(result,9) == entry(arc,9),
            'Composition/palette changed')
    return result, {'frames': metadata, 'decoded_references_checked': checked,
                    'decoded_references_identical': protected,
                    'base_head_body_arm_layers_exact': True,
                    'composition_palette_timing_exact': True,
                    'compression': compression, 'repack': repack,
                    'runtime_verified': False}


def prepare(out, pilot):
    out = out.resolve()
    require(out.is_relative_to(D) and not out.exists(), 'Fresh UI work directory required')
    old, records = load('ver_rin_nana')
    before = old['PL00_U.ARC']
    selected = {5,6,29,30} if pilot else set(range(1,33))
    after, checks = patch(before,selected)
    out.mkdir(parents=True)
    path = out / 'PL00_U.ARC'
    path.write_bytes(after)
    proposal = {'project':'ver_rin_nana','baseline':BUILDS['ver_rin_nana'][0],
                'baseline_sha256':BUILDS['ver_rin_nana'][1],
                'files': {'PL00_U.ARC': {'before':sha256(before),'after':sha256(after),
                    'size':len(after),'path':path.relative_to(ROOT).as_posix(),
                    'record':records['PL00_U.ARC'],
                    'changed_bytes':sum(a!=b for a,b in zip(before,after))}},
                'issues':['C-04'],'checks':checks,'runtime_verified':False,'pilot':pilot}
    (out/'proposal.json').write_text(json.dumps(proposal,indent=2)+'\n','utf8')
    show = [5,29] if pilot else list(range(1,33,2))
    items = [('Accepted idle 0',full_preview(before,0))]
    for n in show:
        items += [(f'before {n}',full_preview(before,n)),(f'after {n}',full_preview(after,n))]
    cols = 5 if pilot else 6
    board = Image.new('RGB',(cols*320,((len(items)+cols-1)//cols)*330),'#29374b')
    draw = ImageDraw.Draw(board)
    for i,(title,pic) in enumerate(items):
        x,y = i%cols*320,i//cols*330
        pic = pic.crop((128,132,192,188)).resize((320,280),Image.Resampling.NEAREST)
        board.paste(pic,(x,y+30),pic)
        draw.text((x+5,y+5),title,fill='white')
    board.save(out/'before_after.png')
    print(str(out))


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--pilot',action='store_true')
    a = p.parse_args()
    prepare(a.output,a.pilot)
