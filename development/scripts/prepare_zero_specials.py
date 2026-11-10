"""확인된 미국판 애니메이션에서 특수 동작의 원본 참조·공유·작업 시트를 추출한다."""
import argparse
import json
from pathlib import Path
import struct
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.repack_zero import read_inputs
from scripts.discover_inputs import sha256
from scripts.project import new_run, write_json
from scripts.extract_zero import save_image
from src.psx_player import graphics_bank, composition_frame, decode_stream, compose_indices
from src.psx_frame_edit import frame_coverage

# Names are working labels tied to local decomp function evidence, not new game slots.
GROUPS = [
    ('wall_saber', [94], [118]),
    ('raijingeki', [95, 96], [119, 120]),
    ('hyouretsuzan', [97, 98], [121]),
    ('double_jump', [99], []),
    ('air_dash', [18, 19], []),
    ('air_spin_saber', [100], [122]),
    ('ryuenjin', [101, 102], [123, 124]),
    ('rakuhouha', [103], []),
    ('shippuuga', [104], [125]),
]


def prepare(extracted, inventory):
    from PIL import Image, ImageDraw
    profile, _, arc, _, gfx, parts, palette = read_inputs(extracted)
    inv = json.loads(inventory.read_text('utf8'))
    if (inv['source_sha256'] != profile['source_sha256'] or
            inv['archive_sha256'] != sha256(arc)):
        raise ValueError('Inventory does not match the supported original')
    out = new_run(ROOT, 'ver_buki_riko', 'special_preparation')
    records = {}; groups = []
    effect_words = struct.unpack_from('<16H', (extracted/'palette_bank.bin').read_bytes(), 3*32)
    for name, bodies, effects in GROUPS:
        keys = {'body': set(), 'effect': set()}
        external_effects = []
        for role, ids in [('body', bodies), ('effect', effects)]:
            for aid in ids:
                a = inv['animations'][aid]
                if role == 'effect' and aid == 121:
                    # US weapon0x21 overrides player_set_animation's resource selection.
                    # Actual RAM compared the complete weapon composition bank to parts6.
                    external_effects.append({'animation':121,'weapon_id':33,'parts_bank':6,
                        'graphics_bank':None,'frames':sorted({s['frame'] for s in a['sequence']}),
                        'texture_source':'separate weapon VRAM; not the player decompression buffer',
                        'runtime_evidence':'work/ver_buki_riko/ice_identification/20261025T104446387845Z/identification.local.json',
                        'effect_image_extracted_by_this_script':False})
                    continue
                for step in a['sequence']:
                    bank, pb, n = a['graphics_bank'], a['parts_bank'], step['frame']
                    key = f'bank{bank}_{n:03d}'
                    keys[role].add(key)
                    if key in records:
                        if records[key]['role'] != role:
                            raise ValueError('Body/effect classification conflict')
                        continue
                    f = graphics_bank(gfx, bank)['frames'][n]
                    c = composition_frame(parts, pb, n)
                    raw = decode_stream(gfx, f['offset'], f['limit'], f['tile_count']*128)
                    pixels, size, bounds, _ = compose_indices(raw.data, f['tile_count'], c)
                    cov, _, _ = frame_coverage(raw.data, f['tile_count'], c)
                    path = out/(key+'.png')
                    save_image(pixels, size, palette if role == 'body' else effect_words, path)
                    records[key] = {'bank': bank, 'parts_bank': pb, 'frame': n, 'role': role,
                        'image': path.name, 'png_sha256': sha256(path.read_bytes()),
                        'indices_sha256': sha256(pixels), 'size': size, 'bounds': bounds,
                        'stream_offset': f['offset'], 'compressed_bytes': raw.end-f['offset'],
                        'parts': c['parts'], 'overlap_pixels': sum(len(set(s)) > 1 for s in cov),
                        'stream_references': inv['stream_sharing'][str(f['offset'])]}
        entry = {'name': name, 'body_animations': bodies, 'effect_animations': effects,
                 'body_keys': sorted(keys['body']), 'effect_keys': sorted(keys['effect']),
                 'external_effect_resources': external_effects,
                 'original_sequences': [inv['animations'][a] for a in bodies+effects],
                 'existing_riko_frames_reusable': name in ('double_jump','air_dash'),
                 'new_riko_art_produced_by_this_script': False, 'runtime_verified': False}
        groups.append(entry)
        for role in ('body', 'effect'):
            ordered = sorted(keys[role])
            if not ordered:
                continue
            board = Image.new('RGBA', (5*320, ((len(ordered)+4)//5)*300), (32,36,48))
            draw = ImageDraw.Draw(board)
            for i, key in enumerate(ordered):
                r = records[key]; cell = Image.new('RGBA', (160,136))
                cell.alpha_composite(Image.open(out/r['image']).convert('RGBA'),
                                     (88+r['bounds'][0], 72+r['bounds'][1]))
                board.alpha_composite(cell.resize((320,272), Image.Resampling.NEAREST),
                                      (i%5*320, i//5*300+28))
                draw.text((i%5*320+6,i//5*300+6), key, fill='white')
            board.save(out/f'{name}_{role}_original.png')
    write_json(out/'preparation.local.json', {'source_sha256': profile['source_sha256'],
        'archive_sha256': sha256(arc), 'executable_sha256': inv['executable_sha256'],
        'inventory': str(inventory), 'inventory_sha256': sha256(inventory.read_bytes()),
        'groups': groups, 'frames': records, 'new_game_data_written': False,
        'effect_palette_row3_is_preview_only': True,
        'technique_labels_require_function_evidence_in_docs': True})
    print(json.dumps({'output':str(out), 'body_references':sum(r['role']=='body' for r in records.values()),
                      'effect_references':sum(r['role']=='effect' for r in records.values())}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--extract', type=Path, required=True)
    parser.add_argument('--inventory', type=Path, required=True)
    args = parser.parse_args()
    prepare(args.extract.resolve(), args.inventory.resolve())
