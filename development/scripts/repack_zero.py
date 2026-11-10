"""제로 압축 예산 감사 및 팔레트/파츠를 유지한 indexed PNG 재삽입 기술 도구."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import struct
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.discover_inputs import psx_arc, sha256
from scripts.project import load_project, validate_bin, inspect_references, new_run, write_json, working_cue
from scripts.extract_zero import save_image
from src.psx_player import bank_offsets, graphics_bank, decode_stream, composition_frame, compose_indices
from src.psx_compress import encode_stream, replace_stream
from src.psx_frame_edit import frame_coverage, edit_frame_indices, read_indexed_png
from src.psx_disc import write_archive_copy


def read_inputs(extracted):
    extracted = extracted.resolve()
    if not extracted.is_relative_to((ROOT/'work/ver_buki_riko').resolve()):
        raise ValueError('Expected first-project extraction directory')
    profile = json.loads((ROOT/'config/ps1_us_slus00561.json').read_text(encoding='utf-8'))
    project = load_project(ROOT, 'ver_buki_riko')
    inspect_references(ROOT, project)
    validate_bin(ROOT/project['source_bin'], profile['source_sha256'])
    arc = (extracted/'original.arc').read_bytes()
    if sha256(arc) != profile['zero_archive']['sha256']:
        raise ValueError('Unexpected source archive')
    entries = psx_arc(arc)
    def entry(kind):
        values = [e for e in entries if e['type'] == hex(kind)]
        if len(values) != 1:
            raise ValueError('Ambiguous archive entry')
        e = values[0]
        return e, arc[e['offset']:e['offset']+e['size']]
    gfx_meta, gfx = entry(2)
    _, parts = entry(3)
    _, palettes = entry(9)
    return profile, project, arc, gfx_meta, gfx, parts, struct.unpack_from('<16H', palettes)


def audit(extracted):
    profile, _, arc, _, gfx, parts, palette = read_inputs(extracted)
    unique = {}
    for bank in range(len(bank_offsets(gfx))):
        for f in graphics_bank(gfx, bank)['frames']:
            key = (f['offset'], f['tile_count'])
            if key not in unique:
                original = decode_stream(gfx, f['offset'], f['limit'], f['tile_count']*128)
                encoded = encode_stream(original.data)
                check = decode_stream(encoded, 0, len(encoded), len(original.data))
                if check.data != original.data:
                    raise AssertionError('Recompression pixel mismatch')
                unique[key] = {'offset': f['offset'], 'tile_count': f['tile_count'],
                               'original_bytes': original.end-original.start, 'encoded_bytes': len(encoded),
                               'fits_original_stream': len(encoded) <= original.end-original.start,
                               'decoded_sha256': sha256(original.data), 'references': []}
            unique[key]['references'].append([bank, f['index']])
    frame = 147
    target = graphics_bank(gfx, 0)['frames'][frame]
    original = decode_stream(gfx, target['offset'], target['limit'], target['tile_count']*128)
    comp = composition_frame(parts, 0, frame)
    indices, size, bounds, _ = compose_indices(original.data, target['tile_count'], comp)
    if edit_frame_indices(original.data, target['tile_count'], comp, indices, size) != original.data:
        raise AssertionError('No-change frame import altered the atlas')
    coverage, _, _ = frame_coverage(original.data, target['tile_count'], comp)
    uses = {}
    for f in graphics_bank(gfx, 0)['frames']:
        if f['offset'] == target['offset']:
            uses[f['index']] = sorted({p['tile'] for p in composition_frame(parts, 0, f['index'])['parts']})
    overlap = {str(f): sorted(set(tiles) & set(uses[frame])) for f, tiles in uses.items() if f != frame}
    out = new_run(ROOT, 'ver_buki_riko', 'compression_audit')
    save_image(indices, size, palette, out/'frame147_indexed.png')
    from PIL import Image
    Image.frombytes('L', size, bytes(255 if c else 0 for c in coverage)).save(out/'frame147_coverage.png')
    report = {'source_sha256': profile['source_sha256'], 'archive_sha256': sha256(arc),
              'distinct_streams': len(unique), 'streams': list(unique.values()),
              'all_decoded_pixels_identical': True,
              'all_fit_original_streams': all(r['fits_original_stream'] for r in unique.values()),
              'target': {'frame': frame, 'graphics_bank': 0, 'composition_bank': 0, 'size': size,
                         'bounds': bounds, 'origin': [-bounds[0], -bounds[1]],
                         'covered_pixels': sum(bool(c) for c in coverage),
                         'overlapping_positions': sum(len(c)>1 for c in coverage),
                         'shared_block_tiles': uses, 'other_frame_tile_overlap': overlap,
                         'compression': unique[(target['offset'], target['tile_count'])]},
              'game_data_modified': False, 'recompressed_game_runtime_verified': False}
    write_json(out/'report.json', report)
    print(json.dumps({'output': str(out), 'streams': len(unique), 'all_fit': report['all_fit_original_streams'],
                      'target': report['target']}))


def build(extracted, png):
    profile, project, arc, gfx_meta, gfx, parts, palette = read_inputs(extracted)
    png = png.resolve()
    if not any(png.is_relative_to((ROOT/p).resolve()) for p in ('work/ver_buki_riko','out/ver_buki_riko')):
        raise ValueError('PNG must be a first-project working/output file')
    png_hash = sha256(png.read_bytes())
    indices, size = read_indexed_png(png, palette)
    target = graphics_bank(gfx, 0)['frames'][147]
    original = decode_stream(gfx, target['offset'], target['limit'], target['tile_count']*128)
    comp = composition_frame(parts, 0, 147)
    packed = edit_frame_indices(original.data, target['tile_count'], comp, indices, size)
    updated, budget = replace_stream(gfx, target, packed)
    affected, decoded_changes = [], []
    for bank in range(len(bank_offsets(gfx))):
        for f in graphics_bank(gfx, bank)['frames']:
            old = decode_stream(gfx, f['offset'], f['limit'], f['tile_count']*128)
            new = decode_stream(updated, f['offset'], f['limit'], f['tile_count']*128)
            if old.data != new.data:
                decoded_changes.append([bank, f['index']])
                if bank != 0 or f['offset'] != target['offset']:
                    raise ValueError('Unrelated compressed frame changed')
                c = composition_frame(parts, 0, f['index'])
                before, bs, _, _ = compose_indices(old.data, f['tile_count'], c)
                after, ns, _, _ = compose_indices(new.data, f['tile_count'], c)
                n = sum(a!=b for a,b in zip(before, after))
                if bs != ns:
                    raise ValueError('Composition dimensions changed')
                if n:
                    if f['index'] != 147:
                        raise ValueError('PNG edits affect another display frame')
                    affected.append({'bank': bank, 'frame': f['index'], 'changed_pixels': n})
    patched = bytearray(arc)
    patched[gfx_meta['offset']:gfx_meta['offset']+gfx_meta['size']] = updated
    parent = ROOT/'out/ver_buki_riko'
    if not parent.resolve().is_relative_to(ROOT):
        raise ValueError('Output escaped workspace')
    out = parent/('repack_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'))
    out.mkdir(parents=True, exist_ok=False)
    result = write_archive_copy(ROOT/project['source_bin'], out/'repacked.bin', profile['zero_archive'],
                                patched, profile['source_sha256'])
    cue = (ROOT/project['source_cue']).read_bytes().decode('utf-8-sig')
    (out/'repacked.cue').write_text(working_cue(cue,'repacked.bin'),encoding='ascii',newline='')
    (out/'modified.arc').write_bytes(patched)
    save_image(indices,size,palette,out/'imported_frame147.png')
    manifest = {'project':'ver_buki_riko','task':'zero_riko','kind':'indexed_png_recompression_test',
                'source_sha256':profile['source_sha256'],'source_archive_sha256':sha256(arc),
                'modified_bin':result,'modified_archive_sha256':sha256(patched),
                'input_png':str(png),'input_png_sha256':png_hash,'frame':147,'compression':budget,
                'decoded_shared_frames':decoded_changes,'visible_affected_frames':affected,
                'palette_changed':False,'composition_changed':False,'relocated':False,
                'runtime_modified_verified':False,'source_preserved':True}
    write_json(out/'manifest.json',manifest)
    validate_bin(ROOT/project['source_bin'],profile['source_sha256'])
    print(json.dumps({'output':str(out),'sha256':result['sha256'],'compression':budget,'affected':affected}))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command',required=True)
    for name in ('audit','build'):
        p = sub.add_parser(name)
        p.add_argument('--extract',type=Path,required=True)
        if name == 'build':p.add_argument('--png',type=Path,required=True)
    args = parser.parse_args()
    if args.command == 'audit':audit(args.extract)
    else:build(args.extract,args.png)


if __name__ == '__main__':main()
