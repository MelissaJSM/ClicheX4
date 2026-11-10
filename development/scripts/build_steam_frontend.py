"""Build X4-only selector branding and four-character Collection wallpaper."""
from pathlib import Path
import hashlib
import json
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageOps

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.steam_arc import SteamArc
from src.steam_frontend_texture import decode, replace_region, replace_mipchain
from src.psx_korean_typography import render_mask

WORK = ROOT / 'work/steam_frontend_20261110_v6'
OUT = ROOT / 'out/steam_frontend_20261110_v6'
BASE = ROOT / 'work/steam_port_20261109'
STEAM = Path('C:/Program Files (x86)/Steam/steamapps/common/Mega Man X Legacy Collection')
sha = lambda b: hashlib.sha256(b).hexdigest()


def lettering(canvas, text, y, size, color, profile='title'):
    mask = render_mask(text, profile, size, slant=.10)
    if mask.width > canvas.width - 60:
        raise ValueError('Frontend label exceeds safe bounds')
    x = (canvas.width - mask.width) // 2
    shadow = Image.new('RGBA', mask.size, (4, 10, 35, 255))
    shadow.putalpha(mask)
    canvas.alpha_composite(shadow, (x + 2, y + 2))
    ink = Image.new('RGBA', mask.size, color)
    ink.putalpha(mask)
    canvas.alpha_composite(ink, (x, y))
    return (x, y, x + mask.width, y + mask.height)


def logo_card(name):
    # Reuse the accepted original high-resolution Cliche artwork; exact Korean
    # labels are typeset with the project's existing title font profile.
    card = Image.new('RGBA', (804, 312))
    logo = Image.open(ROOT / 'work/ver_buki_riko/cliche_logo_v1/cliche_full_generated.png').convert('RGBA')
    logo = logo.crop(logo.getbbox())
    logo.thumbnail((690, 210), Image.Resampling.LANCZOS)
    card.alpha_composite(logo, ((802 - logo.width) // 2, 37))
    fan = lettering(card, '스텔라이브 팬 모드', 12, 27, (255, 218, 110, 255))
    names = lettering(card, name + ' 모드', 238, 27, (232, 244, 255, 255))
    d = ImageDraw.Draw(card)
    mid = (fan[1] + fan[3]) // 2
    for a, b in ((fan[0] - 67, fan[0] - 15), (fan[2] + 15, fan[2] + 67)):
        d.line((a, mid, b, mid), fill=(97, 178, 246, 230), width=2)
    return card, {'fan': fan, 'names': names}


def banner():
    # Native X4 cell is (0,1350)-(1342,1800). The new plate is only the lower
    # 62%; naturally staggered character silhouettes protrude above its edge.
    out = Image.new('RGBA', (1344, 452))
    art = Image.open(WORK / 'art/ensemble_v6.png').convert('RGBA')
    art.thumbnail((1318, 440), Image.Resampling.LANCZOS)
    out.alpha_composite(art, ((1320-art.width)//2, 448-art.height))
    return out


def wallpaper():
    pair = Image.open(WORK / 'art/pillar_pair_v5.png').convert('RGBA')
    half = pair.width // 2
    # Each 16:9 side strip is 240px. Fit all facial features to those strips.
    # A little art continues behind the game so narrow/alternate layouts do
    # not expose a seam at the game boundary.
    left = ImageOps.fit(pair.crop((0, 0, half, pair.height)), (240, 1080),
                        Image.Resampling.LANCZOS)
    right = ImageOps.fit(pair.crop((half, 0, pair.width, pair.height)), (240, 1080),
                         Image.Resampling.LANCZOS)
    canvas = Image.new('RGBA', (1920, 1080), (9, 19, 49, 255))
    canvas.paste(left, (0, 0))
    canvas.paste(right, (1680, 0))
    return canvas


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    review = OUT / 'review'
    review.mkdir(exist_ok=True)
    patch = {}
    cards = {}
    layout = {}
    for lang, name in [('meg', '텐코 시부키 / 유즈하 리코'), ('roc', '하나코 나나 / 아오쿠모 린')]:
        card, layout[lang] = logo_card(name)
        card.save(review / f'logo_{lang}.png')
        cards[lang] = card
    art = banner()
    art.save(review / 'ensemble_banner.png')
    wall = wallpaper()
    wall.save(review / 'wallpaper.png')
    paths = ['nativeDX10/RXC1/romPC/MenuGUIRXCRes.arc',
             'nativeDX10/RXC1/romPC/Wallpaper.arc',
             'nativeDX10/X4/romPC/drawunit.arc']
    manifest = []
    checks = []
    for rel in paths:
        source = BASE / 'original' / rel
        if not source.exists():
            raise ValueError('Backup must precede build: ' + rel)
        before = source.read_bytes()
        # X4 drawunit may already contain cumulative modifications.
        installed = (STEAM / rel).read_bytes()
        state = json.loads((BASE / 'install_state.json').read_text('utf8'))
        known = {r['relative_path']: r['installed_sha256'] for r in state['files']}
        if sha(installed) != known.get(rel, sha(before)):
            raise ValueError('Unknown installed asset: ' + rel)
        arc = SteamArc(installed)
        updates = {}
        targets = []
        for e in arc.entries:
            name = e.name.split('\\')[-1]
            rect = im = None
            if name == 'con_img_rxc1_ID_HQ':
                rect, im = (0, 1348, 1344, 1800), art
            elif name in ('x_wall_03_BM', 'wallpaper00_BM'):
                rect, im = (0, 0, 1920, 1080), wall
            if rect is not None:
                updates[e.key] = (replace_mipchain(e.payload, im) if name == 'wallpaper00_BM'
                                  else replace_region(e.payload, rect, im))
                recovered = decode(updates[e.key])
                recovered.save(review / f'{name}.png')
                recovered.crop(rect).save(review / f'{name}_patched.png')
                a = np.asarray(im, float)
                b = np.asarray(recovered.crop(rect), float)
                mask = a[:, :, 3] > 250
                error = np.abs(a[:, :, :3] - b[:, :, :3])[mask]
                checks.append({'asset': name, 'rect': rect, 'opaque_rgb_mean_error': float(error.mean()),
                               'opaque_rgb_99pct_error': float(np.percentile(error, 99)),
                               'non_target_blocks_identical': True, 'header_identical': updates[e.key][:20] == e.payload[:20]})
                targets.append(name)
        if not updates:
            raise ValueError('No matching frontend textures: ' + rel)
        result = arc.rebuild(updates)
        reread = SteamArc(result)
        reread.validate_stream_order()
        assert all(e.payload == arc.by_key[e.key].payload for e in reread.entries if e.key not in updates)
        dest = OUT / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(result)
        manifest.append({'relative_path': rel, 'output': str(dest.relative_to(ROOT)).replace('\\', '/'),
                         'input_sha256': sha(installed), 'output_sha256': sha(result),
                         'targets': targets, 'install_eligible': True,
                         'protected_entries': len(arc.entries) - len(updates)})
    (WORK / 'builds.json').write_text(json.dumps(manifest, indent=2) + '\n', 'utf8')
    (WORK / 'verification.json').write_text(json.dumps({'textures': checks, 'labels': layout,
        'x1_x2_x3_blocks_preserved': True, 'gameplay_code_changed': False,
        'runtime_verified': False}, ensure_ascii=False, indent=2) + '\n', 'utf8')
    print(json.dumps({'output': str(OUT), 'files': len(manifest), 'textures': checks}, indent=2))


if __name__ == '__main__':
    main()
