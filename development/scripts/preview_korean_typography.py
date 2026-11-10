"""Native-size typography comparisons from assets; not runtime screenshots."""
import argparse
import hashlib
import json
import struct
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.inventory_korean import D
from scripts.prepare_cliche_logo_v3 import loading_palettes
from scripts.prepare_riko_ui import entry
from src.psx_static_effect import compose_static
from src.psx_ui_atlas import aliased_composition, local_composition

STAGES = ['스카이 라군', '정글', '스노 베이스', '바이오 랩', '볼케이노',
          '마린 베이스', '사이버 공간', '에어 포스', '군용 열차', '메모리얼 홀',
          '우주항', '최종 병기']
HEADERS = ['영문 기준 자산', '이전 한글', '수정 한글']
LABEL_FONT = ImageFont.truetype('C:/Windows/Fonts/malgun.ttf', 15)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def source(name):
    first = D / 'inventory' / name
    return first if first.exists() else D / 'ui_inventory' / name


def rgba(indices, palette):
    colors = np.array([((v & 31) * 255 // 31,
                        ((v >> 5) & 31) * 255 // 31,
                        ((v >> 10) & 31) * 255 // 31,
                        255 if i else 0) for i, v in enumerate(palette)], np.uint8)
    return Image.fromarray(colors[indices])


def atlas(texture):
    raw = np.frombuffer(texture, np.uint8)
    unpacked = np.empty(len(raw) * 2, np.uint8)
    unpacked[::2], unpacked[1::2] = raw & 15, raw >> 4
    return unpacked.reshape(-1, 256)


def frame(texture, parts, bank, index, palette):
    composition = local_composition(aliased_composition(parts, bank, index))
    pixels, size, bounds, _ = compose_static(texture, composition)
    return rgba(np.frombuffer(pixels, np.uint8).reshape(size[1], size[0]), palette), bounds


