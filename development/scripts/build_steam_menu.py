"""Add Korean menu glyphs without replacing the native dialogue/font page."""
import argparse
import hashlib
import json
from pathlib import Path
import runpy
import struct
import sys

import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.prepare_korean_menu import render_menu_tile, CENTERED_HEADINGS
from src.steam_arc import SteamArc
from src.steam_menu import native_menu_frames, encode_frames
from src.steam_player import tex_geometry
from src.steam_ui import pat_frames
from src.steam_executable import ORIGINAL_SHA256

WORK = ROOT/'work/steam_port_20261109'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def translations(english):
    data = runpy.run_path(str(ROOT/'work/ver_buki_riko/korean_v1/menu_ko.py'))
    text = {n: s for n, s in data['TEXT'].items() if n < 115}
    text.update({4: '저장 데이터 불러오기', 19: '불러올 데이터를 선택해 주세요.',
                 52: '저장할 데이터를 선택해 주세요.',
                 95: '기본 사격 / 특수 무기', 100: '기본 사격'})
    for n in range(26, 32):
        text[n] = f'데이터 {n-25}'
    # These legacy two-column rows are retained in the native resource.
    for n in range(35, 41):
        text[n] = ('본체 메모리' if n < 38 else '카트리지 메모리') + f'  데이터 {(n-35)%3+1}'
    if english:
        text.update({115: '저장 데이터 불러오기', 116: ' ',
                     117: '완료하지 못했습니다.', 118: '게임을 저장할 수 없습니다.',
                     119: '초기화할까요?', 120: '게임을 종료할까요?',
                     121: '저장 장치에서\n데이터 불러오기',
                     122: '초기화하지 않은 메모리 카드입니다.',
                     123: '데이터 4', 124: '데이터 5', 125: '데이터 6',
                     74: '불러오지 못했습니다.', 75: '저장하지 못했습니다.',
                     76: '초기화를', 77: '게임 데이터를'})
    else:
        text.update({6: '저장 장치에서 불러오기', 45: '게임을 계속할까요?',
                     48: '이어하기', 51: '저장하지 않음', 53: '저장하지 않음',
                     74: '데이터 불러오기에', 75: '데이터 저장에',
                     76: '초기화에', 77: '실패했습니다.',
                     78: '이 메모리 카드는', 79: '초기화되지 않았습니다.',
                     80: '메모리 카드를 초기화할까요?',
                     115: '데이터 4', 116: '데이터 5', 117: '데이터 6'})
    return text


