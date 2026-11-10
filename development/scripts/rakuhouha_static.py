"""Apply two Rakuhouha visual frames without touching projectiles or parts."""
import json
from pathlib import Path
import struct

from scripts.discover_inputs import psx_arc
from src.psx_player import composition_frame
from src.psx_frame_edit import read_indexed_png
from src.psx_static_effect import compose_static, patch_static, sha256


def apply_static_set(arc, recipe_path, *, project='ver_buki_riko'):
    recipe_path = Path(recipe_path).resolve()
    record = json.loads(recipe_path.read_text('utf8'))
    if record.get('kind') != 'us_rakuhouha_embedded_body_v1' or set(record['frames']) != {'23', '24'}:
        raise ValueError('Unsupported static effect scope')
    entries = psx_arc(arc)
    def entry(kind):
        meta = next(e for e in entries if e['type'] == kind)
        return meta, arc[meta['offset']:meta['offset']+meta['size']]
    meta, texture = entry('0x10206')
    _, parts = entry('0x3')
    _, palette = entry('0x9')
    if sha256(texture) != record['source_texture_sha256'] or sha256(parts) != record['parts_sha256']:
        raise ValueError('Static texture/parts source hash mismatch')
    def read_bound(name, expected):
        path = (recipe_path.parent/name).resolve()
        if not path.is_relative_to(recipe_path.parent) or sha256(path.read_bytes()) != expected:
            raise ValueError('Static asset path/hash mismatch')
        return path
    palette_path = read_bound(record['palette_file'], record['palette_sha256'])
    evidence=(recipe_path.parent/record['palette_evidence_file']).resolve()
    if project not in ('ver_buki_riko','ver_rin_nana'):raise ValueError('Unsupported static project')
    work_root=Path(__file__).resolve().parents[1]/'work'/project
    if not evidence.is_relative_to(work_root) or sha256(evidence.read_bytes())!=record['palette_evidence_sha256']:
        raise ValueError('Runtime static CLUT evidence mismatch')
    if palette_path.read_bytes()!=evidence.read_bytes()[480*2048+96:480*2048+128]:
        raise ValueError('Static preview palette differs from captured CLUT 0x7803')
    words = struct.unpack('<16H', palette_path.read_bytes())
    frames, compositions = {}, {}
    for key, item in record['frames'].items():
        n = int(key)
        frames[n] = read_indexed_png(read_bound(item['file'], item['sha256']), words)
        compositions[n] = composition_frame(parts, 6, n)
    changed = patch_static(texture, compositions, frames)
    if sha256(changed) != record['modified_texture_sha256']:
        raise ValueError('Static reconstruction hash mismatch')
    references = []
    for bank in (1, 2, 3, 4, 6):
        for n in range(composition_frame(parts, bank, 0)['bank_frame_count']):
            comp = composition_frame(parts, bank, n)
            # Other static banks can use additional CLUTs; tile bytes still must be unchanged.
            tiles = {p['page']*256+p['tile'] for p in comp['parts']}
            altered = any(texture[(t//16*16+y)*128+t%16*8:(t//16*16+y)*128+t%16*8+8]
                          != changed[(t//16*16+y)*128+t%16*8:(t//16*16+y)*128+t%16*8+8]
                          for t in tiles for y in range(16))
            if altered:
                references.append([bank, n])
    if references != [[6, 23], [6, 24]]:
        raise ValueError('Static edits affect other composition references')
    lo = meta['offset']
    candidate = arc[:lo] + changed + arc[lo+len(texture):]
    runs = []
    for i, (old, new) in enumerate(zip(texture, changed)):
        if old == new:
            continue
        pos = lo+i
        if runs and runs[-1][1] == pos:
            runs[-1][1] += 1
        else:
            runs.append([pos, pos+1])
    report = {'recipe': str(recipe_path), 'recipe_sha256': sha256(recipe_path.read_bytes()),
              'texture_sha256': sha256(changed), 'changed_references': references,
              'changed_bytes': sum(a != b for a, b in zip(texture, changed)),
              'allowed_archive_ranges': runs, 'parts_palette_unchanged': True,
              'projectiles_27_72_unchanged': True}
    return candidate, report
