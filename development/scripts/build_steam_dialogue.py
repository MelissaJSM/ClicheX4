"""Port accepted Korean dialogue to native DAT4 and a persistent glyph atlas."""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import sys

import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.c01_audio_build import read_disc
from scripts.prepare_riko_ui import entry
from scripts.steam_runtime import EXE
from src.steam_arc import SteamArc
from src.steam_dialogue import (decode_dat4, encode_dat4, korean_source,
                                remap_messages, runtime_patches, SPACE, FONT_FIRST)
from src.steam_player import tex_geometry

WORK = ROOT/'work/steam_port_20261109'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def parent_arc(target, version, known, originals):
    rel = 'nativeDX10/X4/romPC/'+target
    path = WORK/f'dialogue_{version}_parents'/target
    expected = known.get(rel, originals[rel])
    if path.exists():
        raw = path.read_bytes()
    else:
        raw = (EXE.parent/rel).read_bytes()
        if sha(raw) != expected:
            raise ValueError('Unknown installed parent: '+target)
        path.parent.mkdir(exist_ok=True)
        path.write_bytes(raw)
    # Parent hashes are locked on first creation and checked on every rebuild.
    proof = path.with_suffix('.json')
    if proof.exists():
        if sha(raw) != json.loads(proof.read_text('utf8'))['sha256']:
            raise ValueError('Parent snapshot changed')
    else:
        proof.write_text(json.dumps({'sha256': sha(raw), 'source': rel}, indent=2)+'\n')
    return SteamArc(raw), str(path.relative_to(ROOT))


def pages(words):
    out = []
    current = []
    for word in words:
        current.append(word)
        if word & 0xa000:
            out.append(current)
            current = []
    if current:
        raise ValueError('Unterminated dialogue page')
    return out