def parts(text, mapping, x, y):
    result = bytearray()
    for c in text:
        if c == ' ':
            x += 6
            continue
        if not -128 <= x <= 127 or not -128 <= y <= 127:
            raise ValueError(f'Menu coordinates overflow: {text!r}, {x}, {y}')
        tile = mapping[c]
        result.extend(struct.pack('<BBbb', tile//256, tile%256, x, y))
        x += 12
    return bytes(result)


def width(text):
    return sum(6 if c == ' ' else 12 for c in text)


def translate_frames(native, texts, mapping, english):
    result = list(native)
    layouts = {}
    for n, text in sorted(texts.items()):
        source = list(struct.iter_unpack('<BBbb', native[n]))
        ys = sorted({q[3] for q in source})
        lines = text.split('\n')
        if len(lines) != len(ys):
            raise ValueError(f'Menu line count changed: {n}')
        output = bytearray()
        positions = []
        for line, y in zip(lines, ys):
            row = [q for q in source if q[3] == y]
            left = min(q[2] for q in row)
            right = max(q[2]+16 for q in row)
            if not english and n in (1, 2):
                x = -width(line)//2
            elif not english and n in (3, 4):
                # Centre the complete choice group: 16px cursor, 16px gap,
                # then the longest Korean option. Both rows share a left edge.
                x = (320-(32+max(width(texts[3]), width(texts[4]))))//2+32-160
            elif n in CENTERED_HEADINGS:
                x = -width(line)//2
            elif n == 93:
                x = (left+right-width(line))//2
            elif 26 <= n <= 31:
                x = 128-width(line)
            elif 35 <= n <= 40:
                one, two = line.split('  ')
                output.extend(parts(one, mapping, -112, y))
                output.extend(parts(two, mapping, 128-width(two), y))
                positions.append({'line': line, 'columns': [-112, 128-width(two)], 'y': y})
                continue
            else:
                x = left
            if line.strip():
                output.extend(parts(line, mapping, x, y))
            else:
                # Preserve a valid transparent quad for the US second line
                # whose sentence is now complete in frame 52.
                output.extend(struct.pack('<BBbb', 1, 255, x, y))
            positions.append({'line': line, 'x': x, 'y': y, 'width': width(line)})
        result[n] = bytes(output)
        layouts[n] = positions
    # Keep native key/button quads and their palette flags; each device atlas
    # retains its original glyphs and bindings.
    for n in (5, 7, 113, 114):
        source = list(struct.iter_unpack('<BBbb', native[n]))
        if n == 5:
            icons = [i for i, q in enumerate(source) if q[0] & 4]
            if len(icons) != 2:
                raise ValueError('Unrecognized native confirm/cancel prompt')
            indices = icons
            labels = ['결정', '취소']
        elif n == 7:
            cancel_tile = 11 if english else 159
            indices = [0, next(i for i, q in enumerate(source) if i > 3 and q[1] == cancel_tile)]
            labels = ['결정', '취소']
        else:
            indices = [0]
            labels = ['결정']
        output = bytearray()
        for index, label in zip(indices, labels):
            count = 4 if n in (7, 113) and index == 0 else 2
            for q in source[index:index+count]:
                output.extend(struct.pack('<BBbb', *q))
            anchor = source[index+count]
            output.extend(parts(label, mapping, anchor[2], anchor[3]))
        result[n] = bytes(output)
        layouts[n] = {'button_records_preserved': True, 'labels': labels}
    if not english:
        # A dedicated Continue footer avoids moving other menu prompts.
        footer = b''.join(struct.pack('<BBbb', flag, tile, x+28, y)
                          for flag, tile, x, y in struct.iter_unpack('<BBbb', result[5]))
        if len(result) != 118:
            raise ValueError('Unexpected JP footer registration index')
        result.append(footer)
        layouts[118] = {'source_frame': 5, 'translation': '결정 / 취소', 'shift_x': 28,
                        'scope': 'JP Continue only'}
    return result, layouts


def render(texture, records, palette, origin=(160, 40), size=(320, 96)):
    _, h, start = tex_geometry(texture)
    pixels = np.frombuffer(texture[start:], np.uint8).reshape(h, 256)
    colors = np.array([[((v >> s) & 31)*255//31 for s in (0, 5, 10)]+[0 if i == 0 else 255]
                       for i, v in enumerate(struct.unpack('<16H', palette))], np.uint8)
    im = Image.new('RGBA', size, (16, 24, 40, 255))
    for flag, tile, x, y in struct.iter_unpack('<BBbb', records):
        tile += (flag & 3)*256
        tx, ty = tile % 16*16, tile//16*16
        block = pixels[ty:ty+16, tx:tx+16]
        if block.shape != (16, 16):
            raise ValueError('Menu tile outside TEX')
        if flag & 64:
            block = block[:, ::-1]
        if flag & 128:
            block = block[::-1]
        im.alpha_composite(Image.fromarray(colors[block]), (origin[0]+x, origin[1]+y))
    return im


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--version', choices=['v1', 'v2', 'v3'], default='v1')
    args = p.parse_args()
    base_reports = json.loads((WORK/'loading_builds.json').read_text('utf8'))
    reports = []
    for base in base_reports:
        mode, target = base['mode'], base['target_arc']
        english = mode == 'ver_buki_riko'
        arc = SteamArc((ROOT/base['output']).read_bytes(), base['output_sha256'])
        native_pat = next(e for e in arc.entries if '\\moji\\' in e.name and e.payload[:4] == b'PAT\0')
        native = native_menu_frames(native_pat.payload)
        textures = [e for e in arc.entries if '\\moji\\' in e.name and e.payload[:4] == b'TEX\0']
        if len(textures) != 2:
            raise ValueError('Expected keyboard and pad font textures')
        palette = next(e.payload for e in arc.entries if e.payload[:4] == b'COL\0')[12:44]
        words = np.array(struct.unpack('<16H', palette), np.uint16)
        indices = np.arange(2, 15, dtype=np.uint8)
        levels = words[indices] & 31
        if not np.array_equal(words[indices] & 31, (words[indices] >> 5) & 31):
            raise ValueError('Unexpected native font palette')
        texts = translations(english)
        chars = sorted({c for s in texts.values() for c in s if c not in ' \n'} | set('결정취소'))
        if len(chars) > 255:
            raise ValueError('Korean menu exceeds new atlas page')
        mapping = {c: 256+i for i, c in enumerate(chars)}
        glyphs = {c: render_menu_tile(c, indices, levels)[0] for c in chars}
        if '.' in glyphs:
            dot = glyphs['.']
            if np.any(dot[7:]):
                raise ValueError('Unexpected punctuation bounds')
            glyphs['.'] = np.pad(dot[:7], ((9, 0), (0, 0)))
        new_frames, layouts = translate_frames(native, texts, mapping, english)
        encoded = encode_frames(new_frames)
        updates = {native_pat.key: encoded}
        unchanged = sorted(set(range(len(native)))-set(layouts))
        for tex in textures:
            if tex_geometry(tex.payload) != (256, 256, 20):
                raise ValueError('Unexpected native font dimensions')
            result = bytearray(tex.payload)+bytearray(65536)
            struct.pack_into('<I', result, 8, 1 | (256 << 6) | (512 << 19))
            for c, tile in mapping.items():
                x, y = tile % 16*16, tile//16*16
                for row in range(16):
                    start = 20+(y+row)*256+x
                    result[start:start+16] = glyphs[c][row].tobytes()
            result = bytes(result)
            if result[20:65556] != tex.payload[20:]:
                raise ValueError('Native dialogue/key font page changed')
            for n in unchanged:
                if render(result, new_frames[n], palette).tobytes() != render(tex.payload, native[n], palette).tobytes():
                    raise ValueError('Native menu icon pixels changed')
            updates[tex.key] = result
        output = arc.rebuild(updates)
        check = SteamArc(output)
        check.validate_stream_order()
        if pat_frames(check.by_key[native_pat.key].payload) != [new_frames]:
            raise ValueError('Installed-format menu readback failed')
        for e in arc.entries:
            if check.by_key[e.key].payload != updates.get(e.key, e.payload):
                raise ValueError('Protected menu/loading resource changed')
        outdir = ROOT/'out'/mode/f'steam_menu_20261109_{args.version}'
        dest = outdir/'nativeDX10/X4/romPC'/target
        dest.parent.mkdir(parents=True, exist_ok=True)
        if dest.exists() and dest.read_bytes() != output:
            raise ValueError('Existing menu version differs')
        dest.write_bytes(output)
        review = outdir/'review'
        review.mkdir(exist_ok=True)
        keyboard = next(e for e in textures if 'keyboard' in e.name)
        for start in range(0, len(new_frames), 40):
            count = min(40, len(new_frames)-start)
            sheet = Image.new('RGB', (960, 96*((count+2)//3)), (0, 0, 0))
            for i, records in enumerate(new_frames[start:start+40]):
                image = render(updates[keyboard.key], records, palette)
                ImageDraw.Draw(image).text((3, 3), str(start+i), fill='white')
                sheet.paste(image, (i%3*320, i//3*96))
            sheet.save(review/f'menus_{start}.png')
        report = {'mode': mode, 'target_arc': target, 'output': str(dest.relative_to(ROOT)),
                  'output_sha256': sha(output), 'original_sha256': base['original_sha256'],
                  'parent': base['output'], 'parent_sha256': base['output_sha256'],
                  'glyphs': len(chars), 'frames': len(new_frames), 'native_frames': len(native),
                  'translated_frames': len(layouts),
                  'native_font_page_preserved': True, 'native_button_icons_preserved': True,
                  'loading_ready_and_save_graphics_preserved': True,
                  'unmodified_frame_ids': unchanged, 'layouts': layouts,
                  'changed_entries': [e.name for e in arc.entries if e.key in updates],
                  'runtime_verified': False, 'install_eligible': True}
        (outdir/'manifest.json').write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n', encoding='utf8')
        reports.append(report)
        print(json.dumps({k: report[k] for k in ['mode', 'glyphs', 'frames', 'translated_frames', 'output_sha256']}))
    (WORK/'menu_builds.json').write_text(json.dumps(reports, ensure_ascii=False, indent=2)+'\n', encoding='utf8')
    display = json.loads((WORK/'loading_runtime_patch.json').read_text('utf8'))
    display['installed_requirements'] = {'nativeDX10/X4/romPC/'+r['target_arc']: r['output_sha256'] for r in reports}
    original_exe = (WORK/'original/RXC1.exe').read_bytes()
    if sha(original_exe) != ORIGINAL_SHA256:
        raise ValueError('Original native UI table source differs')
    offset = 0xb7efa4
    before = original_exe[offset:offset+32]
    expected = bytes.fromhex('20038004a000100130024005d0ff01002004a0038000100130024005d0ff0000')
    if before != expected:
        raise ValueError('JP Continue coordinate/label table changed')
    after = bytearray(before)
    after[0] = after[16] = 84
    after[11] = after[27] = 118
    display['menu_layout_patches'] = [{'name': 'jp_continue_choice_and_footer',
        'address': 0xf7fba4, 'file_offset': offset,
        'before_hex': before.hex(), 'after_hex': after.hex(), 'kind': 'game_data'}]
    (WORK/'menu_runtime_patch.json').write_text(json.dumps(display, indent=2)+'\n', encoding='utf8')


if __name__ == '__main__':
    main()