def plate(items, columns, cell, path):
    """Annotations are outside each native, nearest-neighbour image."""
    width, height = cell
    result = Image.new('RGB', (columns * width, ((len(items) + columns - 1) // columns) * height), '#202533')
    draw = ImageDraw.Draw(result)
    for index, (label, image, scale) in enumerate(items):
        x, y = index % columns * width, index // columns * height
        draw.text((x + 7, y + 4), label, font=LABEL_FONT, fill='white')
        enlarged = image.resize((image.width * scale, image.height * scale), Image.Resampling.NEAREST)
        if enlarged.width > width - 12 or enlarged.height > height - 30:
            raise ValueError(f'Preview cell clips native image: {label}')
        result.paste(enlarged.convert('RGB'), (x + 6, y + 27))
    result.save(path)


def loading_screen(resource, exe, character, stage, area=1):
    """Mirror US func_80013404 direct UV draws, using exact executable data."""
    tex = atlas(entry(resource, 0x10008))
    pal = loading_palettes(exe)
    records = [struct.unpack_from('<hhBBBB', exe, 0xDED04 + i * 8) for i in range(9)]
    if records[1][:2] != (200, 192) or records[2][:2] != (248, 192):
        raise ValueError('Expected accepted loading-logo placement')
    screen = Image.new('RGBA', (320, 240), (0, 0, 0, 255))
    # The native ordering table puts the left logo on top of the right one.
    indices = [0, 2, 1, 3 if character == 'shibuki' else 4, 5, 6]
    if stage < 9:
        indices.append(7 if area == 1 else 8)
    details = []
    for i in indices:
        x, y, uv, w, h, row = records[i]
        if i == 6:
            uv = exe[0xDED04 + 72 + stage]
        u, v = uv % 16 * 16, uv // 16 * 16
        pixels = tex[v:v + h * 16, u:u + w * 16]
        if pixels.shape != (h * 16, w * 16):
            raise ValueError('Loading UV rectangle leaves atlas')
        words = struct.unpack_from('<16H', pal, row * 32)
        screen.alpha_composite(rgba(pixels, words), (x, y))
        yy, xx = np.where(pixels != 0)
        bounds = None if not len(xx) else [x + int(xx.min()), y + int(yy.min()), x + int(xx.max()) + 1, y + int(yy.max()) + 1]
        details.append({'record': i, 'origin': [x, y], 'uv': [u, v], 'size': [w * 16, h * 16],
                        'palette_row': row, 'screen_ink': bounds})
    return screen.convert('RGB'), details


def title_screen(resource, exe, palette_resource, selected):
    texture = entry(resource, 0x10002)
    parts = struct.pack('<I', 4) + entry(resource, 0x12)
    palette = entry(palette_resource, 5)
    screen = Image.new('RGBA', (320, 240), (0, 0, 0, 255))
    base = struct.unpack_from('<I', exe, 0x18)[0]
    offset = 0x8010E71C - base + 2048
    # Accepted logo and mode caption remain visible to judge visual balance.
    for index in (0, 2, 13, 14):
        x, y, number, row = struct.unpack_from('<hhBB', exe, offset + index * 6)
        if index in (2, 13, 14):
            expected = {2: (160, 128, 2), 13: (160, 144, 29), 14: (160, 160, 30)}[index]
            if (x, y, number) != expected or row != 7:
                raise ValueError('Native title row init changed')
            row = 6 if index == (2, 13, 14)[selected] else 7
        words = struct.unpack_from('<16H', palette, row * 32)
        image, bounds = frame(texture, parts, 0, number, words)
        screen.alpha_composite(image, (x + bounds[0], y + bounds[1]))
    return screen.convert('RGB')


def menu_examples(resource, parts, palette):
    """Show real parts and native menu CLUT roles, without invented screen layout."""
    texture = entry(resource, 0x10001)
    examples = [(8, 2, '불러오기 제목'), (19, 0, '안내문'), (20, 3, '선택 항목'),
                (21, 0, '비선택 항목'), (5, 0, '버튼 안내'), (94, 2, '설정 제목')]
    items = []
    for number, row, label in examples:
        words = struct.unpack_from('<16H', palette, row * 32)
        image, bounds = frame(texture, parts, 0, number, words)
        black = Image.new('RGBA', image.size, (0, 0, 0, 255))
        black.alpha_composite(image)
        items.append((label, black.convert('RGB'), {'frame': number, 'palette_row': row, 'bounds': list(bounds)}))
    return items


def main(args):
    args.output.mkdir(parents=True, exist_ok=False)
    exe = source('SLUS_005.61').read_bytes()
    title_pal = source('COL0E_U0.ARC').read_bytes()
    palette_evidence = json.loads((args.menu_palette_capture / 'evidence.json').read_text('utf-8'))
    if palette_evidence['label'] != 'initial_run' or len(palette_evidence['vram_bases']) != 1:
        raise ValueError('Expected inspected native settings-menu palette capture')
    vram_path = args.menu_palette_capture / f"vram_{palette_evidence['vram_bases'][0]}.bin"
    vram = vram_path.read_bytes()
    if len(vram) != 0x100000:
        raise ValueError('Invalid captured native VRAM size')
    # Original menu code uses rows 0/2/3 at y480; the menu loader replaces
    # loading/logo palette rows there. Taking the EXE loading palette is wrong.
    palette = vram[480 * 1024 * 2:480 * 1024 * 2 + 512]
    versions = [(None, None), (args.previous_ui, args.previous_menu), (args.ui, args.menu)]
    input_hashes = {str(source('SLUS_005.61').relative_to(ROOT)): digest(exe),
                    str(source('COL0E_U0.ARC').relative_to(ROOT)): digest(title_pal)}
    checks, loading_items, title_items, menu_items = [], [], [], []
    stage_items = []
    for version, (ui, menu) in enumerate(versions):
        def read(name, component):
            path = source(name) if component is None else component / name
            value = path.read_bytes()
            input_hashes[str(path.relative_to(ROOT) if path.is_absolute() else path)] = digest(value)
            return value
        loading = read('LOAD_U.ARC', ui)
        title = read('ST0E_U0.ARC', ui)
        menu_load = read('LOAD_U.ARC', menu)
        menu_parts = read('MOJIPAT.ARC', menu)
        # Later full-name layouts have different direct-draw rectangles.
        # Each comparison column must use its own executable when supplied;
        # older UI-only proposals retain the accepted parent's EXE.
        version_exe = read('SLUS_005.61', ui) if ui is not None and (ui / 'SLUS_005.61').exists() else exe
        for character in ('riko', 'shibuki'):
            screen, details = loading_screen(loading, version_exe, character, 0)
            screen.save(args.output / f'loading_{version}_{character}_native.png')
            loading_items.append((f'{HEADERS[version]} / {"리코" if character == "riko" else "시부키"} · 정적 합성', screen, 2))
            checks.append({'version': HEADERS[version], 'character': character, 'loading': details})
        for selected in range(3):
            screen = title_screen(title, version_exe, title_pal, selected)
            screen.save(args.output / f'title_{version}_{selected}_native.png')
            title_items.append((f'{HEADERS[version]} / 선택 {selected + 1} · 정적 합성', screen, 2))
        examples = menu_examples(menu_load, menu_parts, palette)
        for label, picture, metadata in examples:
            menu_items.append((f'{HEADERS[version]} / {label} · 정적 자산', picture, 2))
        if version == 2:
            for stage, name in enumerate(STAGES):
                for character in ('riko', 'shibuki'):
                    screen, details = loading_screen(loading, version_exe, character, stage, area=1 + stage % 2)
                    screen.save(args.output / f'loading_stage_{stage:02d}_{character}_native.png')
                    stage_items.append((f'{name} / {"리코" if character == "riko" else "시부키"} · 정적 합성', screen.crop((0, 184, 320, 232)), 2))
                    checks.append({'version': HEADERS[version], 'stage': stage, 'character': character, 'loading': details})
    # Rows compare the same scene across original / previous / revised assets.
    plate([loading_items[v * 2 + c] for c in range(2) for v in range(3)], 3, (652, 510), args.output / 'loading_comparison.png')
    plate([title_items[v * 3 + s] for s in range(3) for v in range(3)], 3, (652, 510), args.output / 'title_comparison.png')
    plate([menu_items[v * 6 + e] for e in range(6) for v in range(3)], 3, (652, 100), args.output / 'menu_comparison.png')
    plate(stage_items, 2, (652, 130), args.output / 'loading_all_stages.png')
    report = {'kind': 'native_asset_typography_static_preview', 'runtime_verified': False,
              'scope': '실제 자산·EXE의 좌표와 팔레트로 만든 정적 합성. 실행 캡처 아님. 제목 배경은 검정, 원래 대기 점멸 위상은 포함하지 않음.',
              'loading_canvas': [320, 240], 'loading_stage_count': 12, 'characters': ['리코', '시부키'],
              'native_sources': ['3A6C.c: func_80013404 / func_8001326C', '55C4.c: func_800160F4',
                                 'misc_19_title.c: title_object_inits / title_draw',
                                 'misc_42_menu_icon.c: CLUT 0x7800 / 0x7802 / 0x7803'],
              'palette_source': {'loading': 'SLUS_005.61:D_800F1660', 'title': 'COL0E_U0.ARC:entry5 rows6/7',
                                 'menu': str(vram_path), 'menu_palette_vram_origin': [0, 480],
                                 'menu_palette_capture_label': palette_evidence['label'],
                                 'menu_palette_capture_bin_sha256': palette_evidence['bin_sha256'],
                                 'menu_vram_sha256': digest(vram),
                                 'menu_palette_sha256': digest(palette)},
              'inputs': input_hashes, 'layout': checks, 'game_files_written': False, 'emulator_accessed': False}
    (args.output / 'preview.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({'output': str(args.output), 'native_pngs': 39, 'comparison_sheets': 4, 'runtime_verified': False}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--ui', type=Path, required=True)
    parser.add_argument('--menu', type=Path, required=True)
    parser.add_argument('--previous-ui', type=Path, default=D / 'ui_proposal_v4')
    parser.add_argument('--previous-menu', type=Path, default=D / 'menu_proposal_v2')
    parser.add_argument('--menu-palette-capture', type=Path,
                        default=ROOT / 'work/ver_buki_riko/korean_runtime/20261028T043413464160Z')
    parser.add_argument('--output', type=Path, required=True)
    main(parser.parse_args())