def render_page(words, tiles):
    im = Image.new('RGB', (320, 112), (8, 18, 34))
    draw = ImageDraw.Draw(im)
    draw.rectangle((32, 20, 288, 89), fill=(4, 33, 74), outline=(120, 211, 232))
    x, y = 40, 29
    count = 0
    for word in words:
        tile = word & 1023
        if tile != SPACE:
            pixels = np.frombuffer(tiles[tile-FONT_FIRST], np.uint8).reshape(16, 16)
            for yy, xx in zip(*np.nonzero(pixels)):
                if 0 <= x+xx < 320 and 0 <= y+yy < 112:
                    shade = int(pixels[yy, xx])*17
                    im.putpixel((x+int(xx), y+int(yy)), (shade, shade, shade))
            count += 1
        if word & 0x4000:
            y += 18
            x = 40
        else:
            x += 12
    if count > 60 or y > 83:
        raise ValueError('Dialogue page exceeds native buffer/window')
    return im


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--version', choices=['v1', 'v2', 'v3'], default='v1')
    args = parser.parse_args()
    installed = json.loads((WORK/'install_state.json').read_text('utf8'))
    known = {r['relative_path']: r['installed_sha256'] for r in installed['files']}
    originals = {r['relative_path']: r['sha256'] for r in json.loads((WORK/'backup_manifest.json').read_text('utf8'))['originals']}
    reports = []
    for mode, suffix in [('ver_rin_nana', ''), ('ver_buki_riko', '_eng')]:
        pointer = json.loads((ROOT/'projects'/mode/'current_build.json').read_text('utf8'))
        source = (ROOT/pointer['cue']).with_suffix('.bin')
        with source.open('rb') as handle:
            if hashlib.file_digest(handle, 'sha256').hexdigest() != pointer['sha256']:
                raise ValueError('Accepted PS1 source changed')
        assets, _ = read_disc(source, ['PL00_U.ARC', 'PL01_U.ARC', 'PL02_U.ARC', 'LOAD_U.ARC'])
        source_font = entry(assets['LOAD_U.ARC'], 0x10001)
        all_sources = {}
        tile_map = {}
        tiles = []
        for player, count in [('pl00', 55), ('pl01', 49), ('pl02', 55)]:
            text = entry(assets[player.upper()+'_U.ARC'], 21)
            messages, glyphs = korean_source(text, count, source_font)
            all_sources[player] = (messages, glyphs)
            for bitmap in glyphs.values():
                if bitmap not in tile_map:
                    tile_map[bitmap] = FONT_FIRST+len(tiles)
                    tiles.append(bitmap)
        if FONT_FIRST+len(tiles) > SPACE:
            raise ValueError('Dialogue exceeds four native tile pages')
        outdir = ROOT/'out'/mode/f'steam_dialogue_20261109_{args.version}'
        review = outdir/'review'
        review.mkdir(parents=True, exist_ok=True)
        mode_reports = []
        for target in ['load'+suffix+'.arc', *[p+suffix+'.arc' for p in all_sources]]:
            arc, parent = parent_arc(target, args.version, known, originals)
            updates = {}
            proof = {}
            if target.startswith('load'):
                textures = [e for e in arc.entries if '\\moji\\' in e.name and e.payload[:4] == b'TEX\0']
                if len(textures) != 2:
                    raise ValueError('Expected both font device variants')
                for texture in textures:
                    if tex_geometry(texture.payload) != (256, 512, 20):
                        raise ValueError('Accepted Korean menu font parent required')
                    data = bytearray(texture.payload)+bytearray(256*512)
                    struct.pack_into('<I', data, 8, 1 | (256 << 6) | (1024 << 19))
                    for index, bitmap in enumerate(tiles, FONT_FIRST):
                        x, y = index%16*16, index//16*16
                        for row in range(16):
                            pos = 20+(y+row)*256+x
                            data[pos:pos+16] = bitmap[row*16:row*16+16]
                    if data[20:len(texture.payload)] != texture.payload[20:]:
                        raise ValueError('Original/menu font pixels changed')
                    for index, bitmap in enumerate(tiles, FONT_FIRST):
                        x, y = index%16*16, index//16*16
                        actual = b''.join(data[20+(y+r)*256+x:20+(y+r)*256+x+16] for r in range(16))
                        if actual != bitmap:
                            raise ValueError('Dialogue glyph pixel roundtrip failed')
                    updates[texture.key] = bytes(data)
                proof = {'glyphs': len(tiles), 'first_tile': FONT_FIRST, 'last_tile': FONT_FIRST+len(tiles)-1,
                         'native_and_menu_pages_preserved': True, 'glyph_pixels_exact': True}
            else:
                player = target[:4]
                native_text = next(e for e in arc.entries if e.payload[:4] == b'DAT4')
                native_messages = decode_dat4(native_text.payload)
                words, glyphs = all_sources[player]
                if len(native_messages) != len(words):
                    raise ValueError('Native message ID directory differs')
                converted = remap_messages(words, glyphs, tile_map)
                updates[native_text.key] = encode_dat4(converted)
                body_timed = 0
                visible_max = 0
                page_count = 0
                for message in converted:
                    for page in pages(message):
                        visible_max = max(visible_max, sum((w & 1023) != SPACE for w in page))
                        body_timed += sum(bool(w & 0x1000) for w in page)
                        render_page(page, tiles)  # Bounds validation for every page.
                        page_count += 1
                proof = {'messages': len(converted), 'pages': page_count, 'maximum_visible_glyphs': visible_max,
                         'timed_words': body_timed, 'all_ps1_control_bits_preserved': True,
                         'native_message_ids_preserved': True,
                         'jp_pagination_uses_accepted_korean_translation': not bool(suffix)}
                if player != 'pl02':
                    intro = pages(converted[30 if player == 'pl00' else 25])
                    sheet = Image.new('RGB', (640, 112), (8, 18, 34))
                    sheet.paste(render_page(intro[0], tiles), (0, 0))
                    sheet.paste(render_page(intro[-1], tiles), (320, 0))
                    sheet.resize((1280, 224), Image.Resampling.NEAREST).save(review/(player+'_intro.png'))
            data = arc.rebuild(updates)
            back = SteamArc(data)
            back.validate_stream_order()
            for e in arc.entries:
                if back.by_key[e.key].payload != updates.get(e.key, e.payload):
                    raise ValueError('Unexpected dialogue output changes')
            output = outdir/'nativeDX10/X4/romPC'/target
            output.parent.mkdir(parents=True, exist_ok=True)
            if output.exists() and output.read_bytes() != data:
                raise ValueError('Existing dialogue version differs')
            output.write_bytes(data)
            report = {'mode': mode, 'target_arc': target, 'parent': parent, 'parent_sha256': sha(arc.raw),
                      'source_bin': str(source.relative_to(ROOT)), 'source_bin_sha256': pointer['sha256'],
                      'original_sha256': originals['nativeDX10/X4/romPC/'+target],
                      'output': str(output.relative_to(ROOT)), 'output_sha256': sha(data),
                      'changed_entries': [e.name for e in arc.entries if e.key in updates],
                      'proof': proof, 'install_eligible': True, 'runtime_verified': False}
            mode_reports.append(report)
            reports.append(report)
        (outdir/'manifest.json').write_text(json.dumps(mode_reports, indent=2)+'\n')
        print(json.dumps({'mode': mode, 'glyphs': len(tiles), 'last_tile': FONT_FIRST+len(tiles)-1,
                          'dialogue': [r['proof'] for r in mode_reports[1:]]}))
    (WORK/'dialogue_builds.json').write_text(json.dumps(reports, indent=2)+'\n')
    required = {'nativeDX10/X4/romPC/'+r['target_arc']: r['output_sha256'] for r in reports}
    patches = [{'name': name, 'address': va, 'before_hex': before.hex(), 'after_hex': after.hex()}
               for name, va, before, after in runtime_patches()]
    (WORK/'dialogue_runtime_patch.json').write_text(json.dumps({'installed_requirements': required, 'patches': patches}, indent=2)+'\n')
    display = json.loads((WORK/'menu_runtime_patch.json').read_text('utf8'))
    display['installed_requirements'] = {rel: h for rel, h in required.items() if Path(rel).name.startswith('load')}
    (WORK/'dialogue_display_patch.json').write_text(json.dumps(display, indent=2)+'\n')


if __name__ == '__main__':
    main()
